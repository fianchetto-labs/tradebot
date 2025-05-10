from abc import ABC
from typing import Optional

from pydantic import BaseModel

from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.tradable_type import TradableType


class Tradable(BaseModel, ABC):
    price: Optional[Price] = None

    def set_price(self, price: Price):
        self.price: Price = price

    def get_type(self)->TradableType:
        pass

