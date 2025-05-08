from fianchetto_tradebot.common.api.request import Request


class GetAccountRequest(Request):
    account_id: str
