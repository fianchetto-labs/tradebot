from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common.order.order import Order

class PreviewModifyOrderRequest(PreviewOrderRequest):
    def __init__(self, order_metadata: OrderMetadata, order_id: str, order: Order):
        super().__init__(order_metadata, order)
        self.order_id_to_modify = order_id