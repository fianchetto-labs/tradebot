from datetime import date

import pytest
from fastapi.testclient import TestClient

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.simulator.etrade import seed_data
from fianchetto_tradebot.server.simulator.etrade.etrade_simulator_app import OrderLifecycleScenario
from fianchetto_tradebot.server.simulator.etrade.etrade_simulator_app import create_app
from tests.fixtures.etrade_simulator_scenario import ETradeSimulatorScenario

pytestmark = pytest.mark.functional


def _cancel_order_xml(order_id: str) -> str:
    return f"""
        <CancelOrderRequest>
          <orderId>{order_id}</orderId>
        </CancelOrderRequest>"""


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
    canceled = client.put(
        f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/cancel.json",
        content=_cancel_order_xml(seed_data.ORDER_ID),
    )
    canceled_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # Then
    # The simulator returns the documented ids and reflects cancellation in later reads.
    assert preview.json()["PreviewOrderResponse"]["PreviewIds"][0]["previewId"] == seed_data.PREVIEW_ID
    assert placed.json()["PlaceOrderResponse"]["OrderIds"][0]["orderId"] == seed_data.ORDER_ID
    assert open_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == "OPEN"
    assert canceled.json()["CancelOrderResponse"]["orderId"] == seed_data.ORDER_ID
    assert canceled_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == "CANCELLED"


@pytest.mark.parametrize(
    ("scenario", "expected_statuses"),
    [
        (OrderLifecycleScenario.OPEN, [OrderStatus.OPEN, OrderStatus.OPEN]),
        (OrderLifecycleScenario.EVENTUALLY_EXECUTED, [OrderStatus.OPEN, OrderStatus.EXECUTED]),
        (OrderLifecycleScenario.BROKER_CANCELLED, [OrderStatus.OPEN, OrderStatus.CANCELLED]),
        (OrderLifecycleScenario.REJECTED, [OrderStatus.REJECTED, OrderStatus.REJECTED]),
    ],
)
def test_etrade_simulator_order_lifecycle_scenarios_progress_by_read(scenario, expected_statuses):
    # Given
    # A simulator app with an explicit order lifecycle scenario selected.
    client = TestClient(create_app())
    scenario_response = client.post("/_simulator/order-lifecycle-scenario", json={"scenario": scenario.value})
    client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")

    # When
    # The caller polls the placed order.
    observed_statuses = [
        client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json").json()[
            "OrdersResponse"
        ]["Order"][0]["OrderDetail"][0]["status"]
        for _ in expected_statuses
    ]

    # Then
    # The scenario deterministically drives the brokerage-like order status.
    assert scenario_response.status_code == HttpStatusCode.OK
    assert scenario_response.json() == {"scenario": scenario.value}
    assert observed_statuses == [status.value for status in expected_statuses]


def test_etrade_simulator_order_lifecycle_progresses_across_replacement_orders():
    # Given
    # A simulator scenario selected before an order is cancelled and replaced.
    client = TestClient(create_app())
    client.post(
        "/_simulator/order-lifecycle-scenario",
        json={"scenario": OrderLifecycleScenario.EVENTUALLY_EXECUTED.value},
    )
    first_placed = client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")
    first_order_id = first_placed.json()["PlaceOrderResponse"]["OrderIds"][0]["orderId"]
    first_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{first_order_id}.json")
    client.put(
        f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/cancel.json",
        content=_cancel_order_xml(first_order_id),
    )

    # When
    # A replacement order is placed and read.
    second_placed = client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")
    second_order_id = second_placed.json()["PlaceOrderResponse"]["OrderIds"][0]["orderId"]
    second_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{second_order_id}.json")

    # Then
    # The simulator scenario can drive the replacement lifecycle a MOEX worker observes.
    assert first_order_id == seed_data.ORDER_ID
    assert second_order_id == "order-2"
    assert first_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.OPEN.value
    executed_order_detail = second_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]
    assert executed_order_detail["status"] == OrderStatus.EXECUTED.value
    assert executed_order_detail["orderValue"] == 100.00
    assert executed_order_detail["executedTime"] == 1767360660000


