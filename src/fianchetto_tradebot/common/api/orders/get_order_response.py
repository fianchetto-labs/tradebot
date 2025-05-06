from typing import Union

from fianchetto_tradebot.common.api.response import Response
from fianchetto_tradebot.common.order.executed_order import ExecutedOrder
from fianchetto_tradebot.common.order.placed_order import PlacedOrder


class GetOrderResponse(Response):
    placed_order: Union[PlacedOrder, ExecutedOrder]

    def __str__(self):
        return f"Order: {self.placed_order}"
