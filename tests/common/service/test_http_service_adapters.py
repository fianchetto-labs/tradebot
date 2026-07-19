import json
from datetime import date, datetime

import httpx
import pytest

from common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.common_models.api.request_status import RequestStatus
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder
from fianchetto_tradebot.common_models.order.placed_order_details import PlacedOrderDetails
from fianchetto_tradebot.server.common.service.adapters import (
    DEFAULT_ORDERS_SERVICE_URL,
    DEFAULT_QUOTES_SERVICE_URL,
    ORDERS_SERVICE_URL_ENV_VAR,
    QUOTES_SERVICE_URL_ENV_VAR,
    HttpOrderServiceAdapter,
    HttpQuoteServiceAdapter,
    HttpServiceAdapterError,
    ServiceAdapters,
    build_http_service_adapters,
    load_http_service_adapter_config,
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _json_response(model) -> httpx.Response:
    return httpx.Response(200, json=model.model_dump(mode="json"))


def _order_metadata(account_id: str = "acct-1") -> OrderMetadata:
    return OrderMetadata(order_type=OrderType.SPREADS, account_id=account_id, client_order_id="client-1")


def _order() -> Order:
    return OrderTestUtil.build_spread_order()


def _preview_order_request(account_id: str = "acct-1") -> PreviewOrderRequest:
    return PreviewOrderRequest(order_metadata=_order_metadata(account_id), order=_order())


def _place_order_response(order_id: str = "order-1") -> PlaceOrderResponse:
    return PlaceOrderResponse(
        order_metadata=_order_metadata(),
        preview_id="preview-1",
        order_id=order_id,
        order=_order(),
    )


def _get_order_response(order_id: str = "order-1") -> GetOrderResponse:
    placed_order_details = PlacedOrderDetails(
        account_id="acct-1",
        brokerage_order_id=order_id,
        status=OrderStatus.OPEN,
        order_placed_time=datetime(2026, 1, 1, 12, 0, 0),
        current_market_price=Price(bid=1.0, ask=1.2),
    )
    return GetOrderResponse(
        placed_order=PlacedOrder(order=_order(), placed_order_details=placed_order_details)
    )


def test_http_adapter_config_reads_generic_service_urls():
    config = load_http_service_adapter_config(
        {
            ORDERS_SERVICE_URL_ENV_VAR: "http://orders:8080",
            QUOTES_SERVICE_URL_ENV_VAR: "http://quotes:8081",
        }
    )

    assert config.orders_base_url == "http://orders:8080"
    assert config.quotes_base_url == "http://quotes:8081"


def test_http_adapter_config_defaults_to_local_service_urls():
    config = load_http_service_adapter_config({})

    assert config.orders_base_url == DEFAULT_ORDERS_SERVICE_URL
    assert config.quotes_base_url == DEFAULT_QUOTES_SERVICE_URL


def test_build_http_service_adapters_creates_port_adapters_from_shared_container():
    config = load_http_service_adapter_config(
        {
            ORDERS_SERVICE_URL_ENV_VAR: "http://orders:8080",
            QUOTES_SERVICE_URL_ENV_VAR: "http://quotes:8081",
        }
    )

    service_adapters = build_http_service_adapters([Brokerage.ETRADE, Brokerage.IBKR], config)

    assert isinstance(service_adapters, ServiceAdapters)
    assert isinstance(service_adapters.order_services[Brokerage.ETRADE], HttpOrderServiceAdapter)
    assert isinstance(service_adapters.quote_services[Brokerage.ETRADE], HttpQuoteServiceAdapter)
    assert isinstance(service_adapters.order_services[Brokerage.IBKR], HttpOrderServiceAdapter)
    assert isinstance(service_adapters.quote_services[Brokerage.IBKR], HttpQuoteServiceAdapter)


def test_http_order_adapter_gets_order():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/etrade/accounts/acct-1/orders/order-1"
        return _json_response(_get_order_response())

    adapter = HttpOrderServiceAdapter(
        brokerage=Brokerage.ETRADE,
        orders_base_url="http://orders:8080",
        client=_client(handler),
    )

    response = adapter.get_order(GetOrderRequest(account_id="acct-1", order_id="order-1"))

    assert response.placed_order.placed_order_details.brokerage_order_id == "order-1"


def test_http_order_adapter_cancels_order():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/api/v1/etrade/accounts/acct-1/orders/order-1"
        return _json_response(
            CancelOrderResponse(
                order_id="order-1",
                cancel_time="2026-01-01T12:00:00",
                messages=[],
                request_status=RequestStatus.SUCCESS,
            )
        )

    adapter = HttpOrderServiceAdapter(
        brokerage=Brokerage.ETRADE,
        orders_base_url="http://orders:8080",
        client=_client(handler),
    )

    response = adapter.cancel_order(CancelOrderRequest(account_id="acct-1", order_id="order-1"))

    assert response.order_id == "order-1"


def test_http_order_adapter_preview_and_place_uses_json_mode_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/etrade/accounts/acct-1/orders/preview_and_place"
        payload = json.loads(request.content)
        assert payload["order_metadata"]["order_type"] == "SPREADS"
        assert payload["order"]["order_lines"][0]["tradable"]["expiry"] == "2025-01-31"
        assert payload["order"]["order_price"]["order_price_type"] == "NET_CREDIT"
        return _json_response(_place_order_response())

    adapter = HttpOrderServiceAdapter(
        brokerage=Brokerage.ETRADE,
        orders_base_url="http://orders:8080/",
        client=_client(handler),
    )

    response = adapter.preview_and_place_order(_preview_order_request())

    assert response.order_id == "order-1"


def test_http_order_adapter_modifies_order_using_path_order_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == "/api/v1/etrade/accounts/acct-1/orders/order-1"
        payload = json.loads(request.content)
        assert payload["order_id_to_modify"] == "order-1"
        return _json_response(_place_order_response(order_id="order-2"))

    adapter = HttpOrderServiceAdapter(
        brokerage=Brokerage.ETRADE,
        orders_base_url="http://orders:8080",
        client=_client(handler),
    )
    request = PreviewModifyOrderRequest(
        order_metadata=_order_metadata(),
        order=_order(),
        order_id_to_modify="order-1",
    )

    response = adapter.modify_order(request)

    assert response.order_id == "order-2"


def test_http_quote_adapter_gets_equity_quote():
    tradable = Equity(ticker="GE")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/etrade/quotes/tradable/GE"
        return _json_response(
            GetTradableResponse(
                tradable=tradable,
                current_price=Price(bid=100, ask=101),
                volume=1000,
            )
        )

    adapter = HttpQuoteServiceAdapter(
        brokerage=Brokerage.ETRADE,
        quotes_base_url="http://quotes:8081",
        client=_client(handler),
    )

    response = adapter.get_tradable_quote(GetTradableRequest(tradable=tradable))

    assert response.tradable == tradable
    assert response.current_price.bid == 100


def test_http_quote_adapter_gets_option_quote_with_encoded_symbol():
    tradable = Option(
        equity=Equity(ticker="GE"),
        type=OptionType.PUT,
        strike=Amount(whole=25, part=0, currency=Currency.US_DOLLARS),
        expiry=date(2026, 1, 16),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert "GE%3A2026%3A1%3A16%3APUT%3A25.0" in str(request.url)
        return _json_response(
            GetTradableResponse(
                tradable=tradable,
                current_price=Price(bid=1.0, ask=1.2),
                volume=100,
            )
        )

    adapter = HttpQuoteServiceAdapter(
        brokerage=Brokerage.ETRADE,
        quotes_base_url="http://quotes:8081",
        client=_client(handler),
    )

    response = adapter.get_tradable_quote(GetTradableRequest(tradable=tradable))

    assert response.tradable == tradable


def test_http_adapter_raises_application_error_for_http_failure():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    adapter = HttpQuoteServiceAdapter(
        brokerage=Brokerage.ETRADE,
        quotes_base_url="http://quotes:8081",
        client=_client(handler),
    )

    with pytest.raises(HttpServiceAdapterError) as exc_info:
        adapter.get_tradable_quote(GetTradableRequest(tradable=Equity(ticker="GE")))

    assert exc_info.value.status_code == 503
    assert exc_info.value.response_text == "service unavailable"
