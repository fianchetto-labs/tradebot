
from fianchetto_tradebot.common.api.orders.order_placement_message import OrderPlacementMessage


class ETradeOrderResponseMessage(OrderPlacementMessage):
    type: str
    code: str