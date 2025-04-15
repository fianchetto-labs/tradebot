import configparser
import os

import pytest

from fianchetto_tradebot.common.api.orders.order_util import OrderUtil
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common.api.orders.preview_order_response import PreviewOrderResponse
from tests.common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.order.order_type import OrderType


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'integration_test_properties.ini')
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

config = configparser.ConfigParser()

@pytest.fixture
def account_id():
    return config['ETRADE'][ACCOUNT_ID_KEY]

@pytest.fixture
def order_service():
    config.read(CONFIG_FILE)
    connector: ETradeConnector = ETradeConnector()
    o: OrderService = ETradeOrderService(connector)
    return o


def test_submit_orders(order_service: OrderService, account_id: str):
    order = OrderTestUtil.build_three_option_put_one_spread_one_naked()

    order_type: OrderType = order.get_order_type()

    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type, account_id, client_order_id)

    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata, order)
    preview_order_response: PreviewOrderResponse = order_service.preview_order(preview_order_request)
    preview_id: str = preview_order_response.preview_id

    place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata, preview_id, order)
    place_order_response: PlaceOrderResponse = order_service.place_order(place_order_request)

    order_id = place_order_response.order_id

    response = order_service.get_order(GetOrderRequest(account_id, order_id))
    print(response.placed_order.order.order_id)
