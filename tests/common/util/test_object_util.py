import datetime

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.currency import Currency
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType

ticker = "GE"

type = OptionType.PUT
type2 = OptionType.CALL

strike = Amount(whole=165, part=0, currency=Currency.US_DOLLARS)

expiry = datetime.datetime(2025, 3, 21).date()
expiry2 = datetime.datetime.today().date()

price = Amount(whole=0, part=87, currency=Currency.US_DOLLARS)
style = ExerciseStyle.AMERICAN


def get_sample_expiry():
    return expiry


def get_sample_price():
    return price


def get_sample_strike():
    return strike


def get_sample_option():
    return Option(equity=get_sample_equity(), type=type, strike=strike, expiry=expiry, style=style)


def get_sample_equity():
    return Equity(ticker=ticker, company_name="General Electric")
