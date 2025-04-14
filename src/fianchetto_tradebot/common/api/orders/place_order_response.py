from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_placement_message import OrderPlacementMessage
from fianchetto_tradebot.common.api.response import Response
from fianchetto_tradebot.common.order.order import Order


class PlaceOrderResponse(Response):
    order_metadata: OrderMetadata
    preview_id: str
    order_id: str
    order: Order
    order_placement_messages: list[OrderPlacementMessage] = []