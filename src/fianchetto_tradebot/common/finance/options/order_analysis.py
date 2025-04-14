from abc import ABC

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.order.order_type import OrderType


class OrderAnalysis(ABC):
    def get_order_type(self) -> OrderType:
        pass

    def get_collateral_required(self) -> Amount:
        pass