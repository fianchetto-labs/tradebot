from fianchetto_tradebot.common.api.response import Response
from fianchetto_tradebot.common.order.placed_order import PlacedOrder


class GetOrderResponse(Response):
    placed_order: PlacedOrder

    def __str__(self):
        return f"Order: {self.placed_order}"
