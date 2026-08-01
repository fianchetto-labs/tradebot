import os
import time

import httpx
import pytest

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import (
    CreateManagedExecutionRequest,
)
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.orders.managed_order_execution import (
    ManagedExecutionCreationParams,
    ManagedExecutionCreationType,
)
from tests.fixtures.etrade_simulator_contract import ACCOUNT_ID
from tests.fixtures.etrade_simulator_contract import demo_order


pytestmark = [pytest.mark.service, pytest.mark.docker, pytest.mark.integration]

ETRADE_SIMULATOR_BASE_URL_ENV_VAR = "TRADEBOT_TEST_ETRADE_SIMULATOR_BASE_URL"
MOEX_BASE_URL_ENV_VAR = "TRADEBOT_TEST_MOEX_BASE_URL"


@pytest.fixture
def etrade_simulator_base_url() -> str:
    base_url = os.getenv(ETRADE_SIMULATOR_BASE_URL_ENV_VAR)
    if not base_url:
        pytest.skip(f"set {ETRADE_SIMULATOR_BASE_URL_ENV_VAR} to run MOEX service stack tests")
    return base_url.rstrip("/")


@pytest.fixture
def moex_base_url() -> str:
    base_url = os.getenv(MOEX_BASE_URL_ENV_VAR)
    if not base_url:
        pytest.skip(f"set {MOEX_BASE_URL_ENV_VAR} to run MOEX service stack tests")
    return base_url.rstrip("/")


def test_moex_service_runs_networked_managed_execution_lifecycle(
    etrade_simulator_base_url: str,
    moex_base_url: str,
):
    request = CreateManagedExecutionRequest(
        managed_execution_creation_params=ManagedExecutionCreationParams(
            managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER,
            brokerage=Brokerage.ETRADE,
            account_id=ACCOUNT_ID,
            creation_order=demo_order(),
        )
    )

    with httpx.Client(timeout=20) as client:
        _reset_etrade_simulator(client, etrade_simulator_base_url)
        health_response = client.get(f"{moex_base_url}/health-check")
        create_response = client.post(
            f"{moex_base_url}/api/v1/managed-executions",
            json=request.model_dump(mode="json"),
        )

        assert create_response.status_code == HttpStatusCode.OK, create_response.text
        managed_execution_id = create_response.json()["managed_execution_id"]
        cancel_response = client.delete(
            f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}"
        )

    assert health_response.status_code == HttpStatusCode.OK
    assert health_response.json() == "MOEX Service Up"

    assert managed_execution_id
    assert cancel_response.status_code == HttpStatusCode.OK, cancel_response.text
    body = cancel_response.json()
    assert body["managed_execution"]["brokerage"] == "etrade"
    assert body["managed_execution"]["account_id"] == ACCOUNT_ID
    assert body["managed_execution"]["status"] == "CANCELLED"
    assert body["managed_execution"]["current_order_status"] == "OPEN"
    assert body["managed_execution"]["current_brokerage_order_id"].startswith("order-")


def test_moex_service_observes_networked_managed_execution_success(
    etrade_simulator_base_url: str,
    moex_base_url: str,
):
    request = CreateManagedExecutionRequest(
        managed_execution_creation_params=ManagedExecutionCreationParams(
            managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER,
            brokerage=Brokerage.ETRADE,
            account_id=ACCOUNT_ID,
            creation_order=demo_order(),
        )
    )

    with httpx.Client(timeout=20) as client:
        _reset_etrade_simulator(client, etrade_simulator_base_url)
        _set_etrade_order_lifecycle_scenario(
            client,
            etrade_simulator_base_url,
            "eventually-executed",
        )
        create_response = client.post(
            f"{moex_base_url}/api/v1/managed-executions",
            json=request.model_dump(mode="json"),
        )

        assert create_response.status_code == HttpStatusCode.OK, create_response.text
        managed_execution_id = create_response.json()["managed_execution_id"]
        managed_execution = _wait_for_managed_execution_status(
            client,
            moex_base_url,
            managed_execution_id,
            expected_status="EXECUTED",
        )

    assert managed_execution["brokerage"] == "etrade"
    assert managed_execution["account_id"] == ACCOUNT_ID
    assert managed_execution["status"] == "EXECUTED"
    assert managed_execution["current_order_status"] == "EXECUTED"
    assert managed_execution["current_brokerage_order_id"].startswith("order-")


def _reset_etrade_simulator(client: httpx.Client, etrade_simulator_base_url: str) -> None:
    response = client.post(f"{etrade_simulator_base_url}/_simulator/reset")
    assert response.status_code == HttpStatusCode.OK, response.text


def _set_etrade_order_lifecycle_scenario(
    client: httpx.Client,
    etrade_simulator_base_url: str,
    scenario: str,
) -> None:
    response = client.post(
        f"{etrade_simulator_base_url}/_simulator/order-lifecycle-scenario",
        json={"scenario": scenario},
    )
    assert response.status_code == HttpStatusCode.OK, response.text
    assert response.json()["scenario"] == scenario


def _wait_for_managed_execution_status(
    client: httpx.Client,
    moex_base_url: str,
    managed_execution_id: str,
    expected_status: str,
    timeout_seconds: float = 20,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_response_text = ""

    while time.monotonic() < deadline:
        response = client.get(f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}")
        last_response_text = response.text
        assert response.status_code == HttpStatusCode.OK, response.text

        managed_execution = response.json()["managed_execution"]
        if managed_execution["status"] == expected_status:
            return managed_execution
        time.sleep(0.25)

    pytest.fail(
        f"Managed execution {managed_execution_id} did not reach {expected_status} "
        f"within {timeout_seconds} seconds. Last response: {last_response_text}"
    )
