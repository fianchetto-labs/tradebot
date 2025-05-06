from enum import Enum


class Brokerage(str, Enum):
    ETRADE = "etrade"
    IKBR = "ikbr"
    SCHWAB = "schwab"
