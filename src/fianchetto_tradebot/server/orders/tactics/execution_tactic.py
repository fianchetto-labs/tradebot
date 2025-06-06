from __future__ import annotations

from abc import ABC
from typing import Type

from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder

TACTIC_REGISTRY = {}

def register_tactic(cls: Type[ExecutionTactic]) -> Type[ExecutionTactic]:
    TACTIC_REGISTRY[cls.__name__] = cls
    return cls

class ExecutionTactic(ABC):
    @staticmethod
    def new_price(order: PlacedOrder)->(OrderPrice, int):
        pass
