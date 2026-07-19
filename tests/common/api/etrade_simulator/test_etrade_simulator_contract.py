import json
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urlsplit

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
from fianchetto_tradebot.common_models.api.request_status import RequestStatus
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.server.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.simulator.etrade import seed_data

SIM_BASE_URL = "http://etrade-sim:8090"
ACCOUNT_ID = seed_data.ACCOUNT_ID
EQUITY_SYMBOL = seed_data.EQUITY_SYMBOL
PREVIEW_ID = seed_data.PREVIEW_ID
ORDER_ID = seed_data.ORDER_ID


@dataclass
class _RecordedRequest:
    method: str
    path: str
    params: dict | None = None
    body: str | None = None


@dataclass
class _ContractResponse:
    body: dict
    status_code: int = HttpStatusCode.OK
    url: str = SIM_BASE_URL
    request: object = field(default_factory=lambda: type("_Request", (), {"headers": {}})())

    @property
    def text(self) -> str:
        return json.dumps(self.body)

    def json(self) -> dict:
        return self.body


class _SimulatorContractSession:
    def __init__(self):
        self.requests: list[_RecordedRequest] = []

    def get(self, url: str, params: dict | None = None):
        path = urlsplit(url).path
        self.requests.append(_RecordedRequest("GET", path, params=params))
        return _ContractResponse(_sync_response_for("GET", path, params))

    def post(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        path = urlsplit(url).path
        self.requests.append(_RecordedRequest("POST", path, body=data))
        return _ContractResponse(_sync_response_for("POST", path, None))

    def put(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        path = urlsplit(url).path
        self.requests.append(_RecordedRequest("PUT", path, body=data))
        return _ContractResponse(_sync_response_for("PUT", path, None))


class _SimulatorContractAsyncSession:
    def __init__(self):
        self.requests: list[_RecordedRequest] = []

    async def request(self, method: str, url: str, params: dict | None = None):
        path = urlsplit(url).path
        self.requests.append(_RecordedRequest(method, path, params=params))
        return _async_response_for(method, path, params)


class _SimulatorContractConnector:
    def __init__(self):
        self.session = _SimulatorContractSession()
        self.async_session = _SimulatorContractAsyncSession()

    def load_connection(self):
        return self.session, self.async_session, SIM_BASE_URL


def test_simulator_contract_supports_account_balance_and_portfolio_paths():
    # Given
    # Account and portfolio services using the simulator contract session.
    connector = _SimulatorContractConnector()
    account_service = ETradeAccountService(connector)
    portfolio_service = ETradePortfolioService(connector)

    # When
    # The services request account, balance, and portfolio data.
    accounts = account_service.list_accounts()
    balance = account_service.get_account_balance(GetAccountBalanceRequest(account_id=ACCOUNT_ID))
    portfolio = portfolio_service.get_portfolio_info(GetPortfolioRequest(account_id=ACCOUNT_ID))

    # Then
    # The simulator-shaped responses parse into useful domain objects.
    assert accounts.account_list[0].account_id_key == ACCOUNT_ID
    assert balance.account_balance.account_id == ACCOUNT_ID
    assert balance.account_balance.total_account_value == Amount.from_float(125000.25)
    assert portfolio.portfolio.equities[EQUITY_SYMBOL] == 100
    assert portfolio.portfolio.options[EQUITY_SYMBOL][date(2026, 1, 16)][Amount.from_float(25)][OptionType.PUT] == -1

    # And
    # The future simulator must support the exact routes and query params the services call.
    assert connector.session.requests[0] == _RecordedRequest("GET", "/v1/accounts/list.json", params=None)
    assert connector.session.requests[1] == _RecordedRequest(
        "GET",
        f"/v1/accounts/{ACCOUNT_ID}/balance.json",
        params={"instType": "BROKERAGE", "realTimeNAV": "true"},
    )
    assert connector.session.requests[2].path == f"/v1/accounts/{ACCOUNT_ID}/portfolio.json"
    assert connector.session.requests[2].params["view"] == "COMPLETE"


def test_simulator_contract_supports_quotes_expiries_and_option_chains():
    # Given
    # Quote service using both sync and async simulator contract sessions.
    connector = _SimulatorContractConnector()
    quote_service = ETradeQuotesService(connector)
    equity = Equity(ticker=EQUITY_SYMBOL)
    option = Option(
        equity=equity,
        type=OptionType.PUT,
        strike=Amount(whole=25, part=0, currency=Currency.US_DOLLARS),
        expiry=date(2026, 1, 16),
    )

    # When
    # The service asks for equity quotes, option quotes, expiries, and the full option chain.
    equity_quote = quote_service.get_tradable_quote(GetTradableRequest(tradable=equity))
    option_quote = quote_service.get_tradable_quote(GetTradableRequest(tradable=option))
    expiries = quote_service.get_option_expire_dates(GetOptionExpireDatesRequest(ticker=EQUITY_SYMBOL))
    chain = quote_service.get_options_chain(GetOptionsChainRequest(ticker=EQUITY_SYMBOL)).options_chain

    # Then
    # The simulator seed responses cover rich quote and chain data.
    assert equity_quote.current_price.mark == 100.5
    assert option_quote.greeks.delta == -0.4
    assert expiries.expire_dates == [date(2026, 1, 16), date(2026, 2, 20)]
    assert chain.expiry_strike_chain_call[date(2026, 1, 16)][Amount.from_float(25)].mark == 1.15
    assert chain.expiry_strike_chain_put[date(2026, 2, 20)][Amount.from_float(30)].mark == 3.25

    # And
    # The future simulator must support the same sync quote routes and async chain route.
    assert connector.session.requests[0].path == "/v1/market/quote/GE.json"
    assert connector.session.requests[1].path == "/v1/market/quote/GE:2026:1:16:PUT:25.0.json"
    assert connector.session.requests[2] == _RecordedRequest(
        "GET",
        "/v1/market/optionexpiredate.json",
        params={"symbol": EQUITY_SYMBOL},
    )
    assert connector.async_session.requests == [
        _RecordedRequest(
            "GET",
            "/v1/market/optionchains.json",
            params={"expiryYear": 2026, "expiryMonth": 1, "expiryDay": 16, "symbol": EQUITY_SYMBOL},
        ),
        _RecordedRequest(
            "GET",
            "/v1/market/optionchains.json",
            params={"expiryYear": 2026, "expiryMonth": 2, "expiryDay": 20, "symbol": EQUITY_SYMBOL},
        ),
    ]


def test_simulator_contract_supports_order_lifecycle_paths():
    # Given
    # Order service using the simulator contract session.
    connector = _SimulatorContractConnector()
    order_service = ETradeOrderService(connector)
    preview_request = _preview_order_request()

    # When
    # The service previews, places, reads, and cancels a demo order.
    preview = order_service.preview_order(preview_request)
    placed = order_service.place_order(
        PlaceOrderRequest(
            order_metadata=preview_request.order_metadata,
            preview_id=preview.preview_id,
            order=preview_request.order,
        )
    )
    fetched = order_service.get_order(GetOrderRequest(account_id=ACCOUNT_ID, order_id=placed.order_id))
    canceled = order_service.cancel_order(CancelOrderRequest(account_id=ACCOUNT_ID, order_id=placed.order_id))

    # Then
    # The simulator seed responses parse through the existing order lifecycle.
    assert preview.preview_id == PREVIEW_ID
    assert placed.order_id == ORDER_ID
    assert fetched.placed_order.placed_order_details.status == OrderStatus.OPEN
    assert canceled.order_id == ORDER_ID

    # And
    # The future simulator must support these order lifecycle routes.
    assert [request.path for request in connector.session.requests] == [
        f"/v1/accounts/{ACCOUNT_ID}/orders/preview.json",
        f"/v1/accounts/{ACCOUNT_ID}/orders/place.json",
        f"/v1/accounts/{ACCOUNT_ID}/orders/{ORDER_ID}.json",
        f"/v1/accounts/{ACCOUNT_ID}/orders/cancel.json",
    ]
    assert f"<orderId>{ORDER_ID}</orderId>" in connector.session.requests[-1].body


def test_simulator_contract_includes_retryable_order_preview_failure():
    # Given
    # A representative simulator error body for a retryable order-preview failure.
    response = _ContractResponse(seed_data.retryable_preview_error_response())

    # When
    # The existing E*Trade parser receives that response.
    parsed = ETradeOrderService._parse_preview_order_response(response, _order_metadata())

    # Then
    # The simulator contract preserves a meaningful retry signal for callers.
    assert parsed.request_status == RequestStatus.FAILURE_RETRY_SUGGESTED
    assert parsed.order_messages[0].code == "167"


def _preview_order_request() -> PreviewOrderRequest:
    return PreviewOrderRequest(order_metadata=_order_metadata(), order=_demo_order())


def _order_metadata() -> OrderMetadata:
    return OrderMetadata(
        order_type=OrderType.EQ,
        account_id=ACCOUNT_ID,
        client_order_id="client-1",
    )


def _demo_order() -> Order:
    return Order(
        expiry=GoodForDay(),
        order_lines=[
            OrderLine(
                tradable=Equity(ticker=EQUITY_SYMBOL),
                action=Action.BUY,
                quantity=1,
            )
        ],
        order_price=OrderPrice(
            order_price_type=OrderPriceType.LIMIT,
            price=Amount(whole=100, part=0, currency=Currency.US_DOLLARS),
        ),
    )


def _sync_response_for(method: str, path: str, params: dict | None) -> dict:
    routes = {
        ("GET", "/v1/accounts/list.json"): seed_data.account_list_response(),
        ("GET", f"/v1/accounts/{ACCOUNT_ID}/balance.json"): seed_data.balance_response(),
        ("GET", f"/v1/accounts/{ACCOUNT_ID}/portfolio.json"): seed_data.portfolio_response(),
        ("GET", "/v1/market/quote/GE.json"): seed_data.quote_response(EQUITY_SYMBOL),
        ("GET", "/v1/market/quote/GE:2026:1:16:PUT:25.0.json"): seed_data.quote_response(
            "GE:2026:1:16:PUT:25.0",
            include_greeks=True,
        ),
        ("GET", "/v1/market/optionexpiredate.json"): seed_data.option_expire_date_response(),
        ("POST", f"/v1/accounts/{ACCOUNT_ID}/orders/preview.json"): seed_data.preview_order_response(),
        ("POST", f"/v1/accounts/{ACCOUNT_ID}/orders/place.json"): seed_data.place_order_response(),
        ("GET", f"/v1/accounts/{ACCOUNT_ID}/orders/{ORDER_ID}.json"): seed_data.get_order_response(),
        ("PUT", f"/v1/accounts/{ACCOUNT_ID}/orders/cancel.json"): seed_data.cancel_order_response(),
    }
    try:
        return routes[(method, path)]
    except KeyError as exc:
        raise AssertionError(f"Simulator contract has no seed response for {method} {path} {params}") from exc


def _async_response_for(method: str, path: str, params: dict | None) -> dict:
    if method == "GET" and path == "/v1/market/optionchains.json":
        return seed_data.option_chain_response(
            year=int(params["expiryYear"]),
            month=int(params["expiryMonth"]),
            day=int(params["expiryDay"]),
        )
    raise AssertionError(f"Simulator contract has no async seed response for {method} {path} {params}")
