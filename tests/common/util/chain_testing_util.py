from datetime import datetime, timedelta

from fianchetto_tradebot.common.finance.chain import ChainBuilder
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.priced_option import PricedOption
from fianchetto_tradebot.common.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.price import Price

DEFAULT_EQUITY = Equity(ticker="GE", company_name="General Electric", price=Price(bid=9.66,ask=10.07))

DEFAULT_NUM_STRIKES_EACH_SIDE = 5
DEFAULT_NUM_EXPIRIES = 3
DEFAULT_EXPIRY = datetime(2024, 7, 12)
DEFAULT_MIDDLE_STRIKE = 10.0
DEFAULT_STRIKE_DELTA = .50
DEFAULT_REFERENCE_OPTIONS_PRICE: float = 1.0

DEFAULT_SPREAD_AMT: float = .07


def build_chain(equity=DEFAULT_EQUITY, num_strikes_each_side=DEFAULT_NUM_STRIKES_EACH_SIDE, expiry=DEFAULT_EXPIRY, num_expiries=DEFAULT_NUM_EXPIRIES, centered_around=DEFAULT_MIDDLE_STRIKE, strike_delta=DEFAULT_STRIKE_DELTA, reference_options_price=DEFAULT_REFERENCE_OPTIONS_PRICE, spread_amt=DEFAULT_SPREAD_AMT):
    return_chain = ChainBuilder(equity)

    current_expiry = expiry
    current_reference_options_price: Amount = reference_options_price
    for e in range(1, num_expiries+1):
        return_chain.add_chain(build_chain_for_expiry(equity, num_strikes_each_side,
                               current_expiry, centered_around,
                               strike_delta, current_reference_options_price, spread_amt))

        current_expiry = current_expiry + timedelta(weeks=1)
        current_reference_options_price = current_reference_options_price * 1.25

    return return_chain


# For testing, assume a linear decay from 0 at (DEFAULT_NUM_STRIKES_EACH_SIDE + 1 ) strikes away
# This is a simple generation tool. It's not meant to simulate realistic numbers
def build_chain_for_expiry(equity=DEFAULT_EQUITY, num_strikes_each_side=DEFAULT_NUM_STRIKES_EACH_SIDE, expiry=DEFAULT_EXPIRY, centered_around=DEFAULT_MIDDLE_STRIKE, strike_delta=DEFAULT_STRIKE_DELTA, reference_options_price=DEFAULT_REFERENCE_OPTIONS_PRICE, spread_amt=DEFAULT_SPREAD_AMT):

    return_chain = ChainBuilder(equity)
    strikes: dict[float] = _get_strikes(centered_around, strike_delta, num_strikes_each_side)
    option_prices_at_strikes = _get_option_prices_at_strikes(equity, strikes, strike_delta, num_strikes_each_side, reference_options_price, spread_amt, expiry)
    for strike in strikes:
        (put, call) = option_prices_at_strikes[strike]
        return_chain.add(put)
        return_chain.add(call)

    return return_chain


def _get_strikes(centered_around: float, strike_delta: float, num_strikes_each_side: int) -> list[float]:
    return [centered_around + x * strike_delta for x in range(-num_strikes_each_side, num_strikes_each_side + 1)]


"""
Generate a line from the current price, and get the prices of that line at the strike prices
dict[strike -> (put price, call price) 
"""


def _get_option_prices_at_strikes(equity: Equity, strikes: list[float], strike_delta: Amount, num_strikes_each_side: int, reference_options_price: float, spread_amt=DEFAULT_SPREAD_AMT, expiry=DEFAULT_EXPIRY):
    return_list: dict[float, (Price, Price)] = dict()

    current_price: float = equity.price.mark

    full_delta_distance = (num_strikes_each_side + 1) * strike_delta
    time_value_line2 = _generate_linear_function((current_price, reference_options_price), (current_price + full_delta_distance, 0))
    time_value_line1 = _generate_linear_function((current_price, reference_options_price), (current_price - full_delta_distance, 0))

    for strike in strikes:
        if strike <= current_price:
            put_value = time_value_line1(strike)
            call_value = time_value_line1(strike) + (current_price - strike)
        else:
            put_value = time_value_line2(strike) + (strike - current_price)
            call_value = time_value_line2(strike)

        if strike not in return_list:
            return_list[strike] = dict()

        put_option_price = _generate_full_option_price_around_central_value(put_value, spread_amt)
        call_option_price = _generate_full_option_price_around_central_value(call_value, spread_amt)
        put_option = Option(equity=equity, type=OptionType.PUT, strike=Amount.from_float(strike), expiry=expiry, style=ExerciseStyle.AMERICAN)
        call_option = Option(equity=equity, type=OptionType.CALL, strike=Amount.from_float(strike), expiry=expiry, style=ExerciseStyle.AMERICAN)
        return_list[strike] = (PricedOption(option=put_option, price=put_option_price),
                               PricedOption(option=call_option, price=call_option_price))

    return return_list


def _generate_linear_function(p1: (float, float), p2: (float, float)):
    (x1, y1) = p1
    (x2, y2) = p2

    slope: float = (y2 - y1) / (x2 - x1)

    # y = mx + b
    # plug in an xy
    # b = y - mx
    b: float = y2 - slope * x2

    # TODO: Figure out how to annotate a lambda
    return lambda x: slope * x + b


def _generate_full_option_price_around_central_value(
        central_value: float, spread_amt: float = .15) -> Price:
    return Price(bid=central_value - spread_amt, ask=central_value + spread_amt, last=central_value + .2)


if __name__ == "__main__":
    print(_get_strikes(DEFAULT_MIDDLE_STRIKE, DEFAULT_STRIKE_DELTA, DEFAULT_NUM_STRIKES_EACH_SIDE))