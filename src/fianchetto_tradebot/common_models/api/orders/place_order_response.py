from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.order_placement_message import OrderPlacementMessage
from fianchetto_tradebot.common_models.api.response import Response
from fianchetto_tradebot.common_models.order.order import Order


class PlaceOrderResponse(Response):
    order_metadata: OrderMetadata
    preview_id: str
    order_id: str
    # Why isn't this a PlacedOrder? Likely b/c some fields aren't available
    order: Order
    order_placement_messages: list[OrderPlacementMessage] = []