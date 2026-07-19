from typing import Protocol, runtime_checkable

from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest


@runtime_checkable
class OrderServicePort(Protocol):
    """Order dependency surface required by managed execution services."""

    def get_order(self, get_order_request: GetOrderRequest) -> GetOrderResponse:
        ...

    def cancel_order(self, cancel_order_request: CancelOrderRequest) -> CancelOrderResponse:
        ...

    def preview_and_place_order(self, preview_order_request: PreviewOrderRequest) -> PlaceOrderResponse:
        ...

    def modify_order(self, preview_modify_order_request: PreviewModifyOrderRequest) -> PlaceOrderResponse:
        ...
