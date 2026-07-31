from enum import Enum

from fianchetto_tradebot.common_models.order.order_status import OrderStatus


class ManagedExecutionStatus(str, Enum):
    PRE_SUBMISSION = "PRE_SUBMISSION"
    WORKING = "WORKING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


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
