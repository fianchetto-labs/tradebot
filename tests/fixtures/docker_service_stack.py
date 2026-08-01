import os
import time
from collections.abc import Callable

import httpx
import pytest

from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode


ETRADE_SIMULATOR_BASE_URL_ENV_VAR = "TRADEBOT_TEST_ETRADE_SIMULATOR_BASE_URL"
MOEX_BASE_URL_ENV_VAR = "TRADEBOT_TEST_MOEX_BASE_URL"
ORDERS_BASE_URL_ENV_VAR = "TRADEBOT_TEST_ORDERS_BASE_URL"
QUOTES_BASE_URL_ENV_VAR = "TRADEBOT_TEST_QUOTES_BASE_URL"


@pytest.fixture
def etrade_simulator_base_url() -> str:
    return _configured_base_url(
        ETRADE_SIMULATOR_BASE_URL_ENV_VAR,
        "E*Trade simulator service stack tests",
    )


@pytest.fixture
def moex_base_url() -> str:
    return _configured_base_url(MOEX_BASE_URL_ENV_VAR, "MOEX service stack tests")


@pytest.fixture
def orders_base_url() -> str:
    return _configured_base_url(ORDERS_BASE_URL_ENV_VAR, "orders service stack tests")


@pytest.fixture
def quotes_base_url() -> str:
    return _configured_base_url(QUOTES_BASE_URL_ENV_VAR, "quotes service stack tests")


@pytest.fixture
def docker_service_stack() -> "DockerServiceStack":
    return DockerServiceStack()


class DockerServiceStack:
    def reset_etrade_simulator(
        self,
        client: httpx.Client,
        etrade_simulator_base_url: str,
    ) -> None:
        response = client.post(f"{etrade_simulator_base_url}/_simulator/reset")
        assert response.status_code == HttpStatusCode.OK, response.text

    def set_etrade_order_lifecycle_scenario(
        self,
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

    def wait_for_managed_execution_status(
        self,
        client: httpx.Client,
        moex_base_url: str,
        managed_execution_id: str,
        expected_status: str,
        timeout_seconds: float = 20,
    ) -> dict:
        return self.wait_for_managed_execution(
            client,
            moex_base_url,
            managed_execution_id,
            lambda managed_execution: managed_execution["status"] == expected_status,
            expected_description=expected_status,
            timeout_seconds=timeout_seconds,
        )

    def wait_for_managed_execution(
        self,
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
            response = client.get(
                f"{moex_base_url}/api/v1/managed-executions/{managed_execution_id}"
            )
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


def _configured_base_url(env_var: str, test_description: str) -> str:
    base_url = os.getenv(env_var)
    if not base_url:
        pytest.skip(f"set {env_var} to run {test_description}")
    return base_url.rstrip("/")
