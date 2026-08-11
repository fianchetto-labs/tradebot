import os
import pickle
import stat
from unittest.mock import MagicMock

import pytest

from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.place_modify_order_request import PlaceModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_response import PreviewOrderResponse
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.orders.etrade.live_trading_gate import ETRADE_LIVE_WRITES_ENABLED_ENV_VAR
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector, DEFAULT_ETRADE_BASE_URL_FILE
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.order.executed_order import ExecutedOrder
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_type import OrderType
from tests.common.api.orders.order_test_util import OrderTestUtil

# TODO: Adjust this suite to do both XML and JSON inputs ..
# For some endpoints, I wasn't able to get the JSON input to work

ACCOUNT_ID = "account123"

CLIENT_ORDER_ID = "ABC123"
SPREAD_ORDER_PREVIEW_ID = "2060570516106"
SPREAD_ORDER_TOTAL_ORDER_VALUE = Amount(whole=247,part=95, negative=True)
SPREAD_ORDER_ESTIMATED_COMMISSION = Amount(whole=1,part=0)

SPREAD_ORDER_METADATA = OrderMetadata(order_type=OrderType.SPREADS, account_id=ACCOUNT_ID, client_order_id=CLIENT_ORDER_ID)

EXPECTED_ORDER_PRICE = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=2, part=49))

PLACED_ORDER_ID = 81117
FAKE_ETRADE_BASE_URL = "https://api.example.test"
LIVE_ETRADE_BASE_URL = "https://api.etrade.com"

SPREAD_PREVIEW_ORDER_RESPONSE_FILE = os.path.join(os.path.dirname(__file__), "./resources/output_preview_order_spread")
SPREAD_PLACE_ORDER_RESPONSE_FILE = os.path.join(os.path.dirname(__file__), "./resources/output_place_order_spread")

SPREAD_ORDER = OrderTestUtil.build_spread_order(EXPECTED_ORDER_PRICE)


class DummyJsonResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body

@pytest.fixture
def spread_preview_request()->PreviewOrderRequest:
    return PreviewOrderRequest(order_metadata=SPREAD_ORDER_METADATA, order=SPREAD_ORDER)

@pytest.fixture
def preview_order_spread_response():
    return _read_input(SPREAD_PREVIEW_ORDER_RESPONSE_FILE)

@pytest.fixture
def place_order_spread_response():
    return _read_input(SPREAD_PLACE_ORDER_RESPONSE_FILE)

@pytest.fixture
def connector():
    return _connector_with_base_url(FAKE_ETRADE_BASE_URL)

@pytest.fixture
def order_service(connector):
    # TODO: Set up the service that will provide mock responses to given requests
    return ETradeOrderService(connector)


def test_live_place_order_fails_closed_without_runtime_gate(monkeypatch):
    # Given
    # A service pointed at the live E*Trade API without the explicit write gate.
    monkeypatch.delenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, raising=False)
    order_service = ETradeOrderService(_connector_with_base_url(LIVE_ETRADE_BASE_URL))
    place_request = PlaceOrderRequest(
        order_metadata=SPREAD_ORDER_METADATA,
        preview_id=SPREAD_ORDER_PREVIEW_ID,
        order=SPREAD_ORDER,
    )

    # When / Then
    # The service rejects the live write before it reaches the brokerage session.
    with pytest.raises(PermissionError) as exc_info:
        order_service.place_order(place_request)

    assert "place_order" in str(exc_info.value)
    assert ETRADE_LIVE_WRITES_ENABLED_ENV_VAR in str(exc_info.value)
    assert ACCOUNT_ID not in str(exc_info.value)
    assert SPREAD_ORDER_PREVIEW_ID not in str(exc_info.value)
    order_service.session.post.assert_not_called()


def test_live_cancel_order_fails_closed_without_runtime_gate(monkeypatch):
    # Given
    # A service pointed at the live E*Trade API without the explicit write gate.
    monkeypatch.delenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, raising=False)
    order_service = ETradeOrderService(_connector_with_base_url(LIVE_ETRADE_BASE_URL))

    # When / Then
    # Cancellation is also blocked because it can change live trading outcomes.
    with pytest.raises(PermissionError) as exc_info:
        order_service.cancel_order(CancelOrderRequest(account_id=ACCOUNT_ID, order_id=str(PLACED_ORDER_ID)))

    assert "cancel_order" in str(exc_info.value)
    assert ACCOUNT_ID not in str(exc_info.value)
    assert str(PLACED_ORDER_ID) not in str(exc_info.value)
    order_service.session.put.assert_not_called()


