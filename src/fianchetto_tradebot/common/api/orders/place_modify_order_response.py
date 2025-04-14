from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_placement_message import OrderPlacementMessage
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.order.order import Order


class PlaceModifyOrderResponse(PlaceOrderResponse):
    def __init__(self, order_metadata: OrderMetadata, preview_id: str, previous_order_id: str, order_id: str, order: Order,
                 order_placement_messages: list[OrderPlacementMessage]):
        super().__init__(order_metadata, preview_id, order_id, order, order_placement_messages)
        self.previous_order_id = previous_order_id
