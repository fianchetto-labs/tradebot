from datetime import date

import pytest
from fastapi import FastAPI, HTTPException

from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.server.common.service.adapters import (
    HttpQuoteServiceAdapter,
    HttpServiceAdapterError,
)
from tests.fixtures.service_adapter_contract import ACCOUNT_ID
from tests.fixtures.service_adapter_contract import INITIAL_ORDER_ID
from tests.fixtures.service_adapter_contract import MODIFIED_ORDER_ID
from tests.fixtures.service_adapter_contract import AdapterContractHarness
from tests.fixtures.service_adapter_contract import FastApiTestClientAdapter
from tests.fixtures.service_adapter_contract import adapter_contract_harness
from tests.fixtures.service_adapter_contract import preview_modify_order_request
from tests.fixtures.service_adapter_contract import preview_order_request

pytestmark = [pytest.mark.functional, pytest.mark.contract]


def test_order_adapter_contract_preserves_order_lifecycle(
        adapter_contract_harness: AdapterContractHarness,
):
    # Given
    # A local or HTTP order adapter backed by the same fake order service.
    order_adapter = adapter_contract_harness.service_adapters.order_services[Brokerage.ETRADE]
    preview_request = preview_order_request()

    # When
    # The caller runs the order lifecycle through the adapter.
    place_response = order_adapter.preview_and_place_order(preview_request)
    get_response = order_adapter.get_order(GetOrderRequest(account_id=ACCOUNT_ID, order_id=place_response.order_id))
    modify_response = order_adapter.modify_order(preview_modify_order_request(place_response.order_id))
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
        client=FastApiTestClientAdapter(app, base_url="http://quotes:8081"),
    )

    # When / Then
    # The HTTP adapter converts transport failure into the expected adapter-level error.
    with pytest.raises(HttpServiceAdapterError) as exc_info:
        quote_adapter.get_tradable_quote(GetTradableRequest(tradable=Equity(ticker="GE")))

    # And
    # The original HTTP status and response body remain available for diagnostics.
    assert exc_info.value.status_code == 503
    assert "quote service unavailable" in exc_info.value.response_text
