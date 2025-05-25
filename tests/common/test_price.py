import pytest

from fianchetto_tradebot.common_models.finance.price import Price


@pytest.fixture
def price1():
    return Price(bid=100.1234, ask=101.9876)

@pytest.fixture
def price2():
    return Price(bid=200.4321, ask=202.5678)

def test_addition(price1, price2):
    result = price1 + price2
    assert result.bid == round(price1.bid + price2.bid, 2)
    assert result.ask == round(price1.ask + price2.ask, 2)

def test_subtraction(price1, price2):
    result = price2 - price1
    assert result.bid == round(price2.bid - price1.ask, 2)
    assert result.ask == round(price2.ask - price1.bid, 2)

def test_rounding():
    price = Price(bid=123.456789, ask=987.654321)
    assert price.bid == 123.46
    assert price.ask == 987.65

def test_mark_property():
    price = Price(bid=99.99, ask=100.01)
    assert price.mark == 100.0
