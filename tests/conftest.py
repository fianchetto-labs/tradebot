import os

import pytest


SERVICE_TEST_ENV_VAR = "TRADEBOT_RUN_SERVICE_TESTS"


def pytest_collection_modifyitems(config, items):
    if os.getenv(SERVICE_TEST_ENV_VAR) == "1":
        return

    skip_service_test = pytest.mark.skip(
        reason=f"set {SERVICE_TEST_ENV_VAR}=1 to run service or Docker tests"
    )
    for item in items:
        if item.get_closest_marker("service") or item.get_closest_marker("docker"):
            item.add_marker(skip_service_test)
