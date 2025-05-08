from fianchetto_tradebot.common.api.request import Request


class GetAccountBalanceRequest(Request):
    account_id: str
