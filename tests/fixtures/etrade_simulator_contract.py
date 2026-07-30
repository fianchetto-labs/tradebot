from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.simulator.etrade import seed_data

SIM_BASE_URL = "http://etrade-sim:8090"
ACCOUNT_ID = seed_data.ACCOUNT_ID
EQUITY_SYMBOL = seed_data.EQUITY_SYMBOL
PREVIEW_ID = seed_data.PREVIEW_ID
ORDER_ID = seed_data.ORDER_ID
BALANCE_PARAMS = {"instType": "BROKERAGE", "realTimeNAV": "true"}
PORTFOLIO_PARAMS = {
    "count": "1000",
    "sortBy": "DAYS_EXPIRATION",
    "sortOrder": "ASC",
    "view": "COMPLETE",
}
GET_ORDER_PARAMS = {"status": "OPEN"}
OPTION_EXPIRY_PARAMS = {"symbol": EQUITY_SYMBOL}


@dataclass
class RecordedRequest:
    method: str
    path: str
    params: dict | None = None
    body: str | None = None


@dataclass
class ContractResponse:
    body: dict
    status_code: int = HttpStatusCode.OK

    @property
    def text(self) -> str:
        return json.dumps(self.body)

    def json(self) -> dict:
        return self.body


class SimulatorContractSession:
    def __init__(self):
        self.requests: list[RecordedRequest] = []

    def get(self, url: str, params: dict | None = None):
        path = urlsplit(url).path
        self.requests.append(RecordedRequest("GET", path, params=params))
        return ContractResponse(_sync_response_for("GET", path, params))

    def post(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        path = urlsplit(url).path
        self.requests.append(RecordedRequest("POST", path, body=data))
        _assert_order_request("POST", path, header_auth, headers, data)
        return ContractResponse(_sync_response_for("POST", path, None))

    def put(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        path = urlsplit(url).path
        self.requests.append(RecordedRequest("PUT", path, body=data))
        _assert_order_request("PUT", path, header_auth, headers, data)
        return ContractResponse(_sync_response_for("PUT", path, None))


class SimulatorContractAsyncSession:
    def __init__(self):
        self.requests: list[RecordedRequest] = []

    async def request(self, method: str, url: str, params: dict | None = None):
        path = urlsplit(url).path
        self.requests.append(RecordedRequest(method, path, params=params))
        return _async_response_for(method, path, params)


class SimulatorContractConnector:
    def __init__(self):
        self.session = SimulatorContractSession()
        self.async_session = SimulatorContractAsyncSession()

    def load_connection(self):
        return self.session, self.async_session, SIM_BASE_URL


def demo_preview_order_request() -> PreviewOrderRequest:
    return PreviewOrderRequest(order_metadata=demo_order_metadata(), order=demo_order())


def demo_order_metadata() -> OrderMetadata:
    return OrderMetadata(
        order_type=OrderType.EQ,
        account_id=ACCOUNT_ID,
        client_order_id="client-1",
    )


def demo_order() -> Order:
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


def retryable_preview_error_response() -> ContractResponse:
    return ContractResponse(seed_data.retryable_preview_error_response())


def _sync_response_for(method: str, path: str, params: dict | None) -> dict:
    routes = {
        ("GET", "/v1/accounts/list.json"): (seed_data.account_list_response(), {}),
        ("GET", f"/v1/accounts/{ACCOUNT_ID}/balance.json"): (seed_data.balance_response(), BALANCE_PARAMS),
        ("GET", f"/v1/accounts/{ACCOUNT_ID}/portfolio.json"): (seed_data.portfolio_response(), PORTFOLIO_PARAMS),
        ("GET", "/v1/market/quote/GE.json"): (seed_data.quote_response(EQUITY_SYMBOL), {}),
        ("GET", "/v1/market/quote/GE:2026:1:16:PUT:25.0.json"): (
            seed_data.quote_response(
                "GE:2026:1:16:PUT:25.0",
                include_greeks=True,
            ),
            {},
        ),
        ("GET", "/v1/market/optionexpiredate.json"): (
            seed_data.option_expire_date_response(),
            OPTION_EXPIRY_PARAMS,
        ),
        ("POST", f"/v1/accounts/{ACCOUNT_ID}/orders/preview.json"): (seed_data.preview_order_response(), None),
        ("POST", f"/v1/accounts/{ACCOUNT_ID}/orders/place.json"): (seed_data.place_order_response(), None),
        ("GET", f"/v1/accounts/{ACCOUNT_ID}/orders/{ORDER_ID}.json"): (
            seed_data.get_order_response(),
            GET_ORDER_PARAMS,
        ),
        ("PUT", f"/v1/accounts/{ACCOUNT_ID}/orders/cancel.json"): (seed_data.cancel_order_response(), None),
    }
    try:
        response, expected_params = routes[(method, path)]
    except KeyError as exc:
        raise AssertionError(f"Simulator contract has no seed response for {method} {path} {params}") from exc
    _assert_params(method, path, params, expected_params)
    return response


def _async_response_for(method: str, path: str, params: dict | None) -> dict:
    if method == "GET" and path == "/v1/market/optionchains.json":
        _assert_option_chain_params(method, path, params)
        return seed_data.option_chain_response(
            year=int(params["expiryYear"]),
            month=int(params["expiryMonth"]),
            day=int(params["expiryDay"]),
        )
    raise AssertionError(f"Simulator contract has no async seed response for {method} {path} {params}")


def _assert_params(method: str, path: str, actual: dict | None, expected: dict | None) -> None:
    if actual != expected:
        raise AssertionError(f"Expected {method} {path} params {expected}, got {actual}")


def _assert_option_chain_params(method: str, path: str, params: dict | None) -> None:
    expected_keys = {"symbol", "expiryYear", "expiryMonth", "expiryDay"}
    if params is None:
        raise AssertionError(f"Expected {method} {path} params with keys {expected_keys}, got None")

    actual_keys = set(params)
    if actual_keys != expected_keys:
        raise AssertionError(f"Expected {method} {path} params keys {expected_keys}, got {actual_keys}")

    if params["symbol"] != EQUITY_SYMBOL:
        raise AssertionError(f"Expected {method} {path} symbol {EQUITY_SYMBOL}, got {params['symbol']}")


def _assert_order_request(
    method: str,
    path: str,
    header_auth: bool,
    headers: dict | None,
    body: str | None,
) -> None:
    if "/orders/" not in path:
        return

    expected_headers = {"Content-Type": "application/xml", "consumerKey": ACCOUNT_ID}
    if not header_auth:
        raise AssertionError(f"Expected {method} {path} to use header authentication")
    if headers != expected_headers:
        raise AssertionError(f"Expected {method} {path} headers {expected_headers}, got {headers}")
    if body is None:
        raise AssertionError(f"Expected {method} {path} XML body")

    if path.endswith("/orders/preview.json"):
        _assert_body_contains(method, path, body, "<PreviewOrderRequest>", "<clientOrderId>client-1</clientOrderId>")
    elif path.endswith("/orders/place.json"):
        _assert_body_contains(method, path, body, "<PlaceOrderRequest>", f"<previewId>{PREVIEW_ID}</previewId>")
    elif path.endswith("/orders/cancel.json"):
        _assert_body_contains(method, path, body, "<CancelOrderRequest>", f"<orderId>{ORDER_ID}</orderId>")


def _assert_body_contains(method: str, path: str, body: str, *snippets: str) -> None:
    missing = [snippet for snippet in snippets if snippet not in body]
    if missing:
        raise AssertionError(f"Expected {method} {path} body to contain {missing}")
