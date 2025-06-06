from __future__ import annotations

import json
from typing import Optional, Type

from pydantic import BaseModel, ConfigDict, field_validator

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic, TACTIC_REGISTRY
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

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            ManagedExecution: lambda m: m.model_dump(mode="json"),
            type: lambda t: t.__name__,
        }
    )

    @field_validator("tactic", mode="before")
    @classmethod
    def load_tactic_from_string(cls, v):
        if isinstance(v, str):
            if v in TACTIC_REGISTRY:
                return TACTIC_REGISTRY[v]
            raise ValueError(f"Unknown tactic class name: {v}")
        return v

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        if isinstance(self.tactic, type):
            data["tactic"] = self.tactic.__name__
        return data

    def model_dump_json(self, *args, **kwargs):
        return json.dumps(self.model_dump(*args, **kwargs), *args, **kwargs)