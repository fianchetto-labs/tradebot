from typing import Protocol, runtime_checkable

from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse


@runtime_checkable
class QuoteServicePort(Protocol):
    """Quote dependency surface required by managed execution services."""

    def get_tradable_quote(self, request: GetTradableRequest) -> GetTradableResponse:
        ...
