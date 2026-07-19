from urllib.parse import quote

import httpx

from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.tradable import Tradable
from fianchetto_tradebot.server.common.service.adapters.http_service_adapter import HttpServiceAdapter
from fianchetto_tradebot.server.common.service.ports import QuoteServicePort


class HttpQuoteServiceAdapter(HttpServiceAdapter, QuoteServicePort):
    def __init__(self, brokerage: Brokerage, quotes_base_url: str, client: httpx.Client | None = None):
        super().__init__(quotes_base_url, client)
        self.brokerage = brokerage

    def get_tradable_quote(self, request: GetTradableRequest) -> GetTradableResponse:
        symbol = self._tradable_symbol(request.tradable)
        encoded_symbol = quote(symbol, safe="")
        response = self._request(
            "GET",
            f"/api/v1/{self.brokerage.value}/quotes/tradable/{encoded_symbol}",
        )
        return GetTradableResponse.model_validate(response.json())

    @staticmethod
    def _tradable_symbol(tradable: Tradable) -> str:
        if isinstance(tradable, Equity):
            return tradable.ticker

        if isinstance(tradable, Option):
            expiry = tradable.expiry
            return (
                f"{tradable.equity.ticker}:{expiry.year}:{expiry.month}:{expiry.day}:"
                f"{tradable.type.value}:{tradable.strike.to_float()}"
            )

        raise ValueError(f"Tradable type {type(tradable)} is not supported by HTTP quote adapter")
