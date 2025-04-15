import configparser
import os
from datetime import datetime

import pytest

from fianchetto_tradebot.common.api.orders.order_util import OrderUtil
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common.api.orders.order_list_request import ListOrdersRequest
from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from tests.common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.order.executed_order import ExecutedOrder
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.order.placed_order import PlacedOrder

"""
NOTE - To test in real life, it's necessary to include an `integration_test_properties.ini` file.
This file is in .gitignore, so as to not leak anyone's sensitive info when they commit code back.

An example is provided in `integration_test_properties.example.ini`.
"""

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'integration_test_properties.ini')
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

JAN_1_2024 = datetime(2024,1,1).date()
JAN_2_2024 = datetime(2024,1,2).date()

TODAY = datetime.now().date()
MAX_COUNT = 1000

config = configparser.ConfigParser()

@pytest.fixture
def account_key():
    config.read(CONFIG_FILE)
    return config['ETRADE'][ACCOUNT_ID_KEY]

@pytest.fixture
def order_service():
    config.read(CONFIG_FILE)
    connector: ETradeConnector = ETradeConnector()
    o: OrderService = ETradeOrderService(connector)
    return o

@pytest.fixture()
def spread_order(order_service, account_key)-> (str, PlacedOrder):
    order = OrderTestUtil.build_spread_order()
    order_metadata: OrderMetadata = OrderMetadata(order.get_order_type(), account_key, OrderUtil.generate_random_client_order_id())
    req: PreviewOrderRequest = PreviewOrderRequest(order_metadata, order)
    res: PlaceOrderResponse = order_service.preview_and_place_order(req)
    return res.order_id, res.order

def test_get_date_range_orders_within_range(order_service: OrderService, account_key: str):
    start_date = JAN_1_2024
    end_date = JAN_2_2024

    list_order_request = ListOrdersRequest(account_key, OrderStatus.ANY, start_date, end_date, 50)
    orders = order_service.list_orders(list_order_request, dict())

    for order in orders.order_list:
        if type(order) == ExecutedOrder:
            order = order.get_order()
        assert start_date <= order.order_placed_time.date() <= end_date

def test_get_open_orders(order_service: OrderService, account_key: str):
    list_order_request = ListOrdersRequest(account_key, OrderStatus.OPEN, JAN_1_2024, TODAY, 50)
    orders = order_service.list_orders(list_order_request, dict())
    assert orders.order_list[0].placed_order_details.status == OrderStatus.OPEN

def test_get_all_orders(order_service: OrderService, account_key: str):
    list_order_request = ListOrdersRequest(account_key, OrderStatus.ANY, JAN_1_2024, TODAY, 50)
    orders = order_service.list_orders(list_order_request, dict())
    assert len(orders.order_list) == 50

def test_get_specific_order(order_service, account_key, spread_order):
    order_id, order = spread_order
    req: GetOrderRequest = GetOrderRequest(account_key, order_id)
    res: GetOrderResponse = order_service.get_order(req)
    assert str(res.placed_order.placed_order_details.exchange_order_id) == str(order_id)


def test_get_specific_order_by_id(order_service, account_key):
    order_id = str(82936)
    req: GetOrderRequest = GetOrderRequest(account_key, order_id)
    res: GetOrderResponse = order_service.get_order(req)
    assert str(res.placed_order.placed_order_details.exchange_order_id) == str(order_id)



if __name__ == "__main__":
    pytest.main()