from fianchetto_tradebot.common_models.api.request import Request


class GetAccountBalanceRequest(Request):
    account_id: str
