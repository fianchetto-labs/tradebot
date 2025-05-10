from fianchetto_tradebot.common_models.account.account_balance import AccountBalance
from fianchetto_tradebot.common_models.api.response import Response


class GetAccountBalanceResponse(Response):
    account_balance: AccountBalance

    def __str__(self):
        return f"AccountBalance: {self.account_balance}"