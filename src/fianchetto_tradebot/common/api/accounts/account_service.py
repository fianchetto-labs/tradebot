from fianchetto_tradebot.common.api.accounts.list_accounts_response import ListAccountsResponse
from fianchetto_tradebot.common.api.accounts.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common.api.accounts.get_account_balance_response import GetAccountBalanceResponse
from fianchetto_tradebot.common.api.accounts.get_account_request import GetAccountRequest
from fianchetto_tradebot.common.api.accounts.get_account_response import GetAccountResponse
from fianchetto_tradebot.common.api.api_service import ApiService
from fianchetto_tradebot.common.brokerage.connector import Connector


class AccountService(ApiService):
    def __init__(self, connector: Connector):
        super().__init__(connector)
        
    def list_accounts(self) -> ListAccountsResponse:
        pass

    def get_account_info(self, get_account_info_request: GetAccountRequest) -> GetAccountResponse:
        pass

    def get_account_balance(self, get_account_balance_request: GetAccountBalanceRequest)-> GetAccountBalanceResponse:
        pass

