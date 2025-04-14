from locale import currency

from src.fianchetto_tradebot.common.finance.amount import Amount
from src.fianchetto_tradebot.common.finance.currency import Currency
from src.fianchetto_tradebot.common.portfolio.portfolio import Portfolio
from tests.common import test_option
from tests.common.util.test_object_util import get_sample_option, get_sample_equity


def test_add_option():
    p = Portfolio()
    o = get_sample_option()
    p.add_position(o, 1)
    assert 1 == p.get_quantity(o)

def test_add_two_options_diff_strike():
    p = Portfolio()
    o = get_sample_option()
    o2 = get_sample_option()
    o2.strike = Amount(whole=10, part=0, negative=False, currency=Currency.US_DOLLARS)

    p.add_position(o, 1)
    p.add_position(o2, 1)

    assert 1 == p.get_quantity(o)
    assert 1 == p.get_quantity(o2)


def test_add_two_options_diff_expiry():
    p = Portfolio()
    o = get_sample_option()
    o2 = get_sample_option()
    o2.expiry = test_option.expiry2

    p.add_position(o, 1)
    p.add_position(o2, 1)

    assert 1 == p.get_quantity(o)
    assert 1 == p.get_quantity(o2)


def test_add_equity():
    p = Portfolio()
    e = get_sample_equity()
    p.add_position(e, 1)
    assert 1 == p.get_quantity(e)


def test_remove_option():
    p = Portfolio()
    o = get_sample_option()
    p.add_position(o, 1)

    p.remove_position(o)

    assert 0 == p.get_quantity(o)


def test_remove_equity():
    p = Portfolio()
    e = get_sample_equity()
    p.add_position(e, 1)

    p.remove_position(e)

    assert 0 == p.get_quantity(e)


def test_add_equity_and_option():
    pass


def get_option_not_present():
    pass

def get_equity_not_present():
    pass


