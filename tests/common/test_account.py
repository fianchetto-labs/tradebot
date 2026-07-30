import pytest

from fianchetto_tradebot.common_models.account.account import Account


class TestAccount:
    def test_create_account(self):
        a = Account(account_id="abc123", account_name="n1", account_desc="random acct")
        assert a.account_id == "abc123"
        assert a.account_name == "n1"
        assert a.account_desc == "random acct"

if __name__ == "__main__":
    pytest.main()
