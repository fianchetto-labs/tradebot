import httpx

from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.service.adapters.http_service_adapter import HttpServiceAdapter
from fianchetto_tradebot.server.common.service.ports import OrderServicePort


class HttpOrderServiceAdapter(HttpServiceAdapter, OrderServicePort):
    def __init__(self, brokerage: Brokerage, orders_base_url: str, client: httpx.Client | None = None):
        super().__init__(orders_base_url, client)
        self.brokerage = brokerage

    def get_order(self, get_order_request: GetOrderRequest) -> GetOrderResponse:
        response = self._request(
            "GET",
            f"/api/v1/{self.brokerage.value}/accounts/{get_order_request.account_id}/orders/{get_order_request.order_id}",
        )
        return GetOrderResponse.model_validate(response.json())

    def cancel_order(self, cancel_order_request: CancelOrderRequest) -> CancelOrderResponse:
        response = self._request(
            "DELETE",
            f"/api/v1/{self.brokerage.value}/accounts/{cancel_order_request.account_id}/orders/{cancel_order_request.order_id}",
        )
        return CancelOrderResponse.model_validate(response.json())

    def preview_and_place_order(self, preview_order_request: PreviewOrderRequest) -> PlaceOrderResponse:
        account_id = preview_order_request.order_metadata.account_id
        response = self._request(
            "POST",
            f"/api/v1/{self.brokerage.value}/accounts/{account_id}/orders/preview_and_place",
            json=self._json_payload(preview_order_request),
        )
        return PlaceOrderResponse.model_validate(response.json())

    def modify_order(self, preview_modify_order_request: PreviewModifyOrderRequest) -> PlaceOrderResponse:
        account_id = preview_modify_order_request.order_metadata.account_id
        order_id = preview_modify_order_request.order_id_to_modify
        response = self._request(
            "PUT",
            f"/api/v1/{self.brokerage.value}/accounts/{account_id}/orders/{order_id}",
            json=self._json_payload(preview_modify_order_request),
        )
        return PlaceOrderResponse.model_validate(response.json())
