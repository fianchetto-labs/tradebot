import datetime
import math
from collections import Counter
from functools import reduce
from unittest.mock import patch, MagicMock

import pytest
from rauth import OAuth1Session

from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.finance.tradable import Tradable
from fianchetto_tradebot.common_models.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.tradable_type import TradableType
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector, DEFAULT_ETRADE_BASE_URL_FILE
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.server.orders.tactics.incremental_price_delta_execution_tactic import \
    IncrementalPriceDeltaExecutionTactic
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from oex.test_get_market_price import quote_service

ORDER_PRICE_EXACTLY_200 = Amount(whole=200, part=0)
ORDER_PRICE_EXACTLY_100: Amount = Amount(whole=100, part=0)

MARKET_PRICE_NEAR_225 = Price(bid=224.95, ask=225.05)

THIRTY_CENTS: Price = Price(bid=.28, ask=.32)

SIXTY_CENTS_AMT: Amount = Amount(whole=0, part=60)
EXACTLY_SIXTY_CENTS: Amount = Amount(whole=0, part=60)

CREDIT_SIXTY_CENTS = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=SIXTY_CENTS_AMT)
DEBIT_SIXTY_CENTS = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=EXACTLY_SIXTY_CENTS)

NINETY_CENTS_MARKET_PRICE: Price = Price(bid=-.85, ask=-.95)

option_expiry: datetime.date = datetime.datetime(2025, 1, 31).date()
prev_week_option_expiry = option_expiry - datetime.timedelta(weeks=1)

t1_strike = Amount(whole=200, part=0, currency=Currency.US_DOLLARS)
t2_strike = Amount(whole=190, part=0, currency=Currency.US_DOLLARS)
t3_strike = Amount(whole=240, part=0, currency=Currency.US_DOLLARS)
t4_strike = Amount(whole=250, part=0, currency=Currency.US_DOLLARS)

equity = Equity(ticker="GE")
tradable0: Option = Option(equity=equity, type=OptionType.PUT,
                           strike=t1_strike, expiry=prev_week_option_expiry)
tradable1: Option = Option(equity=equity, type=OptionType.PUT,
                               strike=t1_strike, expiry=option_expiry)
tradable2: Option = Option(equity=equity, type=OptionType.PUT,
                               strike=t2_strike, expiry=option_expiry)
tradable3: Option = Option(equity=equity, type=OptionType.CALL,
                               strike=t3_strike, expiry=option_expiry)
tradable4: Option = Option(equity=equity, type=OptionType.CALL,
                               strike=t4_strike, expiry=option_expiry)


tradable_to_market_price_lookup: dict[Tradable, Price] = dict()
tradable_to_get_tradable_response_lookup: dict[Tradable, GetTradableResponse] = dict()
def initialize_lookups():
    t1_price_cents = 215
    t0_price = Price(bid=.12, ask=0.15)

    t1_price = Price(bid=2.12, ask=2.21)

    t2_price = Price(bid=1.10, ask=1.18)

    t3_price = Price(bid=2.17, ask=2.24)

    t4_price = Price(bid=1.17, ask=1.24)

    tradable_to_market_price_lookup[equity] = MARKET_PRICE_NEAR_225
    tradable_to_get_tradable_response_lookup[equity] = GetTradableResponse(tradable=equity, current_price=MARKET_PRICE_NEAR_225, volume=50000)

    tradable_to_get_tradable_response_lookup[tradable0] = GetTradableResponse(tradable=tradable0, current_price=t0_price, volume=5)
    tradable_to_market_price_lookup[tradable0] = t0_price

    tradable_to_get_tradable_response_lookup[tradable1] = GetTradableResponse(tradable=tradable1, current_price=t1_price, volume=5)
    tradable_to_market_price_lookup[tradable1] = t1_price

    tradable_to_get_tradable_response_lookup[tradable2] = GetTradableResponse(tradable=tradable2, current_price=t2_price, volume=5)
    tradable_to_market_price_lookup[tradable2] = t2_price

    tradable_to_get_tradable_response_lookup[tradable3] = GetTradableResponse(tradable=tradable3, current_price=t3_price, volume=5)
    tradable_to_market_price_lookup[tradable3] = t3_price

    tradable_to_get_tradable_response_lookup[tradable4] = GetTradableResponse(tradable=tradable4, current_price=t4_price, volume=5)
    tradable_to_market_price_lookup[tradable4] = t4_price

initialize_lookups()

