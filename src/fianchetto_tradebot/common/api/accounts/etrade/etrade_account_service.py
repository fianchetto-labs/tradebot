from datetime import datetime

from fianchetto_tradebot.common.account.account import Account
from fianchetto_tradebot.common.account.account_balance import AccountBalance
from fianchetto_tradebot.common.account.brokerage_call import BrokerageCallType, BrokerageCall
from fianchetto_tradebot.common.account.computed_balance import ComputedBalance
from fianchetto_tradebot.common.account.etrade.etrade_account import ETradeAccount
from fianchetto_tradebot.common.api.accounts.account_list_response import AccountListResponse
from fianchetto_tradebot.common.api.accounts.account_service import AccountService
from fianchetto_tradebot.common.api.accounts.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common.api.accounts.get_account_balance_response import GetAccountBalanceResponse
from fianchetto_tradebot.common.api.accounts.get_account_info_request import GetAccountInfoRequest
from fianchetto_tradebot.common.api.accounts.get_account_info_response import GetAccountInfoResponse
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount

DEFAULT_INST_TYPE = "BROKERAGE"

class ETradeAccountService(AccountService):

    def __init__(self, connector: ETradeConnector):
        super().__init__(connector)
        self.session, self.base_url = self.connector.load_connection()

    def list_accounts(self) -> AccountListResponse:
        path = f"/v1/accounts/list.json"
        url = self.base_url + path
        response = self.session.get(url)
        account_list_response = ETradeAccountService._parse_account_list_response(response)
        return AccountListResponse(account_list_response)

    def get_account_balance(self, get_account_info_request: GetAccountBalanceRequest) -> GetAccountBalanceResponse:
        account_id = get_account_info_request.account_id
        path = f"/v1/accounts/{account_id}/balance.json"

        params: dict[str, str] = dict[str, str]()

        params["instType"] = DEFAULT_INST_TYPE
        params["realTimeNAV"] = "true"

        url = self.base_url + path
        response = self.session.get(url, params=params)

        account_balance: AccountBalance = ETradeAccountService._parse_account_balance_response(response)

        return GetAccountBalanceResponse(account_balance)


    def get_account_info(self, get_account_info_request: GetAccountInfoRequest) -> GetAccountInfoResponse:
        path = f"/v1/accounts/list.json"
        url = self.base_url + path
        response = self.session.get(url)
        print(response.request.headers)
        print(response.url)

        name_filter = (lambda a: a.account_id == get_account_info_request.account_id)

        account_list: list[Account] = ETradeAccountService._parse_account_list_response(response, name_filter)
        if len(account_list) > 1:
            raise Exception("More than one result")

        if len(account_list) == 1:
            return GetAccountInfoResponse(account_list[0])

        return GetAccountInfoResponse(None)

    @staticmethod
    def _parse_account_list_response(input, f=(lambda a: a)) -> list[Account]:
        data: dict = input.json()
        if 'error' in data:
            code = data['error']['code']
            message = data['error']['message']
            raise Exception(f"Error from E*Trade: {code}: {message}")
        account_list_response = data["AccountListResponse"]
        accounts: list = account_list_response["Accounts"]

        return_accounts = map(lambda account: ETradeAccount(account["accountId"], account["accountIdKey"],
                                                    account["accountName"], account["accountDesc"]), accounts["Account"])

        return list(filter(f, return_accounts))

    @staticmethod
    def _parse_account_balance_response(input) -> AccountBalance:
        data: dict = input.json()
        if 'Error' in data:
            message = data['Error']['message']
            raise Exception(f"Error from E*Trade: {input.status_code}: {message}")

        balance_response = data["BalanceResponse"]
        computed = balance_response["Computed"]

        realtime_values = computed["RealTimeValues"]
        open_calls = computed["OpenCalls"]



        account_id = balance_response["accountId"]
        total_account_value = realtime_values["totalAccountValue"]
        as_of_date = datetime.now()

        cash_available_for_investment: Amount = Amount.from_string(str(computed['settledCashForInvestment'])) + Amount.from_string(str(computed['unSettledCashForInvestment']))
        cash_available_for_withdrawal: Amount = Amount.from_string(str(computed['cashAvailableForWithdrawal']))
        net_cash: Amount = Amount.from_float(computed["netCash"])
        cash_balance: Amount = Amount.from_float(computed["cashBalance"])
        margin_buying_power: Amount = Amount.from_float(computed["marginBuyingPower"])
        cash_buying_power: Amount = Amount.from_float(computed["cashBuyingPower"])
        margin_balance: Amount = Amount.from_float(computed["marginBalance"])
        account_balance: Amount = Amount.from_float(computed["accountBalance"])

        brokerage_calls: list[BrokerageCall] = []
        for call_type, call_value in open_calls.items():
            if call_value < 0:
                brokerage_call_type: BrokerageCallType = BrokerageCallType.from_string(call_type)
                amount: Amount = Amount.from_float(call_value)
                brokerage_calls.append(BrokerageCall(brokerage_call_type, amount))

        # TODO: Update these with real values
        computed_balance: ComputedBalance = ComputedBalance(cash_available_for_investment,
                                                            cash_available_for_withdrawal,net_cash, cash_balance,
                                                            margin_buying_power, cash_buying_power, margin_balance,
                                                            account_balance)

        account_balance: AccountBalance = AccountBalance(account_id, total_account_value, as_of_date,  computed_balance, brokerage_calls)
        return account_balance