from datetime import datetime

from fianchetto_tradebot.common.api.request import Request
from fianchetto_tradebot.common.order.order_status import OrderStatus


DEFAULT_ORDER_LIST_COUNT = 50


class ListOrdersRequest(Request):
    def __init__(self, account_id: str, status: OrderStatus, from_date: datetime.date,
                    to_date: datetime.date, max_count=DEFAULT_ORDER_LIST_COUNT):
        self.account_id = account_id
        self.status = status
        self.from_date = from_date
        self.to_date = to_date
        self.count = max_count