from fianchetto_tradebot.common.api.request import Request


class CancelOrderRequest(Request):
    def __init__(self, account_id: str, order_id: str):
        self.account_id = account_id
        self.order_id = order_id
