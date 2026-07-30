from __future__ import annotations

import json
from dataclasses import dataclass, field
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
    url: str = SIM_BASE_URL
    request: object = field(default_factory=lambda: type("_Request", (), {"headers": {}})())

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
        return ContractResponse(_sync_response_for("POST", path, None))

    def put(self, url: str, header_auth: bool = False, headers: dict | None = None, data: str | None = None):
        path = urlsplit(url).path
        self.requests.append(RecordedRequest("PUT", path, body=data))
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
