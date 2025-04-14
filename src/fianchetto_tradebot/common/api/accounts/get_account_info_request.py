from fianchetto_tradebot.common.api.request import Request


class GetAccountInfoRequest(Request):
    def __init__(self, account_id):
        self.account_id = account_id
