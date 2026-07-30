from datetime import date

import pytest

from fianchetto_tradebot.common_models.api.account.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest
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
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from tests.fixtures.etrade_simulator_contract import ACCOUNT_ID
from tests.fixtures.etrade_simulator_contract import EQUITY_SYMBOL
from tests.fixtures.etrade_simulator_contract import ORDER_ID
from tests.fixtures.etrade_simulator_contract import PREVIEW_ID
from tests.fixtures.etrade_simulator_contract import RecordedRequest
from tests.fixtures.etrade_simulator_contract import SimulatorContractConnector
from tests.fixtures.etrade_simulator_contract import demo_order_metadata
from tests.fixtures.etrade_simulator_contract import demo_preview_order_request
from tests.fixtures.etrade_simulator_contract import retryable_preview_error_response

pytestmark = [pytest.mark.functional, pytest.mark.contract]


def test_simulator_contract_supports_account_balance_and_portfolio_paths():
    # Given
    # Account and portfolio services using the simulator contract session.
    connector = SimulatorContractConnector()
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
    assert connector.session.requests[0] == RecordedRequest("GET", "/v1/accounts/list.json", params=None)
    assert connector.session.requests[1] == RecordedRequest(
        "GET",
        f"/v1/accounts/{ACCOUNT_ID}/balance.json",
        params={"instType": "BROKERAGE", "realTimeNAV": "true"},
    )
    assert connector.session.requests[2].path == f"/v1/accounts/{ACCOUNT_ID}/portfolio.json"
    assert connector.session.requests[2].params["view"] == "COMPLETE"


def test_simulator_contract_supports_quotes_expiries_and_option_chains():
    # Given
    # Quote service using both sync and async simulator contract sessions.
    connector = SimulatorContractConnector()
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
    assert connector.session.requests[2] == RecordedRequest(
        "GET",
        "/v1/market/optionexpiredate.json",
        params={"symbol": EQUITY_SYMBOL},
    )
    assert connector.async_session.requests == [
        RecordedRequest(
            "GET",
            "/v1/market/optionchains.json",
            params={"expiryYear": 2026, "expiryMonth": 1, "expiryDay": 16, "symbol": EQUITY_SYMBOL},
        ),
        RecordedRequest(
            "GET",
            "/v1/market/optionchains.json",
            params={"expiryYear": 2026, "expiryMonth": 2, "expiryDay": 20, "symbol": EQUITY_SYMBOL},
        ),
    ]


def test_simulator_contract_supports_order_lifecycle_paths():
    # Given
    # Order service using the simulator contract session.
    connector = SimulatorContractConnector()
    order_service = ETradeOrderService(connector)
    preview_request = demo_preview_order_request()

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
    response = retryable_preview_error_response()

    # When
    # The existing E*Trade parser receives that response.
    parsed = ETradeOrderService._parse_preview_order_response(response, demo_order_metadata())

    # Then
    # The simulator contract preserves a meaningful retry signal for callers.
    assert parsed.request_status == RequestStatus.FAILURE_RETRY_SUGGESTED
    assert parsed.order_messages[0].code == "167"
