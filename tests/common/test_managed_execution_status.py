import pytest

from fianchetto_tradebot.common_models.managed_executions.managed_execution_status import (
    ManagedExecutionStatus,
    managed_execution_status_from_order_status,
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


def test_order_status_any_is_not_a_managed_execution_lifecycle_status():
    with pytest.raises(ValueError, match="query filter"):
        managed_execution_status_from_order_status(OrderStatus.ANY)
