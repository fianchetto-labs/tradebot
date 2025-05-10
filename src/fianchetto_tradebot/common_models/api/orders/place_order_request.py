from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.order.order import Order

class PlaceOrderRequest(Request):
    order_metadata: OrderMetadata
    preview_id: str
    order: Order
