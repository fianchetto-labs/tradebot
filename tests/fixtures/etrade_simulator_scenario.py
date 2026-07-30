from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from fianchetto_tradebot.common_models.api.account.get_account_balance_response import GetAccountBalanceResponse
from fianchetto_tradebot.common_models.api.account.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_response import PreviewOrderResponse
from fianchetto_tradebot.common_models.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common_models.api.portfolio.get_portfolio_response import GetPortfolioResponse
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
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
from fianchetto_tradebot.server.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.simulator.etrade import seed_data
from fianchetto_tradebot.server.simulator.etrade.etrade_simulator_app import create_app

SIM_BASE_URL = "http://testserver"


@dataclass(frozen=True)
class ETradeSimulatorWorkflowResult:
    account_balance: GetAccountBalanceResponse
    portfolio: GetPortfolioResponse
    equity_quote: GetTradableResponse
    option_chain: GetOptionsChainResponse
    preview: PreviewOrderResponse
    placed: PlaceOrderResponse
    fetched: GetOrderResponse
    canceled: CancelOrderResponse


@dataclass(frozen=True)
class ETradeSimulatorScenario:
    client: TestClient
    connector: InProcessETradeConnector
    account_service: ETradeAccountService
    portfolio_service: ETradePortfolioService
    quote_service: ETradeQuotesService
    order_service: ETradeOrderService

    @classmethod
    def create(cls) -> ETradeSimulatorScenario:
        client = TestClient(create_app())
        connector = InProcessETradeConnector(client)
        return cls(
            client=client,
            connector=connector,
            account_service=ETradeAccountService(connector),
            portfolio_service=ETradePortfolioService(connector),
            quote_service=ETradeQuotesService(connector),
            order_service=ETradeOrderService(connector),
        )

    def run_representative_service_workflow(self) -> ETradeSimulatorWorkflowResult:
        preview_order_request = self.preview_order_request()
        preview = self.order_service.preview_order(preview_order_request)
        placed = self.order_service.place_order(
            PlaceOrderRequest(
                order_metadata=preview_order_request.order_metadata,
                preview_id=preview.preview_id,
                order=preview_order_request.order,
            )
        )

        return ETradeSimulatorWorkflowResult(
            account_balance=self.account_service.get_account_balance(
                GetAccountBalanceRequest(account_id=seed_data.ACCOUNT_ID)
            ),
            portfolio=self.portfolio_service.get_portfolio_info(
                GetPortfolioRequest(account_id=seed_data.ACCOUNT_ID)
            ),
            equity_quote=self.quote_service.get_tradable_quote(
                GetTradableRequest(tradable=Equity(ticker=seed_data.EQUITY_SYMBOL))
            ),
            option_chain=self.quote_service.get_options_chain(
                GetOptionsChainRequest(ticker=seed_data.EQUITY_SYMBOL)
            ),
            preview=preview,
            placed=placed,
            fetched=self.order_service.get_order(
                GetOrderRequest(account_id=seed_data.ACCOUNT_ID, order_id=placed.order_id)
            ),
            canceled=self.order_service.cancel_order(
                CancelOrderRequest(account_id=seed_data.ACCOUNT_ID, order_id=placed.order_id)
            ),
        )

    def preview_order_request(self) -> PreviewOrderRequest:
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


class InProcessETradeConnector:
    def __init__(self, client: TestClient, base_url: str = SIM_BASE_URL):
        self.session = _TestClientSession(client)
        self.async_session = _AsyncTestClientSession(client)
        self.base_url = base_url

    def load_connection(self):
        return self.session, self.async_session, self.base_url


class _TestClientSession:
    def __init__(self, client: TestClient):
        self.client = client

    def get(self, url: str, params: dict | None = None):
        return self.client.get(_test_client_url(url), params=params)

    def post(
        self,
        url: str,
        header_auth: bool = False,
        headers: dict | None = None,
        data: str | None = None,
    ):
        return self.client.post(_test_client_url(url), headers=headers, content=data)

    def put(
        self,
        url: str,
        header_auth: bool = False,
        headers: dict | None = None,
        data: str | None = None,
    ):
        return self.client.put(_test_client_url(url), headers=headers, content=data)


class _AsyncTestClientSession:
    def __init__(self, client: TestClient):
        self.client = client

    async def request(self, method: str, url: str, params: dict | None = None):
        response = self.client.request(method, _test_client_url(url), params=params)
        return response.json()


def _test_client_url(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path or "/"
    if parsed.query:
        return f"{path}?{parsed.query}"
    return path
