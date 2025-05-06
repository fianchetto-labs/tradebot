from enum import Enum


class MarketSession(str, Enum):
    REGULAR = "REGULAR"
    EXTENDED = "EXTENDED"
    BOTH = "BOTH"
