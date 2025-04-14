from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.request import Request
from fianchetto_tradebot.common.order.order import Order

class PreviewOrderRequest(Request):
    order_metadata: OrderMetadata
    order: Order
