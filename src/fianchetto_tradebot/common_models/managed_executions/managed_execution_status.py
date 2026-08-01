from enum import Enum

from fianchetto_tradebot.common_models.order.order_status import OrderStatus


class ManagedExecutionStatus(str, Enum):
    PRE_SUBMISSION = "PRE_SUBMISSION"
    WORKING = "WORKING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class InvalidManagedExecutionStatusChange(ValueError):
    pass


TERMINAL_MANAGED_EXECUTION_STATUSES = frozenset(
    {
        ManagedExecutionStatus.CANCELLED,
        ManagedExecutionStatus.EXECUTED,
        ManagedExecutionStatus.FAILED,
    }
)


_MANAGED_EXECUTION_STATUS_BY_ORDER_STATUS = {
    OrderStatus.OPEN: ManagedExecutionStatus.WORKING,
    OrderStatus.PARTIAL: ManagedExecutionStatus.WORKING,
    OrderStatus.INDIVIDUAL_FILLS: ManagedExecutionStatus.WORKING,
    OrderStatus.CANCEL_REQUESTED: ManagedExecutionStatus.WORKING,
    OrderStatus.PRE_SUBMISSION: ManagedExecutionStatus.WORKING,
    OrderStatus.CANCELLED: ManagedExecutionStatus.WORKING,
    OrderStatus.EXECUTED: ManagedExecutionStatus.EXECUTED,
    OrderStatus.EXPIRED: ManagedExecutionStatus.FAILED,
    OrderStatus.REJECTED: ManagedExecutionStatus.FAILED,
}


_ORDER_CHECK_STATUS_OVERRIDES = {
    (
        ManagedExecutionStatus.CANCEL_REQUESTED,
        ManagedExecutionStatus.WORKING,
    ): ManagedExecutionStatus.CANCEL_REQUESTED,
}


_ALLOWED_NEXT_MANAGED_EXECUTION_STATUSES = {
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


def is_terminal_managed_execution_status(status: ManagedExecutionStatus) -> bool:
    return status in TERMINAL_MANAGED_EXECUTION_STATUSES


def managed_execution_status_from_order_status(order_status: OrderStatus) -> ManagedExecutionStatus:
    if order_status == OrderStatus.ANY:
        raise ValueError("OrderStatus.ANY is a query filter, not a brokerage lifecycle status")
    try:
        return _MANAGED_EXECUTION_STATUS_BY_ORDER_STATUS[order_status]
    except KeyError as exc:
        raise ValueError(
            f"No managed execution status decision for order status {order_status.value}"
        ) from exc


def managed_execution_status_after_order_check(
    current_status: ManagedExecutionStatus,
    order_status: OrderStatus,
) -> ManagedExecutionStatus:
    default_next_status = managed_execution_status_from_order_status(order_status)
    next_status = _ORDER_CHECK_STATUS_OVERRIDES.get(
        (current_status, default_next_status),
        default_next_status,
    )
    return managed_execution_status_after_change(
        current_status=current_status,
        next_status=next_status,
    )


def managed_execution_status_after_change(
    current_status: ManagedExecutionStatus,
    next_status: ManagedExecutionStatus,
) -> ManagedExecutionStatus:
    if current_status == next_status:
        return current_status

    if is_terminal_managed_execution_status(current_status):
        raise InvalidManagedExecutionStatusChange(
            "Cannot change managed execution status: "
            f"{current_status.value} is already terminal"
        )

    allowed_targets = _ALLOWED_NEXT_MANAGED_EXECUTION_STATUSES.get(current_status, frozenset())
    if next_status not in allowed_targets:
        raise InvalidManagedExecutionStatusChange(
            "Cannot change managed execution status "
            f"from {current_status.value} to {next_status.value}"
        )

    return next_status
