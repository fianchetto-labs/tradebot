from dateutil.parser import parse

from fianchetto_tradebot.common.api.accounts.list_accounts_response import ListAccountsResponse
from fianchetto_tradebot.common.api.accounts.account_service import AccountService
from fianchetto_tradebot.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.common.api.accounts.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common.api.accounts.get_account_balance_response import GetAccountBalanceResponse
from fianchetto_tradebot.common.api.accounts.get_account_request import GetAccountRequest
from fianchetto_tradebot.common.api.accounts.get_account_response import GetAccountResponse
from fianchetto_tradebot.common.api.encoding.custom_json_provider import CustomJSONProvider
from fianchetto_tradebot.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.common.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common.api.portfolio.get_portfolio_response import GetPortfolioResponse
from fianchetto_tradebot.common.api.portfolio.portfolio_service import PortfolioService
from fianchetto_tradebot.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.service.rest_service import RestService, ETRADE_ONLY_BROKERAGE_CONFIG
from fianchetto_tradebot.common.service.service_key import ServiceKey
from fianchetto_tradebot.quotes.api.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.quotes.api.get_option_expire_dates_response import GetOptionExpireDatesResponse
from fianchetto_tradebot.quotes.api.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.quotes.api.get_options_chain_response import GetOptionsChainResponse
from fianchetto_tradebot.quotes.api.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.quotes.api.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.quotes.quotes_service import QuotesService


