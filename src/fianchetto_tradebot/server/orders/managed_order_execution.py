from __future__ import annotations

from enum import Enum
from typing import Optional, Type

from pydantic import BaseModel, field_validator, model_validator

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.managed_executions.moex_status import MoexStatus
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic, TACTIC_REGISTRY, register_tactic
from fianchetto_tradebot.server.orders.tactics.incremental_price_delta_execution_tactic import IncrementalPriceDeltaExecutionTactic


class ManagedExecutionCreationType(str, Enum):
    AS_NEW_ORDER = "AS_NEW_ORDER"
    FROM_EXISTING_ORDER = "FROM_EXISTING_ORDER"

class ManagedExecutionCreationParams(BaseModel):
    managed_execution_creation_type: ManagedExecutionCreationType
    brokerage: Brokerage
    account_id: str
    # TODO: Implement as part of FIA-107
    reserve_order_price: Optional[OrderPrice] = None
    tactic: Type[ExecutionTactic] = IncrementalPriceDeltaExecutionTactic

    # TODO: Add validation
    creation_order: Optional[Order] = None
    creation_order_id: Optional[str] = None


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

    @model_validator(mode="after")
    def validate_conditionals(self) -> ManagedExecutionCreationParams:
        if self.managed_execution_creation_type == ManagedExecutionCreationType.AS_NEW_ORDER:
            if self.creation_order is None:
                raise ValueError("`creation_order` is required when creation type is AS_NEW_ORDER")
        elif self.managed_execution_creation_type == ManagedExecutionCreationType.FROM_EXISTING_ORDER:
            if self.creation_order_id is None:
                raise ValueError("`creation_order_id` is required when creation type is FROM_EXISTING_ORDER")
        return self

@register_tactic
class ManagedExecution(BaseModel):
    brokerage: Brokerage
    account_id: str

    # TODO: This can be updated to be a validation function instead of a static price
    reserve_order_price: Optional[OrderPrice] = None
    tactic: Type[ExecutionTactic] = IncrementalPriceDeltaExecutionTactic

    past_brokerage_order_ids: Optional[list[str]] = []

    # Initialization - either provide the order, or the order_id
    original_order: Optional[Order] = None
    original_order_id: Optional[str] = None

    # Status of the order, or the managed execution? I guess the Order
    status: MoexStatus
    current_brokerage_order_id: Optional[str] = None
    current_order: Optional[Order] = None

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
