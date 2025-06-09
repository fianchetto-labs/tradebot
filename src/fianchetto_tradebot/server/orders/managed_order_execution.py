from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel, field_validator

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic, TACTIC_REGISTRY, register_tactic
from fianchetto_tradebot.server.orders.tactics.incremental_price_delta_execution_tactic import IncrementalPriceDeltaExecutionTactic

@register_tactic
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

    def model_dump_json(self, **kwargs) -> str:
        return super().model_dump_json(
            **kwargs,
            fallback=self._json_fallback
        )

    @field_validator("tactic", mode="before")
    @classmethod
    def deserialize_tactic(cls, value):
        if isinstance(value, str):
            try:
                return TACTIC_REGISTRY[value]
            except KeyError:
                raise ValueError(f"Unknown tactic class name: {value}")
        return value

    @staticmethod
    def _json_fallback(obj):
        if isinstance(obj, type):  # class objects like IncrementalPriceDeltaExecutionTactic
            return obj.__name__
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