def test_live_modify_order_fails_closed_before_canceling_original_order(monkeypatch):
    # Given
    # A live modify request that would cancel and replace the original order.
    monkeypatch.delenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, raising=False)
    order_service = ETradeOrderService(_connector_with_base_url(LIVE_ETRADE_BASE_URL))
    modify_request = PreviewModifyOrderRequest(
        order_metadata=SPREAD_ORDER_METADATA,
        order_id_to_modify=str(PLACED_ORDER_ID),
        order=SPREAD_ORDER,
    )

    # When / Then
    # The guard rejects the modify operation before the internal cancel path runs.
    with pytest.raises(PermissionError) as exc_info:
        order_service.modify_order(modify_request)

    assert "modify_order" in str(exc_info.value)
    order_service.session.put.assert_not_called()
    order_service.session.post.assert_not_called()


def test_live_place_modify_order_fails_closed_without_runtime_gate(monkeypatch):
    # Given
    # A direct place-modify call against the live E*Trade API.
    monkeypatch.delenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, raising=False)
    order_service = ETradeOrderService(_connector_with_base_url(LIVE_ETRADE_BASE_URL))
    place_modify_request = PlaceModifyOrderRequest(
        order_metadata=SPREAD_ORDER_METADATA,
        order_id_to_modify=str(PLACED_ORDER_ID),
        preview_id=SPREAD_ORDER_PREVIEW_ID,
        order=SPREAD_ORDER,
    )

    # When / Then
    # The service rejects the live write before it reaches the brokerage session.
    with pytest.raises(PermissionError) as exc_info:
        order_service.place_modify_order(place_modify_request)

    assert "place_modify_order" in str(exc_info.value)
    order_service.session.put.assert_not_called()


def test_live_preview_and_place_order_fails_closed_before_preview(monkeypatch, spread_preview_request):
    # Given
    # A combined preview-and-place request against the live E*Trade API.
    monkeypatch.delenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, raising=False)
    order_service = ETradeOrderService(_connector_with_base_url(LIVE_ETRADE_BASE_URL))

    # When / Then
    # The service rejects the operation before sending the preview request.
    with pytest.raises(PermissionError) as exc_info:
        order_service.preview_and_place_order(spread_preview_request)

    assert "preview_and_place_order" in str(exc_info.value)
    order_service.session.post.assert_not_called()


def test_live_place_order_runs_when_runtime_gate_is_explicitly_enabled(monkeypatch, place_order_spread_response):
    # Given
    # A live service with the explicit write gate enabled.
    monkeypatch.setenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, "true")
    order_service = ETradeOrderService(_connector_with_base_url(LIVE_ETRADE_BASE_URL))
    order_service.session.post.return_value = place_order_spread_response

    # When
    response = order_service.place_order(
        PlaceOrderRequest(
            order_metadata=SPREAD_ORDER_METADATA,
            preview_id=SPREAD_ORDER_PREVIEW_ID,
            order=SPREAD_ORDER,
        )
    )

    # Then
    assert response.order_id == str(PLACED_ORDER_ID)
    order_service.session.post.assert_called_once()


def test_non_live_place_order_does_not_require_runtime_gate(monkeypatch, place_order_spread_response):
    # Given
    # A simulator or test endpoint, where writes do not touch the live broker.
    monkeypatch.delenv(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, raising=False)
    order_service = ETradeOrderService(_connector_with_base_url("http://etrade-sim:8090"))
    order_service.session.post.return_value = place_order_spread_response

    # When
    response = order_service.place_order(
        PlaceOrderRequest(
            order_metadata=SPREAD_ORDER_METADATA,
            preview_id=SPREAD_ORDER_PREVIEW_ID,
            order=SPREAD_ORDER,
        )
    )

    # Then
    assert response.order_id == str(PLACED_ORDER_ID)
    order_service.session.post.assert_called_once()

def test_process_spread_preview_order_response(preview_order_spread_response):
    response: PreviewOrderResponse = ETradeOrderService._parse_preview_order_response(preview_order_spread_response, SPREAD_ORDER_METADATA)
    assert SPREAD_ORDER_PREVIEW_ID == str(response.preview_id)
    assert SPREAD_ORDER_TOTAL_ORDER_VALUE == response.preview_order_info.total_order_value
    assert SPREAD_ORDER_ESTIMATED_COMMISSION == response.preview_order_info.estimated_commission

def test_process_spread_place_order_response_id_parsed(place_order_spread_response):
    response: PlaceOrderResponse = ETradeOrderService._parse_place_order_response(place_order_spread_response, SPREAD_ORDER_METADATA, SPREAD_ORDER_PREVIEW_ID)
    assert str(PLACED_ORDER_ID) == response.order_id

