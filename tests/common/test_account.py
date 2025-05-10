import sys

import pytest

from fianchetto_tradebot.common_models.account.account import Account

print(sys.path)

class TestAccount:
    def test_create_account(self):
        a = Account(account_id="abc123", account_name="n1", account_desc="random acct")

        print(a)

if __name__ == "__main__":
    pytest.main()