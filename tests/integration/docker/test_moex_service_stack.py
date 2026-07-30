import os

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
from tests.fixtures.etrade_simulator_contract import ORDER_ID
from tests.fixtures.etrade_simulator_contract import demo_order


pytestmark = [pytest.mark.service, pytest.mark.docker, pytest.mark.integration]

MOEX_BASE_URL_ENV_VAR = "TRADEBOT_TEST_MOEX_BASE_URL"


@pytest.fixture
def moex_base_url() -> str:
    base_url = os.getenv(MOEX_BASE_URL_ENV_VAR)
    if not base_url:
        pytest.skip(f"set {MOEX_BASE_URL_ENV_VAR} to run MOEX service stack tests")
    return base_url.rstrip("/")


def test_moex_service_runs_networked_managed_execution_lifecycle(moex_base_url: str):
    request = CreateManagedExecutionRequest(
        managed_execution_creation_params=ManagedExecutionCreationParams(
            managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER,
            brokerage=Brokerage.ETRADE,
            account_id=ACCOUNT_ID,
            creation_order=demo_order(),
        )
    )

    with httpx.Client(timeout=20) as client:
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

    assert managed_execution_id == "1"
    assert cancel_response.status_code == HttpStatusCode.OK, cancel_response.text
    body = cancel_response.json()
    assert body["managed_execution"]["brokerage"] == "etrade"
    assert body["managed_execution"]["account_id"] == ACCOUNT_ID
    assert body["managed_execution"]["current_brokerage_order_id"] == ORDER_ID
