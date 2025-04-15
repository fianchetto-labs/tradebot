from fianchetto_tradebot.common.api.request import Request


class CancelOrderRequest(Request):
    account_id: str
    order_id: str