from datetime import date

import pytest
from fastapi.testclient import TestClient

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.simulator.etrade import seed_data
from fianchetto_tradebot.server.simulator.etrade.etrade_simulator_app import create_app
from tests.functional.etrade_simulator_scenario import ETradeSimulatorScenario

pytestmark = pytest.mark.functional


def test_etrade_simulator_exposes_health_and_seed_routes():
    # Given
    # A simulator app running in-process.
    client = TestClient(create_app())

    # When / Then
    # The first seed routes are reachable without credentials.
    assert client.get("/health-check").json() == "E*Trade Simulator Up"
    assert client.get("/v1/accounts/list.json").json()["AccountListResponse"]
    assert client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/balance.json").json()["BalanceResponse"]
    assert client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/portfolio.json").json()["PortfolioResponse"]
    assert client.get(f"/v1/market/quote/{seed_data.EQUITY_SYMBOL}.json").json()["QuoteResponse"]
    assert client.get("/v1/market/optionexpiredate.json", params={"symbol": seed_data.EQUITY_SYMBOL}).json()[
        "OptionExpireDateResponse"
    ]
    assert client.get(
        "/v1/market/optionchains.json",
        params={"symbol": seed_data.EQUITY_SYMBOL, "expiryYear": 2026, "expiryMonth": 1, "expiryDay": 16},
    ).json()["OptionChainResponse"]


def test_etrade_simulator_rejects_unknown_accounts_and_symbols():
    # Given
    # A simulator app with only deterministic seed data.
    client = TestClient(create_app())

    # When / Then
    # Unsupported account and symbol values fail loudly instead of returning misleading seed data.
    assert client.get("/v1/accounts/nope/balance.json").status_code == HttpStatusCode.NOT_FOUND
    assert client.get("/v1/market/quote/MSFT.json").status_code == HttpStatusCode.NOT_FOUND
    assert (
        client.get("/v1/market/optionexpiredate.json", params={"symbol": "MSFT"}).status_code
        == HttpStatusCode.NOT_FOUND
    )


def test_etrade_simulator_supports_order_state_lifecycle():
    # Given
    # A simulator app with in-memory order state.
    client = TestClient(create_app())

    # When
    # A caller places, reads, cancels, and reads the seed order.
    preview = client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/preview.json")
    placed = client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")
    open_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")
    canceled = client.put(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/cancel.json")
    canceled_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # Then
    # The simulator returns the documented ids and reflects cancellation in later reads.
    assert preview.json()["PreviewOrderResponse"]["PreviewIds"][0]["previewId"] == seed_data.PREVIEW_ID
    assert placed.json()["PlaceOrderResponse"]["OrderIds"][0]["orderId"] == seed_data.ORDER_ID
    assert open_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == "OPEN"
    assert canceled.json()["CancelOrderResponse"]["orderId"] == seed_data.ORDER_ID
    assert canceled_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == "CANCELLED"


def test_etrade_simulator_exposes_retryable_preview_error_scenario():
    # Given
    # A simulator app with the documented retryable failure seed response.
    client = TestClient(create_app())

    # When
    # A caller opts into the retryable preview-error scenario.
    response = client.post(
        f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/preview.json",
        params={"scenario": "retryable-preview-error"},
    )

    # Then
    # The route returns the same error shape used by the executable contract.
    assert response.json() == seed_data.retryable_preview_error_response()
    assert client.post(
        f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/preview.json",
        params={"scenario": "does-not-exist"},
    ).status_code == HttpStatusCode.BAD_REQUEST


def test_existing_etrade_services_parse_simulator_http_responses():
    # Given
    # Existing E*Trade services pointed at an in-process simulator through HTTP-shaped calls.
    scenario = ETradeSimulatorScenario.create()

    # When
    # The real service classes execute representative simulator-backed flows.
    result = scenario.run_representative_service_workflow()

    # Then
    # The simulator satisfies the documented contract from behind an actual FastAPI boundary.
    assert result.account_balance.account_balance.total_account_value == Amount.from_float(125000.25)
    assert result.portfolio.portfolio.equities[seed_data.EQUITY_SYMBOL] == 100
    assert result.equity_quote.current_price.mark == 100.5
    assert result.option_chain.options_chain.expiry_strike_chain_put[date(2026, 2, 20)][
        Amount.from_float(30)
    ].mark == 3.25
    assert result.preview.preview_id == seed_data.PREVIEW_ID
    assert result.placed.order_id == seed_data.ORDER_ID
    assert result.fetched.placed_order.placed_order_details.status == OrderStatus.OPEN
    assert result.canceled.order_id == seed_data.ORDER_ID


def test_etrade_simulator_scenario_connector_preserves_query_strings():
    # Given
    # A service-compatible connector that points at the in-process simulator.
    scenario = ETradeSimulatorScenario.create()
    session, _, base_url = scenario.connector.load_connection()

    # When
    # A caller embeds query parameters in the URL instead of passing them separately.
    response = session.get(f"{base_url}/v1/market/optionexpiredate.json?symbol={seed_data.EQUITY_SYMBOL}")

    # Then
    # The harness forwards the query string the way a real HTTP client would.
    assert response.status_code == HttpStatusCode.OK
    assert response.json()["OptionExpireDateResponse"]
