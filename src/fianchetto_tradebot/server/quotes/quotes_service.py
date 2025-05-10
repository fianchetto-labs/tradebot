from fianchetto_tradebot.server.common.api.api_service import ApiService
from fianchetto_tradebot.server.common.brokerage.connector import Connector
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.api.quotes.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.common_models.api.quotes.get_option_expire_dates_response import GetOptionExpireDatesResponse
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse


class QuotesService(ApiService):
    def __init__(self, connector: Connector):
        super().__init__(connector)

    def get_tradable_quote(self, request: GetTradableRequest) -> GetTradableResponse:
        pass

    def get_option_expire_dates(self, get_options_expire_dates_request: GetOptionExpireDatesRequest) -> GetOptionExpireDatesResponse:
        pass

    def get_equity_quote(self, symbol: str):
        pass

    def get_options_chain(self, get_options_chain_request: GetOptionsChainRequest) -> GetOptionsChainResponse:
        pass

    def get_option_details(self, option: Option):
        pass

