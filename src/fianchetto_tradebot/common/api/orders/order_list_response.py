from typing import Union

from fianchetto_tradebot.common.api.response import Response
from fianchetto_tradebot.common.order.executed_order import ExecutedOrder
from fianchetto_tradebot.common.order.placed_order import PlacedOrder


class ListOrdersResponse(Response):
    order_list: list[Union[PlacedOrder, ExecutedOrder]]

    def get_order_list(self):
        return self.order_list

    def __str__(self):
        return f"Order List: {str(self.order_list)}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return { "order_list" : self.order_list}