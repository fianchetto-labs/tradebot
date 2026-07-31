from enum import Enum


class Brokerage(str, Enum):
    ETRADE = "etrade"
    IBKR = "ibkr"
    SCHWAB = "schwab"
