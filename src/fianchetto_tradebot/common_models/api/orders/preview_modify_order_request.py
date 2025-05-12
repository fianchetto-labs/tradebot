from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.order.order import Order

class PreviewModifyOrderRequest(PreviewOrderRequest):
    order_id_to_modify: str