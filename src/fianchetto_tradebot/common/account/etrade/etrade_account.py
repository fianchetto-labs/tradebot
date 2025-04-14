from fianchetto_tradebot.common.account.account import Account


class ETradeAccount(Account):
    def __init__(self, account_id: str, account_id_key: str, account_name: str, account_desc: str):
        self.account_id_key = account_id_key
        super().__init__(account_id, account_name, account_desc)