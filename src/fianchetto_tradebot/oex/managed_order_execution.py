from pydantic import BaseModel

from fianchetto_tradebot.common.order.order_price import OrderPrice
from fianchetto_tradebot.common.order.order_status import OrderStatus


class ManagedOrderExecution(BaseModel):
    managed_order_execution_id: str
    exchange_order_id: str
    status: OrderStatus
    latest_order_price: OrderPrice