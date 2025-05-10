from fianchetto_tradebot.server.common import Account
from fianchetto_tradebot.common_models.api.response import Response


class GetAccountResponse(Response):
    account: Account

    def __str__(self):
        return f"Account: {self.account}"