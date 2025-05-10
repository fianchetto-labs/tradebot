from typing import Optional

from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.order.order_type import OrderType


class OrderMetadata(Request):
    order_type: OrderType
    account_id: str
    client_order_id: Optional[str] = None
