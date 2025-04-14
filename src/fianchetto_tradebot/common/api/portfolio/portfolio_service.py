from abc import ABC

from fianchetto_tradebot.common.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common.exchange.connector import Connector


class PortfolioService(ABC):

    def __init__(self, connector: Connector):
        self.connector = connector

    def list_portfolios(self):
        pass

    def get_portfolio_info(self, get_portfolio_request: GetPortfolioRequest, exchange_specific_options: dict[str, str]):
        pass
