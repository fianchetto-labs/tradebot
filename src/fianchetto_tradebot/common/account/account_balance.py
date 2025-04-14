import logging
from datetime import datetime

from fianchetto_tradebot.common.account.brokerage_call import BrokerageCall
from fianchetto_tradebot.common.account.computed_balance import ComputedBalance
from fianchetto_tradebot.common.finance.amount import Amount

logger = logging.getLogger(__name__)


class AccountBalance:
    def __init__(self, account_id: str, total_account_value: Amount, as_of_date: datetime, computed_balance: ComputedBalance, brokerage_calls:list[BrokerageCall]):
        self.account_id: str = account_id
        self.total_account_value: Amount = total_account_value
        self.as_of_date: datetime = as_of_date
        self.computed_balance: ComputedBalance = computed_balance
        self.brokerage_calls: list[BrokerageCall] = brokerage_calls

    def __str__(self):
        return f"{' - '.join([str(self.__getattribute__(x)) for x in self.__dict__ if self.__getattribute__(x)])}"

    def __repr__(self):
        return self.__str__()