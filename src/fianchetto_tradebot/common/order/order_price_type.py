from enum import Enum


class OrderPriceType(str, Enum):
    MARKET = "MARKET"
    NET_EVEN = "NET_EVEN"
    NET_CREDIT = "NET_CREDIT"
    NET_DEBIT = "NET_DEBIT"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP_CNST_BY_LOWER_TRIGGER = "TRAILING_STOP_CNST_BY_LOWER_TRIGGER"
    MARKET_ON_CLOSE = "MARKET_ON_CLOSE"
    LIMIT_ON_OPEN = "LIMIT_ON_OPEN"
    LIMIT_ON_CLOSE = "LIMIT_ON_CLOSE"
    TRAILING_STOP_PRCT = "TRAILING_STOP_PRCT"
    UPPER_TRIGGER_BY_HIDDEN_STOP = "UPPER_TRIGGER_BY_HIDDEN_STOP"

    def __str__(self):
        return self.name  # Ensures string conversion returns the name