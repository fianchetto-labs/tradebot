from typing import Optional

from fianchetto_tradebot.common_models.api.orders.order_cancellation_message import OrderCancellationMessage
from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.api.request_status import RequestStatus


class CancelOrderResponse(Request):
    order_id: str
    cancel_time: Optional[str]
    messages: list[OrderCancellationMessage]
    request_status: RequestStatus = RequestStatus.SUCCESS
