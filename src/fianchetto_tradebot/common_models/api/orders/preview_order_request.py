from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.order.order import Order

class PreviewOrderRequest(Request):
    order_metadata: OrderMetadata
    order: Order
