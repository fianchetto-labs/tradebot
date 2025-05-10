from fianchetto_tradebot.common_models.api.request import Request


class GetAccountRequest(Request):
    account_id: str
