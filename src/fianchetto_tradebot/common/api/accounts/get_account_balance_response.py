from fianchetto_tradebot.common.account.account_balance import AccountBalance
from fianchetto_tradebot.common.api.response import Response


class GetAccountBalanceResponse(Response):
    account_balance: AccountBalance

    def __str__(self):
        return f"AccountBalance: {self.account_balance}"