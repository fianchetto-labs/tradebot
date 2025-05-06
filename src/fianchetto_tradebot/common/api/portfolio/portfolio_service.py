from fianchetto_tradebot.common.api.api_service import ApiService
from fianchetto_tradebot.common.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common.brokerage.connector import Connector


class PortfolioService(ApiService):
    def __init__(self, connector: Connector):
        super().__init__(connector)

    def get_portfolio_info(self, get_portfolio_request: GetPortfolioRequest, brokerage_specific_options: dict[str, str]):
        pass
