from __future__ import annotations

from abc import ABC
from typing import Type

from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice

TACTIC_REGISTRY = {}

def register_tactic(cls: Type[ExecutionTactic]) -> Type[ExecutionTactic]:
    TACTIC_REGISTRY[cls.__name__] = cls
    return cls

class ExecutionTactic(ABC):
    @staticmethod
    def new_price(order: Order)->(OrderPrice, int):
        pass
