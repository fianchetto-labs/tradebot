from collections.abc import Iterable

import httpx

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.service.adapters.http_order_service_adapter import HttpOrderServiceAdapter
from fianchetto_tradebot.server.common.service.adapters.http_quote_service_adapter import HttpQuoteServiceAdapter
from fianchetto_tradebot.server.common.service.adapters.http_service_adapter_config import (
    HttpServiceAdapterConfig,
    load_http_service_adapter_config,
)
from fianchetto_tradebot.server.common.service.adapters.service_adapters import ServiceAdapters
from fianchetto_tradebot.server.common.service.ports import OrderServicePort, QuoteServicePort


def build_http_service_adapters(
        brokerages: Iterable[Brokerage],
        config: HttpServiceAdapterConfig | None = None,
        orders_client: httpx.Client | None = None,
        quotes_client: httpx.Client | None = None,
) -> ServiceAdapters:
    config = config or load_http_service_adapter_config()
    order_services: dict[Brokerage, OrderServicePort] = dict()
    quote_services: dict[Brokerage, QuoteServicePort] = dict()

    for brokerage in brokerages:
        order_services[brokerage] = HttpOrderServiceAdapter(
            brokerage=brokerage,
            orders_base_url=config.orders_base_url,
            client=orders_client,
        )
        quote_services[brokerage] = HttpQuoteServiceAdapter(
            brokerage=brokerage,
            quotes_base_url=config.quotes_base_url,
            client=quotes_client,
        )

    return ServiceAdapters(order_services=order_services, quote_services=quote_services)
