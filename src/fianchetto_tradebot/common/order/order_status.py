from enum import Enum


class OrderStatus(Enum):
    OPEN = 0
    PARTIAL = 1
    EXECUTED = 2
    CANCELLED = 3
    INDIVIDUAL_FILLS = 4
    CANCEL_REQUESTED = 5
    EXPIRED = 6
    REJECTED = 7
    PRE_SUBMISSION = 8
    ANY = 9
