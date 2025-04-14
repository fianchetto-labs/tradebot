from fianchetto_tradebot.common.account.account_balance import AccountBalance
from fianchetto_tradebot.common.api.response import Response


class GetAccountBalanceResponse(Response):
    def __init__(self, account_balance: AccountBalance):
        self.account_balance: AccountBalance = account_balance

    def __str__(self):
        return f"AccountBalance: {self.account_balance}"