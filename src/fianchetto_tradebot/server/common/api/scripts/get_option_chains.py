import configparser
import datetime
import os

import pytest

from fianchetto_tradebot.common_models.api.quotes.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.api.quotes.get_option_expire_dates_response import GetOptionExpireDatesResponse
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

"""
NOTE - To test in real life, it's necessary to include an `integration_test_properties.ini` file.
This file is in .gitignore, so as to not leak anyone's sensitive info when they commit code back.

An example is provided in `integration_test_properties.example.ini`.
"""

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'integration_test_properties.ini')
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

ticker = "SPY"
equity_name = "SPDR S&P 500 ETF TRUST"

equity: Equity = Equity(ticker, equity_name)

config = configparser.ConfigParser()

@pytest.fixture
def q():
    config.read(CONFIG_FILE)

    connector: ETradeConnector = ETradeConnector()
    return ETradeQuotesService(connector)

def test_option_expirations(q: QuotesService):
    req: GetOptionExpireDatesRequest = GetOptionExpireDatesRequest(ticker=ticker)
    resp: GetOptionExpireDatesResponse = q.get_option_expire_dates(req)

    print(resp.expire_dates)

def test_options_chains(q: QuotesService):

    expiry = datetime.datetime(2025, 3, 21).date()

    options_chain_request_for_date: GetOptionsChainRequest = GetOptionsChainRequest(equity, expiry)
    options_chain_request_no_expiry: GetOptionsChainRequest = GetOptionsChainRequest(equity, None)

    get_options_chain_response: GetOptionsChainResponse = q.get_options_chain(options_chain_request_for_date)
    options_chain = get_options_chain_response.options_chain
    print(options_chain)

    # If no date is provided, it will default to today's date. May possible default to the next closing date.
    get_options_chain_response_no_expiry: GetOptionsChainResponse = q.get_options_chain(options_chain_request_no_expiry)
    options_chain_no_expiry = get_options_chain_response_no_expiry.options_chain
    print(options_chain_no_expiry)