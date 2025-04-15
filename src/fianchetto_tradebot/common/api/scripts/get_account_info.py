import configparser
import os
import sys

import pytest

from fianchetto_tradebot.common.account.account import Account
from fianchetto_tradebot.common.api.accounts.account_service import AccountService
from fianchetto_tradebot.common.api.accounts.etrade.etrade_account_service import ETradeAccountService
from fianchetto_tradebot.common.api.accounts.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common.api.accounts.get_account_info_request import GetAccountInfoRequest
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
"""
NOTE - To test in real life, it's necessary to include an `integration_test_properties.ini` file.
This file is in .gitignore, so as to not leak anyone's sensitive info when they commit code back.

An example is provided in `integration_test_properties.example.ini`.
"""

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'integration_test_properties.ini')
ACCOUNT_ID = 'ACCOUNT_ID'
ACCOUNT_ID_KEY = 'ACCOUNT_ID_KEY'

config = configparser.ConfigParser()

@pytest.fixture
def account_service()->AccountService:
    config.read(CONFIG_FILE)
    connector: ETradeConnector = ETradeConnector()

    return ETradeAccountService(connector)

def test_list_accounts(account_service: AccountService):
    accounts: list[Account] = account_service.list_accounts().get_account_list()
    print(accounts)

def test_get_account_info(account_service: AccountService):
    account_id_key: str = config['ETRADE'][ACCOUNT_ID_KEY]
    account: Account = account_service.get_account_info(GetAccountInfoRequest(account_id_key)).account
    print(account)

def test_get_account_balance(account_service: AccountService):
    account_id_key: str = config['ETRADE'][ACCOUNT_ID_KEY]
    get_balance_request = GetAccountBalanceRequest(account_id_key)
    response = account_service.get_account_balance(get_balance_request)
    print(response.account_balance)


if __name__ == "__main__":
    sys.exit(pytest.main(["-qq"]))