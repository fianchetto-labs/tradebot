import configparser
import os

from fianchetto_tradebot.common.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common.api.portfolio.get_portfolio_response import GetPortfolioResponse
from fianchetto_tradebot.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.quotes.etrade.etrade_quote_service import ETradeQuoteService
from fianchetto_tradebot.quotes.quote_service import QuoteService

"""
NOTE - To test in real life, it's necessary to include an `integration_test_properties.ini` file.
This file is in .gitignore, so as to not leak anyone's sensitive info when they commit code back.

An example is provided in `integration_test_properties.example.ini`.
"""

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'integration_test_properties.ini')
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

config = configparser.ConfigParser()

if __name__ == "__main__":
    config.read(CONFIG_FILE)

    connector: ETradeConnector = ETradeConnector()
    q: QuoteService = ETradeQuoteService(connector)

    portfolio_service: ETradePortfolioService = ETradePortfolioService(connector)

    account_id_key = config['ETRADE'][ACCOUNT_ID_KEY]
    portfolio_request: GetPortfolioRequest = GetPortfolioRequest(account_id_key)
    get_portfolio_response: GetPortfolioResponse = portfolio_service.get_portfolio_info(portfolio_request)

    portfolio = get_portfolio_response.portfolio

    print(portfolio)