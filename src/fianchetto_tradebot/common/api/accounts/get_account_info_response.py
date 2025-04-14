from fianchetto_tradebot.common.account.account import Account
from fianchetto_tradebot.common.api.response import Response


class GetAccountInfoResponse(Response):
    def __init__(self, account: Account):
        self.account = account

    def __str__(self):
        return f"Account: {self.account}"