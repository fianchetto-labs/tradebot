from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.request import Request
from fianchetto_tradebot.common.order.order import Order

class PlaceOrderRequest(Request):
    order_metadata: OrderMetadata
    preview_id: str
    order: Order
