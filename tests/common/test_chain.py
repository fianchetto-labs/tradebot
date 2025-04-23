from datetime import date

from flask import jsonify

from common.util.chain_testing_util import instantiate_simple_chain_builder
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.chain import ChainBuilder
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.priced_option import PricedOption
from tests.common.util import chain_testing_util


def test_print_chain():
    cb = chain_testing_util.build_chain()

    print(cb)

def test_chain_builder_to_chain():
    cb = chain_testing_util.build_chain()

    print(cb.to_chain())

def test_add_single_expiry():
    cb = instantiate_simple_chain_builder()

    print(cb.to_chain())

def test_chain_model_dump():
    cb: ChainBuilder = instantiate_simple_chain_builder()
    chain = cb.to_chain()

    chain.model_dump()
