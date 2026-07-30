from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.simulator.etrade import seed_data


def test_equity_quote_request_sends_explicit_empty_params():
    session = StrictGetSession()
    service = object.__new__(ETradeQuotesService)
    service.session = session
    service.base_url = "http://etrade-simulator:8090"

    response = service.get_tradable_quote(GetTradableRequest(tradable=Equity(ticker="GE")))

    assert session.requested_url == "http://etrade-simulator:8090/v1/market/quote/GE.json"
    assert response.current_price.bid == 100.0
    assert response.current_price.ask == 101.0


class StrictGetSession:
    requested_url: str | None = None

    def get(self, url: str, *, params: dict):
        self.requested_url = url
        assert params == {}
        return QuoteResponse()


class QuoteResponse:
    def json(self):
        return seed_data.quote_response("GE")
