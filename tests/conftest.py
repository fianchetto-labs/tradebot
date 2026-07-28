import os

import pytest


SERVICE_TEST_ENV_VAR = "TRADEBOT_RUN_SERVICE_TESTS"
LIVE_E2E_TEST_ENV_VAR = "TRADEBOT_RUN_LIVE_E2E_TESTS"
SERVICE_GATED_MARKERS = ("service", "docker", "integration")
LIVE_E2E_GATED_MARKERS = ("live_e2e",)


def pytest_collection_modifyitems(config, items):
    skip_service_test = pytest.mark.skip(
        reason=f"set {SERVICE_TEST_ENV_VAR}=1 to run service or Docker tests"
    )
    skip_live_e2e_test = pytest.mark.skip(
        reason=f"set {LIVE_E2E_TEST_ENV_VAR}=1 to run live paper-account E2E tests"
    )

    service_tests_enabled = os.getenv(SERVICE_TEST_ENV_VAR) == "1"
    live_e2e_tests_enabled = os.getenv(LIVE_E2E_TEST_ENV_VAR) == "1"

    for item in items:
        if not live_e2e_tests_enabled and any(
            item.get_closest_marker(marker) for marker in LIVE_E2E_GATED_MARKERS
        ):
            item.add_marker(skip_live_e2e_test)
        if not service_tests_enabled and any(
            item.get_closest_marker(marker) for marker in SERVICE_GATED_MARKERS
        ):
            item.add_marker(skip_service_test)
