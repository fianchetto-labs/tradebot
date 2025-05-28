from typing import Optional, Type

from pydantic import BaseModel

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic
from fianchetto_tradebot.server.orders.tactics.incremental_price_delta_execution_tactic import IncrementalPriceDeltaExecutionTactic


class ManagedExecution(BaseModel):
    brokerage: Brokerage
    account_id: str
    current_brokerage_order_id: Optional[str] = None
    past_brokerage_order_ids: Optional[list[str]] = []
    original_order: Order
    status: Optional[OrderStatus] = OrderStatus.PRE_SUBMISSION
    latest_order_price: OrderPrice
    reserve_order_price: OrderPrice
    tactic: Type[ExecutionTactic] = IncrementalPriceDeltaExecutionTactic