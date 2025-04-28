from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.currency import Currency
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.portfolio.portfolio_builder import PortfolioBuilder, Portfolio
from tests.common import test_option
from tests.common.util.test_object_util import get_sample_option, get_sample_equity

def test_add_option():
    p = PortfolioBuilder()
    o = get_sample_option()
    p.add_position(o, 1)
    assert 1 == p.get_quantity(o)

def test_add_two_options_diff_strike():
    p = PortfolioBuilder()
    o = get_sample_option()
    o2 = get_sample_option()
    o2.strike = Amount(whole=10, part=0, negative=False, currency=Currency.US_DOLLARS)

    p.add_position(o, 1)
    p.add_position(o2, 1)

    assert 1 == p.get_quantity(o)
    assert 1 == p.get_quantity(o2)

def test_portfolio_dump():
    p = PortfolioBuilder()
    o = get_sample_option()
    o2 = get_sample_option()
    o2.strike = Amount(whole=10, part=0, negative=False, currency=Currency.US_DOLLARS)

    p.add_position(o, 1)
    p.add_position(o2, 1)

    portfolio: Portfolio = p.to_portfolio()
    portfolio.model_dump()

def test_portfolio_serde():
    p = PortfolioBuilder()
    o = get_sample_option()
    o2 = get_sample_option()
    o2.strike = Amount(whole=10, part=0, negative=False, currency=Currency.US_DOLLARS)

    p.add_position(o, 1)
    p.add_position(o2, 1)

    portfolio: Portfolio = p.to_portfolio()
    model_dump_json = portfolio.model_dump_json()

    from_json: Portfolio = Portfolio.model_validate_json(model_dump_json)

    ge_opts = from_json.options["GE"]
    ge_opts_at_expiry = ge_opts[o2.expiry]
    ge_opts_at_expiry_strike = ge_opts_at_expiry[o2.strike]
    ge_opts_at_expiry_strike_type = ge_opts_at_expiry_strike[OptionType.PUT]

    assert ge_opts_at_expiry_strike_type == 1

def test_add_two_options_diff_expiry():
    p = PortfolioBuilder()
    o = get_sample_option()
    o2 = get_sample_option()
    o2.expiry = test_option.expiry2

    p.add_position(o, 1)
    p.add_position(o2, 1)

    assert 1 == p.get_quantity(o)
    assert 1 == p.get_quantity(o2)

def test_add_equity():
    p = PortfolioBuilder()
    e = get_sample_equity()
    p.add_position(e, 1)
    assert 1 == p.get_quantity(e)

def test_remove_option():
    p = PortfolioBuilder()
    o = get_sample_option()
    p.add_position(o, 1)

    p.remove_position(o)

    assert 0 == p.get_quantity(o)

def test_portfolio_model_dump_empty_portfolio():
    pb = PortfolioBuilder()
    p: Portfolio = pb.to_portfolio()

    p.model_dump()

    p.options = dict()
    p.model_dump()

    p.options["GE"] = dict()
    p.model_dump()

def test_remove_equity():
    p = PortfolioBuilder()
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

