from dataclasses import dataclass
from typing import cast

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.brokerage.connector import Connector
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.server.common.service.adapters.local_order_service_adapter import LocalOrderServiceAdapter
from fianchetto_tradebot.server.common.service.adapters.local_quote_service_adapter import LocalQuoteServiceAdapter
from fianchetto_tradebot.server.common.service.ports import OrderServicePort, QuoteServicePort
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService


@dataclass(frozen=True)
class LocalServiceAdapters:
    order_services: dict[Brokerage, OrderServicePort]
    quote_services: dict[Brokerage, QuoteServicePort]


def build_local_service_adapters(connectors: dict[Brokerage, Connector]) -> LocalServiceAdapters:
    order_services: dict[Brokerage, OrderServicePort] = dict()
    quote_services: dict[Brokerage, QuoteServicePort] = dict()

    for brokerage, connector in connectors.items():
        if brokerage == Brokerage.ETRADE:
            etrade_connector = cast(ETradeConnector, connector)
            order_services[brokerage] = LocalOrderServiceAdapter(ETradeOrderService(etrade_connector))
            quote_services[brokerage] = LocalQuoteServiceAdapter(ETradeQuotesService(etrade_connector))
        else:
            raise NotImplementedError(f"Local service adapters are not implemented for {brokerage}")

    return LocalServiceAdapters(order_services=order_services, quote_services=quote_services)
