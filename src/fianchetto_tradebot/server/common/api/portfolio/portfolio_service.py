from fianchetto_tradebot.server.common.api.api_service import ApiService
from fianchetto_tradebot.common_models.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.server.common.brokerage.connector import Connector


class PortfolioService(ApiService):
    def __init__(self, connector: Connector):
        super().__init__(connector)

    def get_portfolio_info(self, get_portfolio_request: GetPortfolioRequest, brokerage_specific_options: dict[str, str]):
        pass
