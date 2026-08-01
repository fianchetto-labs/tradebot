import pytest

from fianchetto_tradebot.common_models.managed_executions.managed_execution_status import (
    TERMINAL_MANAGED_EXECUTION_STATUSES,
    InvalidManagedExecutionStatusChange,
    ManagedExecutionStatus,
    is_terminal_managed_execution_status,
    managed_execution_status_from_order_status,
    managed_execution_status_after_change,
    managed_execution_status_after_order_check,
)
from fianchetto_tradebot.common_models.order.order_status import OrderStatus


EXPECTED_BROKERAGE_STATUS_TRANSLATIONS = {
    OrderStatus.OPEN: ManagedExecutionStatus.WORKING,
    OrderStatus.PARTIAL: ManagedExecutionStatus.WORKING,
    OrderStatus.INDIVIDUAL_FILLS: ManagedExecutionStatus.WORKING,
    OrderStatus.CANCEL_REQUESTED: ManagedExecutionStatus.WORKING,
    OrderStatus.PRE_SUBMISSION: ManagedExecutionStatus.WORKING,
    OrderStatus.EXECUTED: ManagedExecutionStatus.EXECUTED,
    OrderStatus.CANCELLED: ManagedExecutionStatus.WORKING,
    OrderStatus.EXPIRED: ManagedExecutionStatus.FAILED,
    OrderStatus.REJECTED: ManagedExecutionStatus.FAILED,
}


@pytest.mark.parametrize(
    ("order_status", "managed_execution_status"),
    EXPECTED_BROKERAGE_STATUS_TRANSLATIONS.items(),
)
def test_brokerage_order_status_maps_to_managed_execution_status(
    order_status: OrderStatus,
    managed_execution_status: ManagedExecutionStatus,
):
    assert managed_execution_status_from_order_status(order_status) == managed_execution_status


def test_every_brokerage_order_status_has_an_explicit_managed_execution_decision():
    assert set(EXPECTED_BROKERAGE_STATUS_TRANSLATIONS) | {OrderStatus.ANY} == set(OrderStatus)


def test_brokerage_cancellation_does_not_cancel_or_fail_the_managed_execution():
    assert managed_execution_status_from_order_status(OrderStatus.CANCELLED) == ManagedExecutionStatus.WORKING
    assert (
        managed_execution_status_after_order_check(
            current_status=ManagedExecutionStatus.WORKING,
            order_status=OrderStatus.CANCELLED,
        )
        == ManagedExecutionStatus.WORKING
    )


def test_cancel_request_is_not_cleared_by_later_active_order_check():
    assert (
        managed_execution_status_after_order_check(
            current_status=ManagedExecutionStatus.CANCEL_REQUESTED,
            order_status=OrderStatus.OPEN,
        )
        == ManagedExecutionStatus.CANCEL_REQUESTED
    )


def test_order_status_any_is_not_a_managed_execution_lifecycle_status():
    with pytest.raises(ValueError, match="query filter"):
        managed_execution_status_from_order_status(OrderStatus.ANY)


def test_terminal_managed_execution_statuses_are_explicit():
    assert TERMINAL_MANAGED_EXECUTION_STATUSES == {
        ManagedExecutionStatus.CANCELLED,
        ManagedExecutionStatus.EXECUTED,
        ManagedExecutionStatus.FAILED,
    }


@pytest.mark.parametrize("status", ManagedExecutionStatus)
def test_terminal_managed_execution_status_policy(status: ManagedExecutionStatus):
    assert is_terminal_managed_execution_status(status) == (
        status in TERMINAL_MANAGED_EXECUTION_STATUSES
    )


@pytest.mark.parametrize(
    ("current_status", "order_status", "expected_status"),
    [
        (ManagedExecutionStatus.PRE_SUBMISSION, OrderStatus.OPEN, ManagedExecutionStatus.WORKING),
        (ManagedExecutionStatus.PRE_SUBMISSION, OrderStatus.EXECUTED, ManagedExecutionStatus.EXECUTED),
        (ManagedExecutionStatus.PRE_SUBMISSION, OrderStatus.REJECTED, ManagedExecutionStatus.FAILED),
        (ManagedExecutionStatus.WORKING, OrderStatus.OPEN, ManagedExecutionStatus.WORKING),
        (ManagedExecutionStatus.WORKING, OrderStatus.CANCELLED, ManagedExecutionStatus.WORKING),
        (ManagedExecutionStatus.WORKING, OrderStatus.EXECUTED, ManagedExecutionStatus.EXECUTED),
        (ManagedExecutionStatus.WORKING, OrderStatus.EXPIRED, ManagedExecutionStatus.FAILED),
        (ManagedExecutionStatus.WORKING, OrderStatus.REJECTED, ManagedExecutionStatus.FAILED),
        (ManagedExecutionStatus.CANCEL_REQUESTED, OrderStatus.OPEN, ManagedExecutionStatus.CANCEL_REQUESTED),
        (ManagedExecutionStatus.CANCEL_REQUESTED, OrderStatus.CANCELLED, ManagedExecutionStatus.CANCEL_REQUESTED),
        (ManagedExecutionStatus.CANCEL_REQUESTED, OrderStatus.EXECUTED, ManagedExecutionStatus.EXECUTED),
        (ManagedExecutionStatus.CANCEL_REQUESTED, OrderStatus.EXPIRED, ManagedExecutionStatus.FAILED),
        (ManagedExecutionStatus.CANCEL_REQUESTED, OrderStatus.REJECTED, ManagedExecutionStatus.FAILED),
    ],
)
def test_checking_order_status_updates_managed_execution_status(
    current_status: ManagedExecutionStatus,
    order_status: OrderStatus,
    expected_status: ManagedExecutionStatus,
):
    assert (
        managed_execution_status_after_order_check(
            current_status=current_status,
            order_status=order_status,
        )
        == expected_status
    )


def test_invalid_status_change_fails_loudly():
    with pytest.raises(InvalidManagedExecutionStatusChange, match="from PRE_SUBMISSION to CANCELLED"):
        managed_execution_status_after_change(
            current_status=ManagedExecutionStatus.PRE_SUBMISSION,
            next_status=ManagedExecutionStatus.CANCELLED,
        )


@pytest.mark.parametrize("terminal_status", TERMINAL_MANAGED_EXECUTION_STATUSES)
def test_terminal_managed_execution_statuses_cannot_be_overwritten(
    terminal_status: ManagedExecutionStatus,
):
    with pytest.raises(InvalidManagedExecutionStatusChange, match="already terminal"):
        managed_execution_status_after_change(
            current_status=terminal_status,
            next_status=ManagedExecutionStatus.WORKING,
        )


def test_terminal_managed_execution_status_can_be_reapplied_idempotently():
    assert (
        managed_execution_status_after_change(
            current_status=ManagedExecutionStatus.EXECUTED,
            next_status=ManagedExecutionStatus.EXECUTED,
        )
        == ManagedExecutionStatus.EXECUTED
    )
