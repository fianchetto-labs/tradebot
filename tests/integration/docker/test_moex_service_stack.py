import os
import time
from collections.abc import Callable

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
    # Given
    # A healthy Docker MOEX stack backed by the default open-order simulator scenario.
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

        # When
        # A managed execution is created and then explicitly cancelled by TradeBot.
        create_response = client.post(
            f"{moex_base_url}/api/v1/managed-executions",
            json=request.model_dump(mode="json"),
        )

        assert create_response.status_code == HttpStatusCode.OK, create_response.text
        managed_execution_id = create_response.json()["managed_execution_id"]
        cancel_response = client.delete(
            f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}"
        )

    # Then
    # The active cancellation path cancels the managed execution and preserves order state.
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
    # Given
    # A Docker MOEX stack whose simulator will eventually execute the brokerage order.
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

        # When
        # A managed execution reaches EXECUTED and receives a later cancel request.
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
        cancel_response = client.delete(
            f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}"
        )

    # Then
    # The terminal managed execution state is not overwritten by the later command.
    assert managed_execution["brokerage"] == "etrade"
    assert managed_execution["account_id"] == ACCOUNT_ID
    assert managed_execution["status"] == "EXECUTED"
    assert managed_execution["current_order_status"] == "EXECUTED"
    assert managed_execution["current_brokerage_order_id"].startswith("order-")
    assert cancel_response.status_code == HttpStatusCode.OK, cancel_response.text
    assert cancel_response.json()["managed_execution"]["status"] == "EXECUTED"


def test_moex_service_treats_broker_cancelled_order_as_transient_work(
    etrade_simulator_base_url: str,
    moex_base_url: str,
):
    # Given
    # A Docker MOEX stack whose broker simulator cancels the underlying order.
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
            "broker-cancelled",
        )

        # When
        # MOEX observes the broker-side cancellation and is later explicitly cancelled.
        create_response = client.post(
            f"{moex_base_url}/api/v1/managed-executions",
            json=request.model_dump(mode="json"),
        )

        assert create_response.status_code == HttpStatusCode.OK, create_response.text
        managed_execution_id = create_response.json()["managed_execution_id"]
        working_after_broker_cancel = _wait_for_managed_execution(
            client,
            moex_base_url,
            managed_execution_id,
            lambda managed_execution: (
                managed_execution["status"] == "WORKING"
                and managed_execution["current_order_status"] == "CANCELLED"
            ),
            expected_description="WORKING with a broker-side CANCELLED order",
        )
        cancel_response = client.delete(
            f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}"
        )

    # Then
    # Broker-side cancellation is treated as transient work, not managed-execution failure.
    assert working_after_broker_cancel["brokerage"] == "etrade"
    assert working_after_broker_cancel["account_id"] == ACCOUNT_ID
    assert working_after_broker_cancel["status"] == "WORKING"
    assert working_after_broker_cancel["current_order_status"] == "CANCELLED"
    assert cancel_response.status_code == HttpStatusCode.OK, cancel_response.text
    assert cancel_response.json()["managed_execution"]["status"] == "CANCELLED"


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
    return _wait_for_managed_execution(
        client,
        moex_base_url,
        managed_execution_id,
        lambda managed_execution: managed_execution["status"] == expected_status,
        expected_description=expected_status,
        timeout_seconds=timeout_seconds,
    )


def _wait_for_managed_execution(
    client: httpx.Client,
    moex_base_url: str,
    managed_execution_id: str,
    predicate: Callable[[dict], bool],
    expected_description: str,
    timeout_seconds: float = 20,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_response_text = ""

    while time.monotonic() < deadline:
        response = client.get(f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}")
        last_response_text = response.text
        assert response.status_code == HttpStatusCode.OK, response.text

        managed_execution = response.json()["managed_execution"]
        if predicate(managed_execution):
            return managed_execution
        time.sleep(0.25)

    pytest.fail(
        f"Managed execution {managed_execution_id} did not reach {expected_description} "
        f"within {timeout_seconds} seconds. Last response: {last_response_text}"
    )
