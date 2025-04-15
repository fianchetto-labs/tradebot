from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from tests.common.util.test_object_util import get_sample_equity, get_sample_option
from fianchetto_tradebot.quotes.api.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.quotes.api.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.quotes.etrade.etrade_quote_service import ETradeQuoteService
from fianchetto_tradebot.quotes.quote_service import QuoteService

if __name__ == "__main__":
    connector: ETradeConnector = ETradeConnector()

    equity: Equity = get_sample_equity()
    option: Option = get_sample_option()
    equity_request: GetTradableRequest = GetTradableRequest(tradable=equity)
    option_request: GetTradableRequest = GetTradableRequest(tradable=option)

    q: QuoteService = ETradeQuoteService(connector)
    equity_response: GetTradableResponse = q.get_tradable_quote(equity_request)

    option_response: GetTradableResponse = q.get_tradable_quote(option_request)

    print(option_response)