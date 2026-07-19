from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.server.common.service.ports import OrderServicePort


class LocalOrderServiceAdapter(OrderServicePort):
    def __init__(self, service: OrderServicePort):
        self.service = service

    def get_order(self, get_order_request: GetOrderRequest) -> GetOrderResponse:
        return self.service.get_order(get_order_request)

    def cancel_order(self, cancel_order_request: CancelOrderRequest) -> CancelOrderResponse:
        return self.service.cancel_order(cancel_order_request)

    def preview_and_place_order(self, preview_order_request: PreviewOrderRequest) -> PlaceOrderResponse:
        return self.service.preview_and_place_order(preview_order_request)

    def modify_order(self, preview_modify_order_request: PreviewModifyOrderRequest) -> PlaceOrderResponse:
        return self.service.modify_order(preview_modify_order_request)
