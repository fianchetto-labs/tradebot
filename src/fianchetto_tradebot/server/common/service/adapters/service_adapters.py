from dataclasses import dataclass

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.service.ports import OrderServicePort, QuoteServicePort


@dataclass(frozen=True)
class ServiceAdapters:
    order_services: dict[Brokerage, OrderServicePort]
    quote_services: dict[Brokerage, QuoteServicePort]
