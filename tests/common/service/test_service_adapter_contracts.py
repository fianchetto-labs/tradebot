from dataclasses import dataclass, field
from datetime import date, datetime

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

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
from fianchetto_tradebot.common_models.finance.tradable import Tradable
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder
from fianchetto_tradebot.common_models.order.placed_order_details import PlacedOrderDetails
from fianchetto_tradebot.server.common.service.adapters import (
    HttpOrderServiceAdapter,
    HttpQuoteServiceAdapter,
    HttpServiceAdapterError,
    LocalOrderServiceAdapter,
    LocalQuoteServiceAdapter,
    ServiceAdapters,
)
from fianchetto_tradebot.server.common.service.ports import OrderServicePort, QuoteServicePort

ACCOUNT_ID = "acct-1"
INITIAL_ORDER_ID = "order-1"
MODIFIED_ORDER_ID = "order-2"


@dataclass
class ContractCallLog:
    preview_order_requests: list[PreviewOrderRequest] = field(default_factory=list)
    modify_order_requests: list[PreviewModifyOrderRequest] = field(default_factory=list)
    get_order_requests: list[GetOrderRequest] = field(default_factory=list)
    cancel_order_requests: list[CancelOrderRequest] = field(default_factory=list)
    quote_requests: list[GetTradableRequest] = field(default_factory=list)


@dataclass
class AdapterContractHarness:
    service_adapters: ServiceAdapters
    call_log: ContractCallLog


class _TestClientAdapter:
    def __init__(self, app: FastAPI, base_url: str):
        self.client = TestClient(app, base_url=base_url)

    def request(self, method: str, url: str, **kwargs):
        kwargs.pop("timeout", None)
        return self.client.request(method, url, **kwargs)


class ContractOrderService(OrderServicePort):
    def __init__(self, call_log: ContractCallLog):
        self.call_log = call_log

    def preview_and_place_order(self, preview_order_request: PreviewOrderRequest) -> PlaceOrderResponse:
        self.call_log.preview_order_requests.append(preview_order_request)
        return _place_order_response(INITIAL_ORDER_ID, preview_order_request.order)

    def get_order(self, get_order_request: GetOrderRequest) -> GetOrderResponse:
        self.call_log.get_order_requests.append(get_order_request)
        return _get_order_response(get_order_request.order_id, OrderStatus.OPEN)

    def modify_order(self, preview_modify_order_request: PreviewModifyOrderRequest) -> PlaceOrderResponse:
        self.call_log.modify_order_requests.append(preview_modify_order_request)
        return _place_order_response(MODIFIED_ORDER_ID, preview_modify_order_request.order)

    def cancel_order(self, cancel_order_request: CancelOrderRequest) -> CancelOrderResponse:
        self.call_log.cancel_order_requests.append(cancel_order_request)
        return CancelOrderResponse(
            order_id=cancel_order_request.order_id,
            cancel_time="2026-01-01T12:00:00",
            messages=[],
            request_status=RequestStatus.SUCCESS,
        )


class ContractQuoteService(QuoteServicePort):
    def __init__(self, call_log: ContractCallLog):
        self.call_log = call_log

    def get_tradable_quote(self, request: GetTradableRequest) -> GetTradableResponse:
        self.call_log.quote_requests.append(request)
        return GetTradableResponse(
            tradable=request.tradable,
            current_price=Price(bid=100, ask=101),
            volume=1000,
        )


@pytest.fixture(params=["local", "http"])
def adapter_contract_harness(request) -> AdapterContractHarness:
    call_log = ContractCallLog()
    order_service = ContractOrderService(call_log)
    quote_service = ContractQuoteService(call_log)

    if request.param == "local":
        return AdapterContractHarness(
            service_adapters=ServiceAdapters(
                order_services={Brokerage.ETRADE: LocalOrderServiceAdapter(order_service)},
                quote_services={Brokerage.ETRADE: LocalQuoteServiceAdapter(quote_service)},
            ),
            call_log=call_log,
        )

    return AdapterContractHarness(
        service_adapters=ServiceAdapters(
            order_services={
                Brokerage.ETRADE: HttpOrderServiceAdapter(
                    brokerage=Brokerage.ETRADE,
                    orders_base_url="http://orders:8080",
                    client=_TestClientAdapter(_orders_app(order_service), base_url="http://orders:8080"),
                )
            },
            quote_services={
                Brokerage.ETRADE: HttpQuoteServiceAdapter(
                    brokerage=Brokerage.ETRADE,
                    quotes_base_url="http://quotes:8081",
                    client=_TestClientAdapter(_quotes_app(quote_service), base_url="http://quotes:8081"),
                )
            },
        ),
        call_log=call_log,
    )


