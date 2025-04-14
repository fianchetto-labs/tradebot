from fianchetto_tradebot.common.api.orders.order_cancellation_message import OrderCancellationMessage


class ETradeOrderResponseMessage(OrderCancellationMessage):
    def __init__(self, code: str, description: str, message_type:str):
        super().__init__(message=description)
        self.code = code
        self.type = message_type