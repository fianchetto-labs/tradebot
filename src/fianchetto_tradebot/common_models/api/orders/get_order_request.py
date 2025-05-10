from fianchetto_tradebot.common_models.api.request import Request


class GetOrderRequest(Request):
    account_id: str
    order_id: str
