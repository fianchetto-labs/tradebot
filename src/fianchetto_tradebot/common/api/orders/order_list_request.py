from datetime import datetime

from fianchetto_tradebot.common.api.request import Request
from fianchetto_tradebot.common.order.order_status import OrderStatus


DEFAULT_ORDER_LIST_COUNT = 50


class ListOrdersRequest(Request):
    account_id: str
    status: OrderStatus
    from_date: datetime
    to_date: datetime
    count: int = DEFAULT_ORDER_LIST_COUNT