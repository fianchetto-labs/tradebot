from flask import jsonify

from fianchetto_tradebot.common.api.accounts.account_list_response import AccountListResponse
from fianchetto_tradebot.common.api.accounts.account_service import AccountService
from fianchetto_tradebot.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.common.api.accounts.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common.api.accounts.get_account_balance_response import GetAccountBalanceResponse
from fianchetto_tradebot.common.api.accounts.get_account_info_request import GetAccountInfoRequest
from fianchetto_tradebot.common.api.accounts.get_account_info_response import GetAccountInfoResponse
from fianchetto_tradebot.common.api.portfolio.etrade_portfolio_service import ETradePortfolioService
from fianchetto_tradebot.common.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common.api.portfolio.get_portfolio_response import GetPortfolioResponse
from fianchetto_tradebot.common.api.portfolio.portfolio_service import PortfolioService
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.exchange.exchange_name import ExchangeName
from fianchetto_tradebot.common.service.rest_service import RestService, ETRADE_ONLY_EXCHANGE_CONFIG
from fianchetto_tradebot.common.service.service_key import ServiceKey
from fianchetto_tradebot.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.quotes.quotes_service import QuotesService


class QuotesRestService(RestService):
    def __init__(self, credential_config_files: dict[ExchangeName, str]=ETRADE_ONLY_EXCHANGE_CONFIG):
        super().__init__(ServiceKey.QUOTES, credential_config_files)

    def _register_endpoints(self):
        super()._register_endpoints()

        # Account endpoints
        self.app.add_url_rule(rule='/api/v1/<exchange>/accounts', endpoint='list-accounts',
                              view_func=self.list_accounts, methods=['GET'])
        self.app.add_url_rule(rule='/api/v1/<exchange>/accounts/<account_id>', endpoint='get-account',
                              view_func=self.get_account, methods=['GET'])

        self.app.add_url_rule(rule='/api/v1/<exchange>/accounts/<account_id>/balance', endpoint='get-account-balance',
                              view_func=self.get_account_balance, methods=['GET'])

        self.app.add_url_rule(rule='/api/v1/<exchange>/accounts/<account_id>/portfolio', endpoint='get-account-portfolio',
                              view_func=self.get_account_portfolio, methods=['GET'])


    def list_accounts(self, exchange:str):
        account_service: AccountService = self.account_services[ExchangeName[exchange.upper()]]
        account_list_response: AccountListResponse = account_service.list_accounts()

        return jsonify(account_list_response)


    def get_account(self, exchange:str, account_id: str):
        account_service: AccountService = self.account_services[ExchangeName[exchange.upper()]]
        get_account_info_request: GetAccountInfoRequest = GetAccountInfoRequest(account_id)
        get_account_response: GetAccountInfoResponse = account_service.get_account_info(get_account_info_request)

        return jsonify(get_account_response)

    def get_account_balance(self, exchange:str, account_id: str):
        account_service: AccountService = self.account_services[ExchangeName[exchange.upper()]]
        get_account_balance_request: GetAccountBalanceRequest = GetAccountBalanceRequest(account_id)
        get_account_balance_response: GetAccountBalanceResponse = account_service.get_account_balance(get_account_balance_request)

        return jsonify(get_account_balance_response)

    def get_account_portfolio(self, exchange:str, account_id: str):
        # TODO - get exchange-specific options that are now part of the defaults. This is tricky b/c normally we'd want to
        # wrap it up into an object, but for GET requests, we can't have a serialized body
        portfolio_service: PortfolioService = self.portfolio_services[ExchangeName[exchange.upper()]]
        get_portfolio_request: GetPortfolioRequest = GetPortfolioRequest(account_id)
        get_portfolio_response: GetPortfolioResponse = portfolio_service.get_portfolio_info(get_portfolio_request)

        return jsonify(get_portfolio_response)

    def _setup_exchange_services(self):
        # Delegated to subclass
        self.quotes_services: dict[ExchangeName, QuotesService] = dict()
        self.portfolio_services: dict[ExchangeName, PortfolioService] = dict()
        self.account_services: dict[ExchangeName, AccountService] = dict()

        # E*Trade
        etrade_key: ExchangeName = ExchangeName.ETRADE
        etrade_connector: ETradeConnector = self.connectors[ExchangeName.ETRADE]

        etrade_quotes_service = ETradeQuotesService(etrade_connector)
        etrade_portfolio_service = ETradePortfolioService(etrade_connector)
        etrade_account_service = ETradeAccountService(etrade_connector)

        self.quotes_services[etrade_key] = etrade_quotes_service
        self.portfolio_services[etrade_key] = etrade_portfolio_service
        self.account_services[etrade_key] = etrade_account_service

        # TODO: Add for Schwab and IKBR
    pass


if __name__ == "__main__":
    # Login To Exchange Here
    oex_app = QuotesRestService()
    oex_app.run(host="0.0.0.0", port=8081)