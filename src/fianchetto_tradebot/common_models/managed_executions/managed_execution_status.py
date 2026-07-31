from enum import Enum


class ManagedExecutionStatus(str, Enum):
    PRE_SUBMISSION = "PRE_SUBMISSION"
    WORKING = "WORKING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
