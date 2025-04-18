from fianchetto_tradebot.common.api.request import Request


class GetAccountInfoRequest(Request):
    account_id: str