class QuotesRestService(RestService):
    def __init__(self, credential_config_files: dict[Brokerage, str]=ETRADE_ONLY_BROKERAGE_CONFIG):
        super().__init__(ServiceKey.QUOTES, credential_config_files)

    def _register_endpoints(self):
        super()._register_endpoints()

        # Account endpoints
        self.app.add_api_route(path='/api/v1/{brokerage}/accounts', endpoint=self.list_accounts, methods=['GET'], response_model=ListAccountsResponse)
        self.app.add_api_route(path='/api/v1/{brokerage}/accounts/{account_id}', endpoint=self.get_account, methods=['GET'], response_model=GetAccountResponse)
        self.app.add_api_route(path='/api/v1/{brokerage}/accounts/{account_id}/balance', endpoint=self.get_account_balance, methods=['GET'], response_model=GetAccountBalanceResponse)

        # Portfolio Endpoints
        self.app.add_api_route(path='/api/v1/{brokerage}/accounts/{account_id}/portfolio', endpoint=self.get_account_portfolio, methods=['GET'], response_model=GetPortfolioResponse)

        # Quotes Endpoints
        self.app.add_api_route(path='/api/v1/{brokerage}/quotes/equity/{equity}', endpoint=self.get_equity_quote, methods=['GET'])
        self.app.add_api_route(path='/api/v1/{brokerage}/quotes/equity/{equity}/options_chain', endpoint=self.get_options_chain, methods=['GET'])
        self.app.add_api_route(path='/api/v1/{brokerage}/quotes/equity/{equity}/options_chain/expiry', endpoint=self.get_options_chain_expiries, methods=['GET'])
        self.app.add_api_route(path='/api/v1/{brokerage}/quotes/equity/{equity}/options_chain/expiry/{expiry}', endpoint=self.get_options_chain_by_expiry, methods=['GET'])


        # TODO - add more granular endpoints for options by expiry, strike, etc


    def list_accounts(self, brokerage:str):
        account_service: AccountService = self.account_services[Brokerage[brokerage.upper()]]
        account_list_response: ListAccountsResponse = account_service.list_accounts()

        return account_list_response

    def get_account(self, brokerage:str, account_id: str):
        account_service: AccountService = self.account_services[Brokerage[brokerage.upper()]]
        get_account_info_request: GetAccountRequest = GetAccountRequest(account_id=account_id)
        get_account_response: GetAccountResponse = account_service.get_account_info(get_account_info_request)

        return get_account_response

    def get_account_balance(self, brokerage:str, account_id: str):
        account_service: AccountService = self.account_services[Brokerage[brokerage.upper()]]
        get_account_balance_request: GetAccountBalanceRequest = GetAccountBalanceRequest(account_id=account_id)
        get_account_balance_response: GetAccountBalanceResponse = account_service.get_account_balance(get_account_balance_request)

        return get_account_balance_response

    def get_account_portfolio(self, brokerage:str, account_id: str):
        # TODO - get brokerage-specific options that are now part of the defaults. This is tricky b/c normally we'd want to
        # wrap it up into an object, but for GET requests, we can't have a serialized body
        portfolio_service: PortfolioService = self.portfolio_services[Brokerage[brokerage.upper()]]
        get_portfolio_request: GetPortfolioRequest = GetPortfolioRequest(account_id)
        get_portfolio_response: GetPortfolioResponse = portfolio_service.get_portfolio_info(get_portfolio_request)

        return get_portfolio_response

    def get_equity_quote(self, brokerage, equity):
        quotes_service: QuotesService = self.quotes_services[Brokerage[brokerage.upper()]]
        tradable: Tradable = Equity(ticker=equity)
        tradeable_request: GetTradableRequest = GetTradableRequest(tradable=tradable)
        get_tradable_response: GetTradableResponse = quotes_service.get_tradable_quote(tradeable_request)

        return get_tradable_response

    def get_options_chain(self, brokerage, equity):
        quotes_service: QuotesService = self.quotes_services[Brokerage[brokerage.upper()]]

        get_options_chain_request: GetOptionsChainRequest = GetOptionsChainRequest(ticker=equity)
        get_option_chain_response: GetOptionsChainResponse = quotes_service.get_options_chain(get_options_chain_request)

        with_stringified_keys = CustomJSONProvider.stringify_keys(get_option_chain_response.options_chain)
        return with_stringified_keys

    def get_options_chain_expiries(self, brokerage, equity):
        quotes_service: QuotesService = self.quotes_services[Brokerage[brokerage.upper()]]

        # TODO: Need to define a good format for expiry values
        expiry_request: GetOptionExpireDatesRequest = GetOptionExpireDatesRequest(ticker=equity)
        get_option_expiries_response: GetOptionExpireDatesResponse = quotes_service.get_option_expire_dates(expiry_request)

        return get_option_expiries_response

    def get_options_chain_by_expiry(self, brokerage, equity, expiry):
        quotes_service: QuotesService = self.quotes_services[Brokerage[brokerage.upper()]]

        # Document for format in which to get this (yyyy_mm_dd)
        expiry_date = parse(expiry)

        get_options_chain_request: GetOptionsChainRequest = GetOptionsChainRequest(ticker=equity, expiry=expiry_date)
        get_options_chain_response: GetOptionsChainResponse = quotes_service.get_options_chain(get_options_chain_request)

        with_stringified_keys = CustomJSONProvider.stringify_keys(get_options_chain_response)
        return with_stringified_keys

    def _setup_brokerage_services(self):
        # Delegated to subclass
        self.quotes_services: dict[Brokerage, QuotesService] = dict()
        self.portfolio_services: dict[Brokerage, PortfolioService] = dict()
        self.account_services: dict[Brokerage, AccountService] = dict()

        # E*Trade
        etrade_key: Brokerage = Brokerage.ETRADE
        etrade_connector: ETradeConnector = self.connectors[Brokerage.ETRADE]

        etrade_quotes_service = ETradeQuotesService(etrade_connector)
        etrade_portfolio_service = ETradePortfolioService(etrade_connector)
        etrade_account_service = ETradeAccountService(etrade_connector)

        self.quotes_services[etrade_key] = etrade_quotes_service
        self.portfolio_services[etrade_key] = etrade_portfolio_service
        self.account_services[etrade_key] = etrade_account_service

        # TODO: Add for Schwab and IKBR


if __name__ == "__main__":
    oex_app = QuotesRestService()
    oex_app.run(host="0.0.0.0", port=8081)