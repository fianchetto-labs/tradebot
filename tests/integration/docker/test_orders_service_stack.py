import os

import httpx
import pytest

from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from tests.fixtures.etrade_simulator_contract import ACCOUNT_ID
from tests.fixtures.etrade_simulator_contract import ORDER_ID
from tests.fixtures.etrade_simulator_contract import demo_preview_order_request


pytestmark = [pytest.mark.service, pytest.mark.docker, pytest.mark.integration]

ORDERS_BASE_URL_ENV_VAR = "TRADEBOT_TEST_ORDERS_BASE_URL"


@pytest.fixture
def orders_base_url() -> str:
    base_url = os.getenv(ORDERS_BASE_URL_ENV_VAR)
    if not base_url:
        pytest.skip(f"set {ORDERS_BASE_URL_ENV_VAR} to run orders service stack tests")
    return base_url.rstrip("/")


def test_orders_service_runs_simulator_backed_order_lifecycle(orders_base_url: str):
    preview_request = demo_preview_order_request()

    with httpx.Client(timeout=5) as client:
        health_response = client.get(f"{orders_base_url}/health-check")
        preview_response = client.post(
            f"{orders_base_url}/api/v1/ETRADE/accounts/{ACCOUNT_ID}/orders/preview",
            json=preview_request.model_dump(mode="json"),
        )

        assert preview_response.status_code == HttpStatusCode.OK
        preview_body = preview_response.json()
        place_request = PlaceOrderRequest(
            order_metadata=preview_request.order_metadata,
            preview_id=preview_body["preview_id"],
            order=preview_request.order,
        )
        place_url = (
            f"{orders_base_url}/api/v1/ETRADE/accounts/{ACCOUNT_ID}/orders/preview/"
            f"{preview_body['preview_id']}"
        )
        place_response = client.post(
            place_url,
            json=place_request.model_dump(mode="json"),
        )
        get_response = client.get(
            f"{orders_base_url}/api/v1/ETRADE/accounts/{ACCOUNT_ID}/orders/{ORDER_ID}"
        )
        cancel_response = client.delete(
            f"{orders_base_url}/api/v1/ETRADE/accounts/{ACCOUNT_ID}/orders/{ORDER_ID}"
        )

    assert health_response.status_code == HttpStatusCode.OK
    assert health_response.json() == "ORDERS Service Up"

    assert preview_body["request_status"] == "SUCCESS"

    assert place_response.status_code == HttpStatusCode.OK
    assert place_response.json()["order_id"] == ORDER_ID

    assert get_response.status_code == HttpStatusCode.OK
    assert get_response.json()["placed_order"]["placed_order_details"]["status"] == "OPEN"

    assert cancel_response.status_code == HttpStatusCode.OK
    assert cancel_response.json()["order_id"] == ORDER_ID
    assert cancel_response.json()["request_status"] == "SUCCESS"
