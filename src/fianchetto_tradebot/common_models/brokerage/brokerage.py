from enum import Enum


class Brokerage(str, Enum):
    ETRADE = "etrade"
    IBKR = "ibkr"
    IKBR = "ibkr"
    SCHWAB = "schwab"

    @classmethod
    def _missing_(cls, value):
        if value == "ikbr":
            return cls.IBKR
        return None
