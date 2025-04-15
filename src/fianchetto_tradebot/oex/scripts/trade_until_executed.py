import configparser
import datetime
import os
from time import sleep

import pytest

from fianchetto_tradebot.common.api.orders.order_util import OrderUtil
from fianchetto_tradebot.common.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from tests.common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.order.order_type import OrderType
from fianchetto_tradebot.quotes.etrade.etrade_quote_service import ETradeQuoteService
from fianchetto_tradebot.quotes.quote_service import QuoteService
from fianchetto_tradebot.oex.tactics.incremental_price_delta_execution_tactic import IncrementalPriceDeltaExecutionTactic
from fianchetto_tradebot.oex.trade_execution_util import TradeExecutionUtil

DEFAULT_WAIT: datetime.timedelta = datetime.timedelta(seconds=8)
DEFAULT_INITIAL_DELTA = Amount(whole=0, part=25)

CONFIG_FILE = os.path.join(os.path.dirname(__file__),'../../common/api/scripts/', 'integration_test_properties.ini')
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

SFIX = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")

ZERO = Amount(whole=0, part=0)

TRADE_IN_PROGRESS_ERROR_CODE = 5001
TRADE_IN_PROGRESS_MSG = 'currently being executed or rejected'

@pytest.fixture
def connector():
    return get_connector()

def get_connector():
    return ETradeConnector()

@pytest.fixture
def quote_service(connector):
    return get_quote_service(connector)

def get_quote_service(connector):
    q: QuoteService = ETradeQuoteService(connector)
    return q

@pytest.fixture
def order_service(connector):
    return get_order_service(connector)

def get_order_service(connector):
    o: OrderService = ETradeOrderService(connector)
    return o

@pytest.fixture
def account_id()->str:
    return config['ETRADE'][ACCOUNT_ID_KEY]

def test_lower_until_executed(account_id: str, quote_service: QuoteService, order_service: OrderService):

    # The pattern is we'll put in the order, to get a sense of the actual price, once the response returns. From there, we'll keep getting new prices until it's clsoed.
    # Get a sense of what it may be worth
    order = OrderTestUtil.build_equity_order(equity=SFIX, action=Action.BUY)
    order_market_price: Price = TradeExecutionUtil.get_market_price(order, quote_service)
    print(f"Security currently at: {order_market_price}")

    # Find a price that's reasonable
    potential_order_price: Amount = Amount.from_float(order_market_price.mark) + DEFAULT_INITIAL_DELTA if order.order_price.order_price_type is OrderPriceType.NET_CREDIT else Amount.from_float(order_market_price.mark) - DEFAULT_INITIAL_DELTA
    order.order_price.price = potential_order_price

    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order.get_order_type(), account_id=account_id, client_order_id=client_order_id)
    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)

    # place the order
    place_order_response: PlaceOrderResponse = order_service.preview_and_place_order(preview_order_request)
    order_id = place_order_response.order_id

    adjust_order_until_executed(account_id, order_id, order_service, quote_service)

def adjust_order_until_executed(account_id: str, order_id: str, order_service: OrderService, quote_service: QuoteService):
        # Get information about the order
        get_order_response: GetOrderResponse = order_service.get_order(GetOrderRequest(account_id=account_id, order_id=order_id))
        placed_order = get_order_response.placed_order
        order_type: OrderType = placed_order.order.get_order_type()
        order = placed_order.order

        while placed_order.placed_order_details.status == OrderStatus.OPEN:
            print("Cancelling old order")
            cancel_order_request: CancelOrderRequest = CancelOrderRequest(account_id=account_id, order_id=order_id)
            response: CancelOrderResponse = order_service.cancel_order(cancel_order_request)
            if response.request_status.is_permanent_failure():
                if response.messages:
                    message = response.messages[0]
                    if message.code == TRADE_IN_PROGRESS_ERROR_CODE and TRADE_IN_PROGRESS_MSG in message.message:
                        print(f"Order {order_id} executed!")
                        return
                    raise Exception(f"Order cancellation for {order_id} failed with message: {message}")
                else:
                    raise Exception(f"Order cancellation for {order_id}.")
            else:
                print(f"Cancelled old order {response.order_id}")

            new_price, wait_period = IncrementalPriceDeltaExecutionTactic.new_price(placed_order, quote_service)
            order.order_price.price = new_price.price

            order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, order_id=OrderUtil.generate_random_client_order_id())
            preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)

            # place the order
            print("Submitted new order")
            response: PlaceOrderResponse = order_service.preview_and_place_order(preview_order_request)

            print(f"New order is {response.order_id}")
            order_id = response.order_id

            order_status = order_service.get_order(
                GetOrderRequest(account_id=account_id, order_id=order_id)).placed_order.placed_order_details.status
            print(f"Order status {response.order_id}: {order_status}")
            if order_status == OrderStatus.EXECUTED:
                print("Awesome, it executed!")
                break

            print(f"Sleeping {wait_period} seconds before adding new order")
            sleep(wait_period)

if __name__ == "__main__":
    connector = get_connector()
    adjust_order_until_executed("1XRq48Mv_HUiP8xmEZRPnA","84077", get_order_service(connector), get_quote_service(connector))