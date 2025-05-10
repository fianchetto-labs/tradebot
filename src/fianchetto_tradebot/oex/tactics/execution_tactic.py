from abc import ABC

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder


class ExecutionTactic(ABC):
    @staticmethod
    def new_price_and_order_placement_time(order: PlacedOrder)->(Amount, int):
        pass