class TradeSetup:
    def __init__(self, market_price_lookup:dict[Tradable, Price], tradable_quantities:dict[Tradable, int]):

        self.market_price_lookup: dict[Tradable, Price] = market_price_lookup
        self.tradable_quantities: dict[Tradable, int] = tradable_quantities
        self._validate_tradable_quantities()

        self.order_lines = self.to_order_lines()
        self.market_price = self.get_market_price()

    def _validate_tradable_quantities(self):
        # make sure only one equity is present
        num_equity_tradables: dict[TradableType, int] = Counter(map(lambda t: t.get_type() , self.tradable_quantities.keys()))
        if num_equity_tradables[TradableType.Equity] > 1:
            raise Exception("cannot have two equities in a trade")
        get_ticker = lambda t: t.ticker if t.type == TradableType.Equity else t.equity.ticker

        ticker_counts = Counter(map(get_ticker, self.tradable_quantities.keys()))

        if len(ticker_counts) > 1:
            raise Exception("Only one ticker symbol per tradeset allowed")

    def to_order_lines(self)->list[OrderLine]:
        order_lines: list[OrderLine] = list[OrderLine]()
        for tradable, quantity in self.tradable_quantities.items():
            if tradable.get_type() == TradableType.Equity:
                if quantity > 0:
                    # TODO - see if we can get away with consolidating to Action.BUY_OPEN
                    action = Action.BUY
                else:
                    action = Action.SELL
            elif tradable.get_type() == TradableType.Option:
                if quantity > 0:
                    action = Action.BUY_OPEN
                else:
                    action = Action.SELL
            order_lines.append(OrderLine(tradable=tradable, action=action, quantity=abs(quantity)))

        return order_lines

    def get_market_price(self)->Price:
        running_price = Price(bid=0, ask=0)
        quantities: set[int] = set(self.tradable_quantities.values())
        gcd = reduce(math.gcd, quantities)

        for tradable, quantity in self.tradable_quantities.items():
            # Figure how to handle equities, especially in non-block-sizes
            if quantity > 0:
                running_price -= self.market_price_lookup[tradable] * quantity
            else:
                running_price += self.market_price_lookup[tradable] * abs(quantity)
        return running_price / gcd


@pytest.fixture
@patch('rauth.OAuth1Session')
def connector(session: OAuth1Session):
    # build a connector that gives back a mock session
    connector: ETradeConnector = ETradeConnector()
    connector.load_connection = MagicMock(return_value=(session, DEFAULT_ETRADE_BASE_URL_FILE))
    return connector

@pytest.fixture
def order_service(connector):
    # TODO: Set up the service that will provide mock responses to given requests
    return ETradeOrderService(connector)

@pytest.fixture
def quotes_service(connector):
    return ETradeQuotesService(connector)

def test_credit_spread_order_more_than_market(quote_service):
    # Mock out quotes
    tradable_to_quantity_map: dict[Tradable, int] = dict[Tradable, int]()

    tradable_to_quantity_map[tradable1] = -1
    tradable_to_quantity_map[tradable2] = 1

    ts: TradeSetup = TradeSetup(market_price_lookup=tradable_to_market_price_lookup, tradable_quantities=tradable_to_quantity_map)

    # Adjust the order price based on the market price
    if ts.market_price.mark >= 0:
        # then we want to get more cash
        initial_offer_price = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount.from_float(2 * ts.market_price.ask))
    else:
        initial_offer_price = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount.from_float(0))

    o: Order = Order(expiry=GoodUntilCancelled(), order_lines=ts.to_order_lines(), order_price=initial_offer_price)

    quote_service.get_tradable_quote = lookup_market_values

    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(o, quote_service)

    assert new_price.order_price_type == OrderPriceType.NET_CREDIT
    assert new_price.price == Amount(whole=1, part=82)

def test_debit_spread_order_less_than_market(quote_service):
    # Mock out quotes
    tradable_to_quantity_map: dict[Tradable, int] = dict[Tradable, int]()

    tradable_to_quantity_map[tradable1] = 1
    tradable_to_quantity_map[tradable2] = -1

    ts: TradeSetup = TradeSetup(market_price_lookup=tradable_to_market_price_lookup, tradable_quantities=tradable_to_quantity_map)

    # Adjust the order price based on the market price
    if ts.market_price.mark >= 0:
        # then we want to get more cash
        initial_offer_price = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount.from_float(2 * ts.market_price.ask))
    else:
        initial_offer_price = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount.from_float(0))

    o: Order = Order(expiry=GoodUntilCancelled(), order_lines=ts.to_order_lines(), order_price=initial_offer_price)

    quote_service.get_tradable_quote = lookup_market_values

    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(o, quote_service)

    assert new_price.order_price_type == OrderPriceType.NET_DEBIT
    assert new_price.price == Amount(whole=0, part=34)

def test_scaled_multi_legged_trade():
    tradable_to_quantity_map: dict[Tradable, int] = dict[Tradable, int]()

    tradable_to_quantity_map[tradable0] = 5
    tradable_to_quantity_map[tradable1] = -5
    tradable_to_quantity_map[tradable2] = 5

    ts: TradeSetup = TradeSetup(market_price_lookup=tradable_to_market_price_lookup,
                                tradable_quantities=tradable_to_quantity_map)
    if ts.market_price.mark >= 0:
        # then we want to get more cash
        initial_offer_price = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount.from_float(2 * ts.market_price.ask))
    else:
        initial_offer_price = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount.from_float(0))

    o: Order = Order(expiry=GoodUntilCancelled(), order_lines=ts.to_order_lines(), order_price=initial_offer_price)

    quote_service.get_tradable_quote = lookup_market_values

    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(o, quote_service)

    assert new_price.order_price_type == OrderPriceType.NET_CREDIT
    assert new_price.price == Amount(whole=1, part=16)


def lookup_market_values(get_tradable_request: GetTradableRequest):
    return tradable_to_get_tradable_response_lookup[get_tradable_request.tradable]