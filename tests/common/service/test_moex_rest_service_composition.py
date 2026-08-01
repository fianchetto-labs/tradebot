import logging

import pytest

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_request import (
    GetManagedExecutionRequest,
)
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_response import (
    GetManagedExecutionResponse,
)
from fianchetto_tradebot.server.common.service.adapters import (
    HttpServiceAdapterConfigurationError,
    ORDERS_SERVICE_URL_ENV_VAR,
    QUOTES_SERVICE_URL_ENV_VAR,
    ServiceAdapters,
)
from fianchetto_tradebot.server.moex.serving import moex_rest_service
from fianchetto_tradebot.server.moex.serving.moex_rest_service import (
    HTTP_SERVICE_ADAPTER_MODE,
    LOCAL_SERVICE_ADAPTER_MODE,
    MOEX_SERVICE_ADAPTER_MODE_ENV_VAR,
    MoexRestService,
)


class _FakeConnector:
    pass


class _FakeMoexService:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def get_managed_execution(self, request):
        self.requests.append(request)
        return self.response


def test_moex_service_uses_local_adapters_by_default(monkeypatch, caplog):
    service = object.__new__(MoexRestService)
    service.connectors = {Brokerage.ETRADE: _FakeConnector()}
    expected_adapters = ServiceAdapters(order_services={}, quote_services={})
    calls = []

    def build_local_service_adapters(connectors):
        calls.append(connectors)
        return expected_adapters

    monkeypatch.setattr(
        moex_rest_service,
        "build_local_service_adapters",
        build_local_service_adapters,
    )

    with caplog.at_level(logging.INFO, logger=moex_rest_service.__name__):
        assert service._build_service_adapters(env={}) is expected_adapters

    assert calls == [service.connectors]
    assert "local mode" in caplog.text


def test_moex_service_can_use_http_adapters_from_environment(monkeypatch, caplog):
    service = object.__new__(MoexRestService)
    service.connectors = {Brokerage.ETRADE: _FakeConnector()}
    expected_adapters = ServiceAdapters(order_services={}, quote_services={})
    calls = []
    env = {
        MOEX_SERVICE_ADAPTER_MODE_ENV_VAR: HTTP_SERVICE_ADAPTER_MODE,
        ORDERS_SERVICE_URL_ENV_VAR: "http://orders:8080",
        QUOTES_SERVICE_URL_ENV_VAR: "http://quotes:8081",
    }

    def build_http_service_adapters(brokerages, config):
        calls.append((list(brokerages), config))
        return expected_adapters

    monkeypatch.setattr(
        moex_rest_service,
        "build_http_service_adapters",
        build_http_service_adapters,
    )

    with caplog.at_level(logging.INFO, logger=moex_rest_service.__name__):
        assert service._build_service_adapters(env=env) is expected_adapters

    brokerages, config = calls[0]
    assert brokerages == [Brokerage.ETRADE]
    assert config.orders_base_url == "http://orders:8080"
    assert config.quotes_base_url == "http://quotes:8081"
    assert "http mode" in caplog.text


def test_moex_service_rejects_http_mode_without_explicit_service_urls():
    service = object.__new__(MoexRestService)
    service.connectors = {Brokerage.ETRADE: _FakeConnector()}

    with pytest.raises(HttpServiceAdapterConfigurationError) as exc_info:
        service._build_service_adapters(env={MOEX_SERVICE_ADAPTER_MODE_ENV_VAR: HTTP_SERVICE_ADAPTER_MODE})

    message = str(exc_info.value)
    assert ORDERS_SERVICE_URL_ENV_VAR in message
    assert QUOTES_SERVICE_URL_ENV_VAR in message
    assert "local mode" in message


def test_moex_service_rejects_unknown_adapter_mode():
    service = object.__new__(MoexRestService)
    service.connectors = {Brokerage.ETRADE: _FakeConnector()}

    try:
        service._build_service_adapters(env={MOEX_SERVICE_ADAPTER_MODE_ENV_VAR: "sideways"})
    except ValueError as exc:
        assert MOEX_SERVICE_ADAPTER_MODE_ENV_VAR in str(exc)
        assert LOCAL_SERVICE_ADAPTER_MODE in str(exc)
        assert HTTP_SERVICE_ADAPTER_MODE in str(exc)
    else:
        raise AssertionError("Expected unknown MOEX adapter mode to be rejected")


def test_moex_rest_get_managed_execution_returns_service_response():
    service = object.__new__(MoexRestService)
    expected_response = GetManagedExecutionResponse()
    service.moex_service = _FakeMoexService(expected_response)

    response = service.get_managed_execution("moex-1")

    assert response is expected_response
    assert service.moex_service.requests == [
        GetManagedExecutionRequest(managed_execution_id="moex-1")
    ]
