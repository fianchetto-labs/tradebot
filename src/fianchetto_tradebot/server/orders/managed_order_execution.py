from pydantic import BaseModel

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic


class ManagedExecution(BaseModel):
    managed_execution_id: str
    brokerage: Brokerage
    brokerage_order_id: str
    status: OrderStatus
    latest_order_price: OrderPrice
    tactic: ExecutionTactic