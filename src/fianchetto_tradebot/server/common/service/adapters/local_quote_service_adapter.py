from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.server.common.service.ports import QuoteServicePort


class LocalQuoteServiceAdapter(QuoteServicePort):
    def __init__(self, service: QuoteServicePort):
        self.service = service

    def get_tradable_quote(self, request: GetTradableRequest) -> GetTradableResponse:
        return self.service.get_tradable_quote(request)
