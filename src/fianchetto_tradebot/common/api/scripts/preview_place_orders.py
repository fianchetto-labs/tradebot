import configparser
import copy
import os
from datetime import datetime

import jsonpickle
import pytest

from fianchetto_tradebot.common.api.orders.order_util import OrderUtil
from fianchetto_tradebot.common.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common.api.orders.order_list_request import ListOrdersRequest
from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.api.orders.place_modify_order_request import PlaceModifyOrderRequest
from fianchetto_tradebot.common.api.orders.place_modify_order_response import PlaceModifyOrderResponse
from fianchetto_tradebot.common.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common.api.orders.preview_modify_order_response import PreviewModifyOrderResponse
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common.api.orders.preview_order_response import PreviewOrderResponse
from tests.common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.order.order import Order
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.order.order_type import OrderType

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
    return config['ETRADE'][ACCOUNT_ID_KEY]

@pytest.fixture
def order_service():
    config.read(CONFIG_FILE)
    connector: ETradeConnector = ETradeConnector()
    o: OrderService = ETradeOrderService(connector)
    return o

def test_equity_order_for_preview_using_json_pickle(order_service: OrderService, account_key: str):
    order_type: OrderType = OrderType.EQ
    account_id = account_key
    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

    order = OrderTestUtil.build_equity_order()

    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)

    result = jsonpickle.encode(preview_order_request)
    print(result)

    decoded: PreviewOrderRequest = jsonpickle.decode(result)
    assert decoded.order_metadata.client_order_id == client_order_id


def test_equity_order_for_preview_using_pydantic(order_service: OrderService, account_key: str):
    order_type: OrderType = OrderType.EQ
    account_id = account_key
    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

    order = OrderTestUtil.build_equity_order()

    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)

    as_json: str = preview_order_request.model_dump_json()
    print(as_json)
    as_model: dict = preview_order_request.model_dump()
    print(as_model)

    decoded_str = PreviewOrderRequest.model_validate(as_model)
    print(decoded_str)
    decoded: PreviewOrderRequest = PreviewOrderRequest.model_validate_json(as_json)
    print(decoded)
    assert decoded.order_metadata.client_order_id == client_order_id
    assert decoded_str.order_metadata.client_order_id == client_order_id

def test_equity_order_for_preview_and_place(order_service: OrderService, account_key: str):
    order_type: OrderType = OrderType.EQ
    account_id = account_key
    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

    order = OrderTestUtil.build_equity_order()

    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)
    preview_order_response: PreviewOrderResponse = order_service.preview_order(preview_order_request)
    preview_id: str = preview_order_response.preview_id

    place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata=order_metadata, preview_id=preview_id, order=order)
    place_order_response: PlaceOrderResponse = order_service.place_order(place_order_request)

    order_id = place_order_response.order_id
    assert order_id is not None

def test_equity_order_for_preview_place_and_cancel(order_service: OrderService, account_key: str):
    order_type: OrderType = OrderType.EQ
    account_id = account_key
    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

    order = OrderTestUtil.build_equity_order()

    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)
    preview_order_response: PreviewOrderResponse = order_service.preview_order(preview_order_request)
    preview_id: str = preview_order_response.preview_id

    place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata=order_metadata, preview_id=preview_id, order=order)
    place_order_response: PlaceOrderResponse = order_service.place_order(place_order_request)

    order_id = place_order_response.order_id

    cancel_order_request: CancelOrderRequest = CancelOrderRequest(account_id=account_id, order_id=order_id)
    cancel_order_response: CancelOrderResponse = order_service.cancel_order(cancel_order_request)
    print(cancel_order_response)

def test_option_order_for_preview_and_place(order_service: OrderService, account_key: str):
    order_type: OrderType = OrderType.BUY_WRITES
    account_id = account_key
    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

    order = OrderTestUtil.build_short_covered_call()
    preview_order_request : PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)
    print(preview_order_request.model_dump_json())

    preview_order_response: PreviewOrderResponse = order_service.preview_order(preview_order_request)
    preview_id = preview_order_response.preview_id

    place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata=order_metadata, preview_id=preview_id, order=order)
    print(place_order_request.model_dump_json())

    place_order_response: PlaceOrderResponse = order_service.place_order(place_order_request)
    print(place_order_response)

def test_option_order_for_preview_place_preview_modify_and_place_modify(order_service: OrderService, account_key: str):
    order_type: OrderType = OrderType.SPREADS
    account_id = account_key
    client_order_id = OrderUtil.generate_random_client_order_id()
    order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

    order = OrderTestUtil.build_spread_order()

    # Preview
    preview_order_request: PreviewOrderRequest = PreviewOrderRequest(order_metadata=order_metadata, order=order)
    preview_order_response: PreviewOrderResponse = order_service.preview_order(preview_order_request)

    preview_id = preview_order_response.preview_id

    # Place
    place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata=order_metadata, preview_id=preview_id, order=order)
    place_order_response: PlaceOrderResponse = order_service.place_order(place_order_request)
    print(place_order_response.model_dump_json())

    placed_order_id = place_order_response.order_id

    modified_order: Order = copy.deepcopy(place_order_response.order)
    modified_order.order_price.price = modified_order.order_price.price + Amount(0,5)

    # Regenerate client
    order_metadata.client_order_id = OrderUtil.generate_random_client_order_id()

    # Preview Modify
    preview_modify_order_request: PreviewModifyOrderRequest = PreviewModifyOrderRequest(order_metadata, placed_order_id, modified_order)
    preview_modify_order_response: PreviewModifyOrderResponse = order_service.preview_modify_order(preview_modify_order_request)

    modified_preview_id = preview_modify_order_response.preview_id

    # Place Modify
    place_modify_order_request: PlaceModifyOrderRequest = PlaceModifyOrderRequest(order_metadata, modified_preview_id, placed_order_id, modified_order)
    place_modify_order_response: PlaceModifyOrderResponse = order_service.place_modify_order(place_modify_order_request)

    assert place_modify_order_response.order_id is not None


def test_set_options_order_for_preview(order_service: OrderService, account_key: str):
    list_order_request = ListOrdersRequest(account_key, OrderStatus.OPEN, JAN_1_2024, TODAY, 50)
    orders = order_service.list_orders(list_order_request, dict())
    assert orders.order_list[0].placed_order_details.status == OrderStatus.OPEN

if __name__ == "__main__":
    pytest.main()