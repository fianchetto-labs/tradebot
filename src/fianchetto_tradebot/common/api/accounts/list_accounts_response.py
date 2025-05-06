from fianchetto_tradebot.common.account.account import Account
from fianchetto_tradebot.common.api.response import Response


class ListAccountsResponse(Response):
    account_list: list[Account]

    def get_account_list(self):
        return self.account_list

    def __str__(self):
        return f"Account List: {str(self.account_list)}"

    def __repr__(self):
        return self.__str__()