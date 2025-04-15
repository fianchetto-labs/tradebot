import configparser
import os

import pytest

from fianchetto_tradebot.common.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector

ORDER_IDS_TO_CANCEL = range(81276, 81285)

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


def test_cancel_orders(order_service: OrderService, account_id: str):
    for order_id in ORDER_IDS_TO_CANCEL:
        try:
            cancel_order_response = order_service.cancel_order(CancelOrderRequest(account_id, str(order_id)))
            print(f"Successfully cancelled: {cancel_order_response.order_id}")
        except KeyError:
            print(f"failed to delete for {order_id}")


    cancel_order_request: CancelOrderRequest = CancelOrderRequest(account_id, order_id)
    cancel_order_response: CancelOrderResponse = order_service.cancel_order(cancel_order_request)
    print(cancel_order_response)