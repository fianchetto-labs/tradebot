from abc import ABC

from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder


class ExecutionTactic(ABC):
    @staticmethod
    def new_price(order: PlacedOrder)->(OrderPrice, int):
        pass
