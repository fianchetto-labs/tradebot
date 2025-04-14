from fianchetto_tradebot.common.api.request import Request


class GetAccountBalanceRequest(Request):
    def __init__(self, account_id):
        self.account_id = account_id
