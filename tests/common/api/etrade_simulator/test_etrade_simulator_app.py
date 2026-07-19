from datetime import date
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from fianchetto_tradebot.common_models.api.account.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common_models.api.quotes.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.server.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.simulator.etrade import seed_data
from fianchetto_tradebot.server.simulator.etrade.etrade_simulator_app import create_app

SIM_BASE_URL = "http://testserver"


class _TestClientSession:
    def __init__(self, client: TestClient):
        self.client = client

    def get(self, url: str, params: dict | None = None):
        return self.client.get(_path(url), params=params)

    def post(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        return self.client.post(_path(url), headers=headers, content=data)

    def put(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        return self.client.put(_path(url), headers=headers, content=data)


class _AsyncTestClientSession:
    def __init__(self, client: TestClient):
        self.client = client

    async def request(self, method: str, url: str, params: dict | None = None):
        response = self.client.request(method, _path(url), params=params)
        return response.json()


class _SimulatorConnector:
    def __init__(self, client: TestClient):
        self.session = _TestClientSession(client)
        self.async_session = _AsyncTestClientSession(client)

    def load_connection(self):
        return self.session, self.async_session, SIM_BASE_URL


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
    # Existing E*Trade services pointed at the simulator app through HTTP-shaped calls.
    client = TestClient(create_app())
    connector = _SimulatorConnector(client)
    account_service = ETradeAccountService(connector)
    portfolio_service = ETradePortfolioService(connector)
    quote_service = ETradeQuotesService(connector)
    order_service = ETradeOrderService(connector)

    # When
    # The real service classes execute representative simulator-backed flows.
    account_balance = account_service.get_account_balance(GetAccountBalanceRequest(account_id=seed_data.ACCOUNT_ID))
    portfolio = portfolio_service.get_portfolio_info(GetPortfolioRequest(account_id=seed_data.ACCOUNT_ID))
    equity_quote = quote_service.get_tradable_quote(GetTradableRequest(tradable=Equity(ticker=seed_data.EQUITY_SYMBOL)))
    option_chain = quote_service.get_options_chain(GetOptionsChainRequest(ticker=seed_data.EQUITY_SYMBOL)).options_chain
    preview_order_request = _preview_order_request()
    preview = order_service.preview_order(preview_order_request)
    placed = order_service.place_order(
        PlaceOrderRequest(
            order_metadata=preview_order_request.order_metadata,
            preview_id=preview.preview_id,
            order=preview_order_request.order,
        )
    )
    fetched = order_service.get_order(GetOrderRequest(account_id=seed_data.ACCOUNT_ID, order_id=placed.order_id))
    canceled = order_service.cancel_order(CancelOrderRequest(account_id=seed_data.ACCOUNT_ID, order_id=placed.order_id))

    # Then
    # The simulator satisfies the documented contract from behind an actual FastAPI boundary.
    assert account_balance.account_balance.total_account_value == Amount.from_float(125000.25)
    assert portfolio.portfolio.equities[seed_data.EQUITY_SYMBOL] == 100
    assert equity_quote.current_price.mark == 100.5
    assert option_chain.expiry_strike_chain_put[date(2026, 2, 20)][Amount.from_float(30)].mark == 3.25
    assert preview.preview_id == seed_data.PREVIEW_ID
    assert placed.order_id == seed_data.ORDER_ID
    assert fetched.placed_order.placed_order_details.status == OrderStatus.OPEN
    assert canceled.order_id == seed_data.ORDER_ID


def _preview_order_request() -> PreviewOrderRequest:
    return PreviewOrderRequest(
        order_metadata=OrderMetadata(
            order_type=OrderType.EQ,
            account_id=seed_data.ACCOUNT_ID,
            client_order_id="client-1",
        ),
        order=Order(
            expiry=GoodForDay(),
            order_lines=[
                OrderLine(
                    tradable=Equity(ticker=seed_data.EQUITY_SYMBOL),
                    action=Action.BUY,
                    quantity=1,
                )
            ],
            order_price=OrderPrice(
                order_price_type=OrderPriceType.LIMIT,
                price=Amount(whole=100, part=0, currency=Currency.US_DOLLARS),
            ),
        ),
    )


def _path(url: str) -> str:
    return urlsplit(url).path
