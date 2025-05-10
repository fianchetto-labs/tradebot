from fianchetto_tradebot.server.common import AccountBalance
from fianchetto_tradebot.common_models.api.response import Response


class GetAccountBalanceResponse(Response):
    account_balance: AccountBalance

    def __str__(self):
        return f"AccountBalance: {self.account_balance}"