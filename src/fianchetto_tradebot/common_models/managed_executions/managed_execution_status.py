from enum import Enum

from fianchetto_tradebot.common_models.order.order_status import OrderStatus


class ManagedExecutionStatus(str, Enum):
    PRE_SUBMISSION = "PRE_SUBMISSION"
    WORKING = "WORKING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ManagedExecutionTransitionEvent(str, Enum):
    BROKERAGE_ORDER_OBSERVED = "BROKERAGE_ORDER_OBSERVED"
    MANAGEMENT_CONTINUES = "MANAGEMENT_CONTINUES"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCEL_COMPLETED = "CANCEL_COMPLETED"
    WORKER_FAILED = "WORKER_FAILED"


class InvalidManagedExecutionTransition(ValueError):
    pass


TERMINAL_MANAGED_EXECUTION_STATUSES = frozenset(
    {
        ManagedExecutionStatus.CANCELLED,
        ManagedExecutionStatus.EXECUTED,
        ManagedExecutionStatus.FAILED,
    }
)


def is_terminal_managed_execution_status(status: ManagedExecutionStatus) -> bool:
    return status in TERMINAL_MANAGED_EXECUTION_STATUSES


def managed_execution_status_from_order_status(order_status: OrderStatus) -> ManagedExecutionStatus:
    if order_status == OrderStatus.EXECUTED:
        return ManagedExecutionStatus.EXECUTED
    if order_status in {OrderStatus.EXPIRED, OrderStatus.REJECTED}:
        return ManagedExecutionStatus.FAILED
    if order_status == OrderStatus.ANY:
        raise ValueError("OrderStatus.ANY is a query filter, not a brokerage lifecycle status")
    return ManagedExecutionStatus.WORKING


def transition_for_brokerage_order_observation(
    current_status: ManagedExecutionStatus,
    order_status: OrderStatus,
) -> ManagedExecutionStatus:
    target_status = managed_execution_status_from_order_status(order_status)
    if (
        current_status == ManagedExecutionStatus.CANCEL_REQUESTED
        and target_status == ManagedExecutionStatus.WORKING
    ):
        target_status = ManagedExecutionStatus.CANCEL_REQUESTED
    return apply_managed_execution_transition(
        current_status=current_status,
        target_status=target_status,
        event=ManagedExecutionTransitionEvent.BROKERAGE_ORDER_OBSERVED,
    )


def transition_for_management_continuing(
    current_status: ManagedExecutionStatus,
) -> ManagedExecutionStatus:
    target_status = (
        ManagedExecutionStatus.CANCEL_REQUESTED
        if current_status == ManagedExecutionStatus.CANCEL_REQUESTED
        else ManagedExecutionStatus.WORKING
    )
    return apply_managed_execution_transition(
        current_status=current_status,
        target_status=target_status,
        event=ManagedExecutionTransitionEvent.MANAGEMENT_CONTINUES,
    )


def transition_for_cancel_requested(
    current_status: ManagedExecutionStatus,
) -> ManagedExecutionStatus:
    return apply_managed_execution_transition(
        current_status=current_status,
        target_status=ManagedExecutionStatus.CANCEL_REQUESTED,
        event=ManagedExecutionTransitionEvent.CANCEL_REQUESTED,
    )


def transition_for_cancel_completed(
    current_status: ManagedExecutionStatus,
) -> ManagedExecutionStatus:
    return apply_managed_execution_transition(
        current_status=current_status,
        target_status=ManagedExecutionStatus.CANCELLED,
        event=ManagedExecutionTransitionEvent.CANCEL_COMPLETED,
    )


def transition_for_worker_failed(
    current_status: ManagedExecutionStatus,
) -> ManagedExecutionStatus:
    return apply_managed_execution_transition(
        current_status=current_status,
        target_status=ManagedExecutionStatus.FAILED,
        event=ManagedExecutionTransitionEvent.WORKER_FAILED,
    )


def apply_managed_execution_transition(
    current_status: ManagedExecutionStatus,
    target_status: ManagedExecutionStatus,
    event: ManagedExecutionTransitionEvent,
) -> ManagedExecutionStatus:
    if current_status == target_status:
        return current_status

    if is_terminal_managed_execution_status(current_status):
        raise InvalidManagedExecutionTransition(
            f"Cannot apply {event.value}: managed execution is already terminal "
            f"with status {current_status.value}"
        )

    allowed_targets = _ALLOWED_MANAGED_EXECUTION_TRANSITIONS.get(current_status, frozenset())
    if target_status not in allowed_targets:
        raise InvalidManagedExecutionTransition(
            f"Cannot apply {event.value}: {current_status.value} -> {target_status.value} "
            "is not an allowed managed execution transition"
        )

    return target_status


_ALLOWED_MANAGED_EXECUTION_TRANSITIONS = {
    ManagedExecutionStatus.PRE_SUBMISSION: frozenset(
        {
            ManagedExecutionStatus.WORKING,
            ManagedExecutionStatus.CANCEL_REQUESTED,
            ManagedExecutionStatus.EXECUTED,
            ManagedExecutionStatus.FAILED,
        }
    ),
    ManagedExecutionStatus.WORKING: frozenset(
        {
            ManagedExecutionStatus.WORKING,
            ManagedExecutionStatus.CANCEL_REQUESTED,
            ManagedExecutionStatus.EXECUTED,
            ManagedExecutionStatus.FAILED,
        }
    ),
    ManagedExecutionStatus.CANCEL_REQUESTED: frozenset(
        {
            ManagedExecutionStatus.CANCEL_REQUESTED,
            ManagedExecutionStatus.CANCELLED,
            ManagedExecutionStatus.EXECUTED,
            ManagedExecutionStatus.FAILED,
        }
    ),
}
