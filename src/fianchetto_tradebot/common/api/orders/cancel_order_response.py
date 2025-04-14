from fianchetto_tradebot.common.api.orders.order_cancellation_message import OrderCancellationMessage
from fianchetto_tradebot.common.api.request import Request
from fianchetto_tradebot.common.api.request_status import RequestStatus


class CancelOrderResponse(Request):
    def __init__(self, order_id: str, cancel_time: str, messages: list[OrderCancellationMessage], request_status: RequestStatus=RequestStatus.SUCCESS):
        self.order_id = order_id
        self.cancel_time = cancel_time
        self.messages = messages
        self.request_status: RequestStatus = request_status
