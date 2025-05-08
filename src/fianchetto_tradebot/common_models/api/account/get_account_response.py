from fianchetto_tradebot.common.account.account import Account
from fianchetto_tradebot.common.api.response import Response


class GetAccountResponse(Response):
    account: Account

    def __str__(self):
        return f"Account: {self.account}"