def test_order_adapter_contract_preserves_order_lifecycle(
        adapter_contract_harness: AdapterContractHarness,
):
    # Given
    # A local or HTTP order adapter backed by the same fake order service.
    order_adapter = adapter_contract_harness.service_adapters.order_services[Brokerage.ETRADE]
    preview_request = _preview_order_request()

    # When
    # The caller runs the order lifecycle through the adapter.
    place_response = order_adapter.preview_and_place_order(preview_request)
    get_response = order_adapter.get_order(GetOrderRequest(account_id=ACCOUNT_ID, order_id=place_response.order_id))
    modify_response = order_adapter.modify_order(_preview_modify_order_request(place_response.order_id))
    cancel_response = order_adapter.cancel_order(
        CancelOrderRequest(account_id=ACCOUNT_ID, order_id=modify_response.order_id)
    )

    # Then
    # The caller receives the same domain responses regardless of adapter mode.
    assert place_response.order_id == INITIAL_ORDER_ID
    assert get_response.placed_order.placed_order_details.brokerage_order_id == INITIAL_ORDER_ID
    assert modify_response.order_id == MODIFIED_ORDER_ID
    assert cancel_response.order_id == MODIFIED_ORDER_ID

    # And
    # The service behind the adapter receives rich Pydantic request models with the expected data.
    call_log = adapter_contract_harness.call_log
    assert call_log.preview_order_requests[0].order_metadata.account_id == ACCOUNT_ID
    assert call_log.preview_order_requests[0].order.order_lines[0].tradable.expiry == date(2025, 1, 31)
    assert call_log.get_order_requests == [GetOrderRequest(account_id=ACCOUNT_ID, order_id=INITIAL_ORDER_ID)]
    assert call_log.modify_order_requests[0].order_id_to_modify == INITIAL_ORDER_ID
    assert call_log.cancel_order_requests == [CancelOrderRequest(account_id=ACCOUNT_ID, order_id=MODIFIED_ORDER_ID)]


def test_quote_adapter_contract_handles_equity_and_option_quotes(
        adapter_contract_harness: AdapterContractHarness,
):
    # Given
    # A local or HTTP quote adapter backed by the same fake quote service.
    quote_adapter = adapter_contract_harness.service_adapters.quote_services[Brokerage.ETRADE]
    equity = Equity(ticker="GE")
    option = Option(
        equity=Equity(ticker="GE"),
        type=OptionType.PUT,
        strike=Amount(whole=25, part=0, currency=Currency.US_DOLLARS),
        expiry=date(2026, 1, 16),
    )

    # When
    # The caller requests an equity quote and an option quote through the adapter.
    equity_response = quote_adapter.get_tradable_quote(GetTradableRequest(tradable=equity))
    option_response = quote_adapter.get_tradable_quote(GetTradableRequest(tradable=option))

    # Then
    # Both adapter modes return equivalent rich quote responses.
    assert equity_response.tradable == equity
    assert option_response.tradable == option
    assert equity_response.current_price.mark == 100.5
    assert option_response.current_price.mark == 100.5

    # And
    # The fake service receives the same rich tradable request models.
    quote_requests = adapter_contract_harness.call_log.quote_requests
    assert quote_requests[0].tradable == equity
    assert quote_requests[1].tradable == option


def test_http_quote_adapter_surfaces_service_failures():
    # Given
    # A simulated deployed quote service that returns an HTTP failure.
    app = FastAPI()

    @app.get("/api/v1/{brokerage}/quotes/tradable/{symbol}")
    def _get_tradable_quote():
        raise HTTPException(status_code=503, detail="quote service unavailable")

    quote_adapter = HttpQuoteServiceAdapter(
        brokerage=Brokerage.ETRADE,
        quotes_base_url="http://quotes:8081",
        client=_TestClientAdapter(app, base_url="http://quotes:8081"),
    )

    # When / Then
    # The HTTP adapter converts transport failure into the expected adapter-level error.
    with pytest.raises(HttpServiceAdapterError) as exc_info:
        quote_adapter.get_tradable_quote(GetTradableRequest(tradable=Equity(ticker="GE")))

    # And
    # The original HTTP status and response body remain available for diagnostics.
    assert exc_info.value.status_code == 503
    assert "quote service unavailable" in exc_info.value.response_text


