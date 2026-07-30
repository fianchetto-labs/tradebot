from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.service.adapters import ServiceAdapters
from fianchetto_tradebot.server.moex.serving import moex_rest_service
from fianchetto_tradebot.server.moex.serving.moex_rest_service import (
    HTTP_SERVICE_ADAPTER_MODE,
    LOCAL_SERVICE_ADAPTER_MODE,
    MOEX_SERVICE_ADAPTER_MODE_ENV_VAR,
    MoexRestService,
)


class _FakeConnector:
    pass


def test_moex_service_uses_local_adapters_by_default(monkeypatch):
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

    assert service._build_service_adapters(env={}) is expected_adapters
    assert calls == [service.connectors]


def test_moex_service_can_use_http_adapters_from_environment(monkeypatch):
    service = object.__new__(MoexRestService)
    service.connectors = {Brokerage.ETRADE: _FakeConnector()}
    expected_adapters = ServiceAdapters(order_services={}, quote_services={})
    calls = []
    env = {
        MOEX_SERVICE_ADAPTER_MODE_ENV_VAR: HTTP_SERVICE_ADAPTER_MODE,
        "TRADEBOT_ORDERS_SERVICE_URL": "http://orders:8080",
        "TRADEBOT_QUOTES_SERVICE_URL": "http://quotes:8081",
    }

    def build_http_service_adapters(brokerages, config):
        calls.append((list(brokerages), config))
        return expected_adapters

    monkeypatch.setattr(
        moex_rest_service,
        "build_http_service_adapters",
        build_http_service_adapters,
    )

    assert service._build_service_adapters(env=env) is expected_adapters

    brokerages, config = calls[0]
    assert brokerages == [Brokerage.ETRADE]
    assert config.orders_base_url == "http://orders:8080"
    assert config.quotes_base_url == "http://quotes:8081"


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
