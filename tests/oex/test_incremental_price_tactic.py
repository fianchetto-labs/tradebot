import datetime
from unittest.mock import patch, MagicMock

import pytest
from rauth import OAuth1Session

from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector, DEFAULT_ETRADE_BASE_URL_FILE
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder
from fianchetto_tradebot.common_models.order.placed_order_details import PlacedOrderDetails
from fianchetto_tradebot.server.orders.tactics.incremental_price_delta_execution_tactic import \
    IncrementalPriceDeltaExecutionTactic
from tests.common.api.orders.order_test_util import OrderTestUtil

ORDER_PRICE_EXACTLY_200 = Amount(whole=200, part=0)
ORDER_PRICE_EXACTLY_100: Amount = Amount(whole=100, part=0)

MARKET_PRICE_NEAR_125 = Price(bid=124.95, ask=125.05)

THIRTY_CENTS: Price = Price(bid=.28, ask=.32)

SIXTY_CENTS_AMT: Amount = Amount(whole=0, part=60)
EXACTLY_SIXTY_CENTS: Amount = Amount(whole=0, part=60)

CREDIT_SIXTY_CENTS = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=SIXTY_CENTS_AMT)
DEBIT_SIXTY_CENTS = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=EXACTLY_SIXTY_CENTS)

NINETY_CENTS_MARKET_PRICE: Price = Price(bid=-.85, ask=-.95)

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

def get_equity_order_response(action: Action, current_order_price: Amount, current_market_price_equity: Price):
    equity_order: Order = OrderTestUtil.build_equity_order(action=action, price=current_order_price)

    placed_order_details: PlacedOrderDetails = PlacedOrderDetails(account_id="account1", brokerage_order_id="123", status=OrderStatus.OPEN, order_placed_time=datetime.datetime.now(), current_market_price=current_market_price_equity)
    placed_order: PlacedOrder = PlacedOrder(order=equity_order, placed_order_details=placed_order_details)
    return GetOrderResponse(placed_order=placed_order)

def get_spread_order_response(current_order_price: OrderPrice, current_market_price: Price):
    equity_order: Order = OrderTestUtil.build_spread_order(order_price=current_order_price)
    placed_order_details: PlacedOrderDetails = PlacedOrderDetails(account_id="account1", brokerage_order_id="123", status=OrderStatus.OPEN, order_placed_time=datetime.datetime.now(), current_market_price=current_market_price)
    placed_order: PlacedOrder = PlacedOrder(order=equity_order, placed_order_details=placed_order_details)
    return GetOrderResponse(placed_order=placed_order)

def test_equity_order_price_less_than_market_price_debit():
    placed_order = get_equity_order_response(Action.BUY, ORDER_PRICE_EXACTLY_100, MARKET_PRICE_NEAR_125).placed_order
    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(placed_order)

    assert new_price.price == Amount(whole=108, part=33)
    assert new_price.order_price_type == OrderPriceType.LIMIT

def test_spread_order_price_more_than_market_price_credit():
    placed_order = get_spread_order_response(current_order_price=CREDIT_SIXTY_CENTS, current_market_price=THIRTY_CENTS).placed_order
    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(placed_order)

    assert new_price.order_price_type == OrderPriceType.NET_CREDIT
    assert new_price.price == Amount(whole=0, part=50)

def test_spread_order_price_less_than_market_price_debit():
    placed_order = get_spread_order_response(DEBIT_SIXTY_CENTS, NINETY_CENTS_MARKET_PRICE).placed_order
    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(placed_order)

    assert new_price.price == Amount(whole=0, part=70, negative=False)
    assert new_price.order_price_type == OrderPriceType.NET_DEBIT

def test_equity_order_price_more_than_market_price_credit():
    placed_order = get_equity_order_response(Action.SELL, ORDER_PRICE_EXACTLY_200, MARKET_PRICE_NEAR_125).placed_order
    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(placed_order)

    assert new_price.price == Amount(whole=175, part=0)
    assert new_price.order_price_type == OrderPriceType.LIMIT

def test_equity_order_price_increments_by_one_when_near_mark_to_market():
    placed_order = get_equity_order_response(Action.SELL, Amount(whole=124, part=96), MARKET_PRICE_NEAR_125).placed_order
    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(placed_order)

    assert new_price.price == Amount(whole=124, part=95)

    placed_order.order.order_price.price = new_price.price
    new_price, _ = IncrementalPriceDeltaExecutionTactic.new_price(placed_order)

    assert new_price.price == Amount(whole=124, part=94)
    assert new_price.order_price_type == OrderPriceType.LIMIT