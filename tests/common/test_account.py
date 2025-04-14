import sys

import pytest

from fianchetto_tradebot.common.account.account import Account

print(sys.path)

class TestAccount:
    def test_create_account(self):
        a = Account("abc123", "n1", "random acct")

        print(sys.path)
        print(a)

if __name__ == "__main__":
    pytest.main()