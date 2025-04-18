import logging
from datetime import datetime

from pydantic import BaseModel

from fianchetto_tradebot.common.account.brokerage_call import BrokerageCall
from fianchetto_tradebot.common.account.computed_balance import ComputedBalance
from fianchetto_tradebot.common.finance.amount import Amount

logger = logging.getLogger(__name__)

class AccountBalance(BaseModel):
    account_id: str
    total_account_value: Amount
    as_of_date: datetime
    computed_balance: ComputedBalance
    brokerage_calls: list[BrokerageCall]

    def __str__(self):
        return f"{' - '.join([str(self.__getattribute__(x)) for x in self.__dict__ if self.__getattribute__(x)])}"

    def __repr__(self):
        return self.__str__()