def test_etrade_simulator_reset_restores_open_order_scenario_and_seed_routes():
    # Given
    # A simulator app after a terminal scenario has advanced.
    client = TestClient(create_app())
    client.post(
        "/_simulator/order-lifecycle-scenario",
        json={"scenario": OrderLifecycleScenario.EVENTUALLY_EXECUTED.value},
    )
    client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")
    client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")
    executed_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # When
    # The simulator state is reset and a new seed order is placed.
    reset_response = client.post("/_simulator/reset")
    client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")
    reset_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # Then
    # The scenario returns to the default OPEN behavior without disturbing seed data routes.
    assert executed_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.EXECUTED.value
    assert reset_response.status_code == HttpStatusCode.OK
    assert reset_response.json() == {"scenario": OrderLifecycleScenario.OPEN.value}
    assert reset_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.OPEN.value
    assert client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/balance.json").json()["BalanceResponse"]


def test_etrade_simulator_rejects_unknown_order_lifecycle_scenario():
    # Given
    # A simulator app with a strict scenario control surface.
    client = TestClient(create_app())

    # When
    # A caller requests an unsupported simulator scenario.
    response = client.post("/_simulator/order-lifecycle-scenario", json={"scenario": "fills-by-moonlight"})

    # Then
    # The simulator fails clearly with the project's explicit bad-request status.
    assert response.status_code == HttpStatusCode.BAD_REQUEST
    assert "Supported scenarios" in response.json()["detail"]


def test_etrade_simulator_explicit_cancel_wins_over_scenario_progression():
    # Given
    # A simulator app whose selected scenario would otherwise execute on the second read.
    client = TestClient(create_app())
    client.post(
        "/_simulator/order-lifecycle-scenario",
        json={"scenario": OrderLifecycleScenario.EVENTUALLY_EXECUTED.value},
    )
    client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")

    # When
    # The caller actively cancels before polling the order through scenario progression.
    client.put(
        f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/cancel.json",
        content=_cancel_order_xml(seed_data.ORDER_ID),
    )
    first_read = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")
    second_read = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # Then
    # The explicit cancellation remains the observed brokerage order state.
    assert first_read.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.CANCELLED.value
    assert second_read.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.CANCELLED.value


def test_etrade_simulator_terminal_order_status_survives_later_commands():
    # Given
    # A simulator order that has already reached a terminal brokerage status.
    client = TestClient(create_app())
    client.post(
        "/_simulator/order-lifecycle-scenario",
        json={"scenario": OrderLifecycleScenario.EVENTUALLY_EXECUTED.value},
    )
    client.post(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/place.json")
    client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")
    executed_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # When
    # Later simulator controls or cancel commands try to move it elsewhere.
    client.post("/_simulator/order-lifecycle-scenario", json={"scenario": OrderLifecycleScenario.OPEN.value})
    client.put(
        f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/cancel.json",
        content=_cancel_order_xml(seed_data.ORDER_ID),
    )
    final_order = client.get(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/{seed_data.ORDER_ID}.json")

    # Then
    # The terminal brokerage status remains terminal until simulator reset.
    assert executed_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.EXECUTED.value
    assert final_order.json()["OrdersResponse"]["Order"][0]["OrderDetail"][0]["status"] == OrderStatus.EXECUTED.value


def test_etrade_simulator_cancel_requires_order_id_xml_body():
    # Given
    # A simulator app with strict enough request validation to catch adapter regressions.
    client = TestClient(create_app())

    # When
    # A caller attempts to cancel without the XML body the real E*Trade service sends.
    response = client.put(f"/v1/accounts/{seed_data.ACCOUNT_ID}/orders/cancel.json")

    # Then
    # The simulator fails loudly instead of cancelling an unrelated seed order.
    assert response.status_code == HttpStatusCode.BAD_REQUEST
    assert "CancelOrderRequest XML body is required" in response.json()["detail"]


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