def _orders_app(order_service: OrderServicePort) -> FastAPI:
    app = FastAPI()

    @app.post("/api/v1/{brokerage}/accounts/{account_id}/orders/preview_and_place")
    def _preview_and_place_order(brokerage: str, preview_order_request: PreviewOrderRequest):
        assert Brokerage(brokerage) == Brokerage.ETRADE
        return order_service.preview_and_place_order(preview_order_request)

    @app.get("/api/v1/{brokerage}/accounts/{account_id}/orders/{order_id}")
    def _get_order(brokerage: str, account_id: str, order_id: str):
        assert Brokerage(brokerage) == Brokerage.ETRADE
        return order_service.get_order(GetOrderRequest(account_id=account_id, order_id=order_id))

    @app.put("/api/v1/{brokerage}/accounts/{account_id}/orders/{order_id}")
    def _modify_order(brokerage: str, preview_modify_order_request: PreviewModifyOrderRequest):
        assert Brokerage(brokerage) == Brokerage.ETRADE
        return order_service.modify_order(preview_modify_order_request)

    @app.delete("/api/v1/{brokerage}/accounts/{account_id}/orders/{order_id}")
    def _cancel_order(brokerage: str, account_id: str, order_id: str):
        assert Brokerage(brokerage) == Brokerage.ETRADE
        return order_service.cancel_order(CancelOrderRequest(account_id=account_id, order_id=order_id))

    return app


def _quotes_app(quote_service: QuoteServicePort) -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/{brokerage}/quotes/tradable/{symbol}")
    def _get_tradable_quote(brokerage: str, symbol: str):
        assert Brokerage(brokerage) == Brokerage.ETRADE
        return quote_service.get_tradable_quote(GetTradableRequest(tradable=_tradable_from_symbol(symbol)))

    return app


def _preview_order_request() -> PreviewOrderRequest:
    order = _order()
    return PreviewOrderRequest(
        order_metadata=OrderMetadata(
            order_type=order.get_order_type(),
            account_id=ACCOUNT_ID,
            client_order_id="client-1",
        ),
        order=order,
    )


def _preview_modify_order_request(order_id: str) -> PreviewModifyOrderRequest:
    order = _order()
    return PreviewModifyOrderRequest(
        order_metadata=OrderMetadata(
            order_type=order.get_order_type(),
            account_id=ACCOUNT_ID,
            client_order_id="client-2",
        ),
        order=order,
        order_id_to_modify=order_id,
    )


def _order() -> Order:
    return OrderTestUtil.build_spread_order()


def _place_order_response(order_id: str, order: Order) -> PlaceOrderResponse:
    return PlaceOrderResponse(
        order_metadata=OrderMetadata(
            order_type=order.get_order_type(),
            account_id=ACCOUNT_ID,
            client_order_id=f"client-{order_id}",
        ),
        preview_id=f"preview-{order_id}",
        order_id=order_id,
        order=order,
    )


def _get_order_response(order_id: str, status: OrderStatus) -> GetOrderResponse:
    placed_order_details = PlacedOrderDetails(
        account_id=ACCOUNT_ID,
        brokerage_order_id=order_id,
        status=status,
        order_placed_time=datetime(2026, 1, 1, 12, 0, 0),
        current_market_price=Price(bid=1.0, ask=1.2),
    )
    return GetOrderResponse(
        placed_order=PlacedOrder(order=_order(), placed_order_details=placed_order_details)
    )


def _tradable_from_symbol(symbol: str) -> Tradable:
    parsed = symbol.split(":")
    if len(parsed) == 1:
        return Equity(ticker=symbol)

    ticker, year, month, day, option_type, strike_price = parsed
    return Option(
        equity=Equity(ticker=ticker),
        type=OptionType(option_type),
        strike=Amount.from_float(float(strike_price)),
        expiry=date(year=int(year), month=int(month), day=int(day)),
    )
