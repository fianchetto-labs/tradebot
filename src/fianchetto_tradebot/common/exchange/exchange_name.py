from enum import Enum


class ExchangeName(str, Enum):
    ETRADE = "etrade"
    IKBR = "ikbr"
    SCHWAB = "schwab"
