from enum import Enum

from pydantic import BaseModel

from fianchetto_tradebot.common.finance.amount import Amount


class BrokerageCallType(str, Enum):
    CASH = "CASH"
    FED = "FED"
    HOUSE = "HOUSE"
    MIN_EQUITY = "MIN_EQUITY"
    UNKNOWN = "UNKNOWN"

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

class BrokerageCall(BaseModel):
    call_type: BrokerageCallType
    call_amount: Amount