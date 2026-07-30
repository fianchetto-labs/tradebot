import os

import httpx
import pytest


pytestmark = [pytest.mark.service, pytest.mark.docker, pytest.mark.integration]

QUOTES_BASE_URL_ENV_VAR = "TRADEBOT_TEST_QUOTES_BASE_URL"


@pytest.fixture
def quotes_base_url() -> str:
    base_url = os.getenv(QUOTES_BASE_URL_ENV_VAR)
    if not base_url:
        pytest.skip(f"set {QUOTES_BASE_URL_ENV_VAR} to run quotes service stack tests")
    return base_url.rstrip("/")


def test_quotes_service_returns_simulator_backed_equity_quote(quotes_base_url: str):
    with httpx.Client(timeout=5) as client:
        health_response = client.get(f"{quotes_base_url}/health-check")
        quote_response = client.get(f"{quotes_base_url}/api/v1/ETRADE/quotes/tradable/GE")

    assert health_response.status_code == 200
    assert health_response.json() == "QUOTES Service Up"

    assert quote_response.status_code == 200
    body = quote_response.json()
    assert body["tradable"]["ticker"] == "GE"
    assert body["current_price"]["bid"] == 100.0
    assert body["current_price"]["ask"] == 101.0
    assert body["current_price"]["mark"] == 100.5
    assert body["volume"] == 1000
