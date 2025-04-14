from enum import Enum

from fianchetto_tradebot.common.finance.amount import Amount


class BrokerageCallType(Enum):
    CASH = 0,
    FED = 1,
    HOUSE = 2,
    MIN_EQUITY = 3,
    UNKNOWN = 4

    @staticmethod
    def from_string(input: str):
        if "cash" in input.lower():
            return BrokerageCallType.CASH
        if "fed" in input.lower():
            return BrokerageCallType.FED
        if "house" in input.lower():
            return BrokerageCallType.HOUSE
        if "minequity" in input.lower():
            return BrokerageCallType.MIN_EQUITY
        return BrokerageCallType.UNKNOWN

class BrokerageCall:
    def __init__(self, call_type: BrokerageCallType, call_amount: Amount):
        self.call_type: BrokerageCallType = call_type
        self.call_amount: Amount = call_amount