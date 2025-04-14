from fianchetto_tradebot.common.api.request import Request


class GetOrderRequest(Request):
    account_id: str
    order_id: str
