from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService
from tests.common.util.test_object_util import get_sample_equity, get_sample_option

if __name__ == "__main__":
    connector: ETradeConnector = ETradeConnector()

    equity: Equity = get_sample_equity()
    option: Option = get_sample_option()
    equity_request: GetTradableRequest = GetTradableRequest(tradable=equity)
    option_request: GetTradableRequest = GetTradableRequest(tradable=option)

    q: QuotesService = ETradeQuotesService(connector)
    equity_response: GetTradableResponse = q.get_tradable_quote(equity_request)

    option_response: GetTradableResponse = q.get_tradable_quote(option_request)

    print(option_response)