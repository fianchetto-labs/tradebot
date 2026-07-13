from datetime import date

from common.util.chain_testing_util import instantiate_simple_chain_builder
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.chain import Chain, ChainBuilder
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.finance.priced_option import PricedOption
from tests.common.util import chain_testing_util


def _assert_all_dict_keys_are_strings(value):
    if isinstance(value, dict):
        for key, nested_value in value.items():
            assert isinstance(key, str), f"Expected serialized key to be str, got {type(key)}: {key!r}"
            _assert_all_dict_keys_are_strings(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _assert_all_dict_keys_are_strings(nested_value)


def test_print_chain():
    cb = chain_testing_util.build_chain()

    print(cb)

def test_chain_builder_to_chain():
    cb = chain_testing_util.build_chain()

    print(cb.to_chain())

def test_add_single_expiry():
    cb = instantiate_simple_chain_builder()

    print(cb.to_chain())

def test_chain_model_dump_single_dict():
    cb: ChainBuilder = instantiate_simple_chain_builder()
    chain = cb.to_chain()

    as_dict = chain.model_dump()

    _assert_all_dict_keys_are_strings(as_dict)
    assert as_dict["strike_expiry_chain_call"]["25.00 USD"]["2025-09-19"]["bid"] == 1.0
    assert as_dict["expiry_strike_chain_call"]["2025-09-19"]["25.00 USD"]["ask"] == 2.0
    assert as_dict["strike_expiry_chain_put"]["25.00 USD"]["2025-09-19"]["bid"] == 1.0
    assert as_dict["expiry_strike_chain_put"]["2025-09-19"]["25.00 USD"]["ask"] == 2.0

    round_trip = Chain.model_validate(as_dict)
    assert Amount(whole=25, part=0) in round_trip.strike_expiry_chain_call
    assert date(2025, 9, 19) in round_trip.expiry_strike_chain_call
    assert Amount(whole=25, part=0) in round_trip.expiry_strike_chain_call[date(2025, 9, 19)]

    from_json = Chain.model_validate_json(chain.model_dump_json())
    assert Amount(whole=25, part=0) in from_json.strike_expiry_chain_put
    assert date(2025, 9, 19) in from_json.expiry_strike_chain_put

def test_empty_chain_model_dump():
    underlying = Equity(ticker="GE")
    cb = ChainBuilder(underlying)

    chain = cb.to_chain()

    chain.model_dump()

def test_empty_chain_manually_initialized_values_model_dump():
    underlying = Equity(ticker="GE")
    cb = ChainBuilder(underlying)

    chain = cb.to_chain()

    chain.strike_expiry_chain_call = dict()
    chain.strike_expiry_chain_put = dict()
    chain.expiry_strike_chain_call = dict()
    chain.expiry_strike_chain_put = dict()

    chain.model_dump()

def test_empty_chain_manually_initialized_values_model_dump_types_defined():
    underlying = Equity(ticker="GE")
    cb = ChainBuilder(underlying)

    chain = cb.to_chain()

    chain.strike_expiry_chain_call = dict[Amount, dict[date, Price]]()
    chain.strike_expiry_chain_put = dict[Amount, dict[date, Price]]()
    chain.expiry_strike_chain_call = dict[date, dict[Amount, Price]]()
    chain.expiry_strike_chain_put = dict[date, dict[Amount, Price]]()

    chain.model_dump()

def test_empty_chain_manually_initialized_values_model_dump_types_defined_manually_populate_one():
    underlying = Equity(ticker="GE")
    cb = ChainBuilder(underlying)

    chain = cb.to_chain()

    chain.strike_expiry_chain_call = dict[Amount, dict[date, Price]]()
    chain.strike_expiry_chain_put = dict[Amount, dict[date, Price]]()
    chain.expiry_strike_chain_call = dict[date, dict[Amount, Price]]()
    chain.expiry_strike_chain_put = dict[date, dict[Amount, Price]]()

    chain.model_dump()

def test_one_entry_chain_model_dump():
    underlying = Equity(ticker="GE")
    cb = ChainBuilder(underlying)

    p = Price(bid=1.0, ask=2.0)
    expiry_date = date(2025, 9, 19)
    o = Option(equity=underlying, type=OptionType.CALL, strike=Amount(whole=25, part=0), expiry=expiry_date,
               style=ExerciseStyle.AMERICAN)

    o2 = Option(equity=underlying, type=OptionType.PUT, strike=Amount(whole=25, part=0), expiry=expiry_date,
                style=ExerciseStyle.AMERICAN)
    po = PricedOption(option=o, price=p)
    cb.add(po)

    chain = cb.to_chain()
    as_dict = chain.model_dump()
    _assert_all_dict_keys_are_strings(as_dict)
    assert as_dict["expiry_strike_chain_call"]["2025-09-19"]["25.00 USD"]["mark"] == 1.5