def test_process_spread_place_order_response_order_parsed(place_order_spread_response):
    response: PlaceOrderResponse = ETradeOrderService._parse_place_order_response(place_order_spread_response, SPREAD_ORDER_METADATA, SPREAD_ORDER_PREVIEW_ID)
    assert SPREAD_ORDER == response.order

def test_preview_spread_order_posts_spread_preview_request(order_service, spread_preview_request, preview_order_spread_response):
    # Given a mock service
    session = order_service.session
    session.post = MagicMock(return_value = preview_order_spread_response)

    # Given a Request
    response: PreviewOrderResponse = order_service.preview_order(spread_preview_request)

    # Assert output makes sense
    session.post.assert_called_once()
    assert session.post.call_args.args[0] == f"{FAKE_ETRADE_BASE_URL}/v1/accounts/{ACCOUNT_ID}/orders/preview.json"
    assert SPREAD_ORDER_PREVIEW_ID == str(response.preview_id)

def test_place_order():
    # TODO: Implement this test
    # Given an order that has been previewed

    # When a user makes place request to the service

    # Assert that the place response is handled correctly
    pass

def test_cancel_placed_order():
    # TODO: Implement this test
    # Given an order that has been placed

    # When a user cancels that order

    # That the cancellation response is processed correctly

    pass

def test_modify_order_preview():
    # TODO: Implement this test
    pass

def test_place_modified_order():
    # TODO: Implement this test
    pass


def test_parse_order_list_response_handles_no_content_status():
    response = DummyJsonResponse(HttpStatusCode.NO_CONTENT, {})

    assert ETradeOrderService._parse_order_list_response(response, ACCOUNT_ID) == []


def test_parse_get_order_response_returns_executed_order_for_executed_status():
    response = DummyJsonResponse(HttpStatusCode.OK, {
        "OrdersResponse": {
            "Order": [
                {
                    "orderId": PLACED_ORDER_ID,
                    "OrderDetail": [
                        {
                            "accountId": ACCOUNT_ID,
                            "status": "EXECUTED",
                            "placedTime": 1700000000000,
                            "executedTime": 1700000001000,
                            "orderValue": 12.34,
                            "marketSession": "REGULAR",
                            "netPrice": -12.34,
                            "netBid": -12.30,
                            "netAsk": -12.38,
                            "allOrNone": False,
                            "orderTerm": "GOOD_FOR_DAY",
                            "priceType": "LIMIT",
                            "limitPrice": 12.34,
                            "Instrument": [
                                {
                                    "orderedQuantity": 1,
                                    "filledQuantity": 1,
                                    "orderAction": "BUY",
                                    "Product": {
                                        "securityType": "EQ",
                                        "symbol": "GE"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    })

    parsed_response = ETradeOrderService._parse_get_order_response(response, ACCOUNT_ID, str(PLACED_ORDER_ID))

    assert isinstance(parsed_response.placed_order, ExecutedOrder)


def test_connector_serializes_base_url_as_private_json(tmp_path):
    connector = object.__new__(ETradeConnector)
    base_url_file = tmp_path / "base_url.json"
    connector.base_url_file = str(base_url_file)

    connector.serialize_base_url("https://api.example.test")

    assert ETradeConnector.deserialize_base_url(base_url_file) == "https://api.example.test"
    assert stat.S_IMODE(base_url_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(base_url_file.parent.stat().st_mode) == 0o700


def test_connector_rebuilds_sessions_from_private_json_credentials(tmp_path):
    connector = object.__new__(ETradeConnector)
    credentials_file = tmp_path / "connection.json"
    connector.credentials_file = str(credentials_file)

    connector.serialize_connection_credentials(
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        access_token="access-token",
        access_token_secret="access-token-secret",
        request_token="request-token",
        request_token_secret="request-token-secret",
        base_url="https://api.example.test",
    )

    session, async_session, base_url = ETradeConnector._build_connection_from_credentials_file(credentials_file)

    assert session.access_token == "access-token"
    assert session.access_token_secret == "access-token-secret"
    assert async_session.oauth_token == "access-token"
    assert async_session.oauth_token_secret == "access-token-secret"
    assert base_url == "https://api.example.test"
    assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600

def _read_input(input_file):
    with open(input_file, 'rb') as handle:
        response = pickle.load(handle)
    return response


def _connector_with_base_url(base_url: str):
    session = MagicMock()
    async_session = MagicMock()
    connector = MagicMock(spec=ETradeConnector)
    connector.load_connection.return_value = (session, async_session, base_url)
    return connector

if __name__ == "__main__":
    pass
