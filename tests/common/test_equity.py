import pytest as pytest

from fianchetto_tradebot.common_models.finance.equity import Equity


def test_equity_string():
    e = Equity(ticker="GE", company_name="General Electric")
    assert e.__str__() == "GE: General Electric"

def test_equity_empty_ticker():
    with pytest.raises(Exception, match='empty'):
        Equity(ticker="", company_name="General Electric")
