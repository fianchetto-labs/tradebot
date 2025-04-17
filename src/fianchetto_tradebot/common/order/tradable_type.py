from enum import Enum


class TradableType(str, Enum):
    Equity = "EQ"
    Option = "OPTN"

    # Not yet supported
    MutualFund = "MF"

    # Not yet supported
    MoneyMarketFund = "MMF"
