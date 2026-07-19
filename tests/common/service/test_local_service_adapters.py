from unittest.mock import Mock

import pytest

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.brokerage.connector import Connector
from fianchetto_tradebot.server.common.service.adapters import (
    LocalOrderServiceAdapter,
    LocalQuoteServiceAdapter,
    build_local_service_adapters,
)
from fianchetto_tradebot.server.common.service.ports import OrderServicePort, QuoteServicePort


class FakeConnector(Connector):
    brokerage = "ETRADE"

    def load_connection(self):
        return Mock(), Mock(), "https://local.test"


def test_local_order_adapter_delegates_to_wrapped_service():
    service = Mock()
    adapter = LocalOrderServiceAdapter(service)

    get_order_request = object()
    get_order_response = object()
    service.get_order.return_value = get_order_response
    assert adapter.get_order(get_order_request) is get_order_response
    service.get_order.assert_called_once_with(get_order_request)

    cancel_order_request = object()
    cancel_order_response = object()
    service.cancel_order.return_value = cancel_order_response
    assert adapter.cancel_order(cancel_order_request) is cancel_order_response
    service.cancel_order.assert_called_once_with(cancel_order_request)

    preview_order_request = object()
    place_order_response = object()
    service.preview_and_place_order.return_value = place_order_response
    assert adapter.preview_and_place_order(preview_order_request) is place_order_response
    service.preview_and_place_order.assert_called_once_with(preview_order_request)

    preview_modify_order_request = object()
    modify_order_response = object()
    service.modify_order.return_value = modify_order_response
    assert adapter.modify_order(preview_modify_order_request) is modify_order_response
    service.modify_order.assert_called_once_with(preview_modify_order_request)


def test_local_quote_adapter_delegates_to_wrapped_service():
    service = Mock()
    adapter = LocalQuoteServiceAdapter(service)

    request = object()
    response = object()
    service.get_tradable_quote.return_value = response

    assert adapter.get_tradable_quote(request) is response
    service.get_tradable_quote.assert_called_once_with(request)


def test_build_local_service_adapters_creates_etrade_port_adapters():
    local_services = build_local_service_adapters({Brokerage.ETRADE: FakeConnector()})

    order_service = local_services.order_services[Brokerage.ETRADE]
    quote_service = local_services.quote_services[Brokerage.ETRADE]

    assert isinstance(order_service, LocalOrderServiceAdapter)
    assert isinstance(order_service, OrderServicePort)
    assert isinstance(quote_service, LocalQuoteServiceAdapter)
    assert isinstance(quote_service, QuoteServicePort)


def test_build_local_service_adapters_rejects_unsupported_brokerage():
    with pytest.raises(NotImplementedError, match="Local service adapters are not implemented"):
        build_local_service_adapters({Brokerage.IBKR: FakeConnector()})
