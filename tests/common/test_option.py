from datetime import date

import pytest as pytest
from pydantic import ValidationError

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common_models.order.expiry.good_for_sixty_days import GoodForSixtyDays

e = Equity(ticker="GE", company_name="General Electric")
type = OptionType.PUT
type2 = OptionType.CALL

strike = Amount(whole=10, part=0, currency=Currency.US_DOLLARS)

expiry: date = GoodForSixtyDays().expiry_date.date()
expiry2: date = GoodForDay().expiry_date.date()

price = Amount(whole=0, part=87, currency=Currency.US_DOLLARS)
style = ExerciseStyle.AMERICAN


def test_option_construction():
    o: Option = Option(equity=e, type=type, strike=strike, expiry=expiry, style=style)
    assert o.expiry is expiry


def test_option_empty_type():
    with pytest.raises(ValidationError, match='type'):
        Option(equity=e, type=None, strike=strike, expiry=expiry, style=style)


def test_option_none_date():
    with pytest.raises(ValidationError, match='Input should be a valid date'):
        Option(equity=e, type=type, strike=strike, expiry=None, style=style)


def test_option_equality():
    o: Option = Option(equity=e, type=type, strike=strike, expiry=expiry, style=style)
    o2: Option = Option(equity=e, type=type, strike=strike, expiry=expiry, style=style)

    assert o == o2


def test_option_inequality_type():
    o: Option = Option(equity=e, type=type, strike=strike, expiry=expiry, style=style)
    o2: Option = Option(equity=e, type=type2, strike=strike, expiry=expiry, style=style)

    assert o != o2


def test_option_inequality_expiry():
    o: Option = Option(equity=e, type=type, strike=strike, expiry=expiry, style=style)
    o2: Option = Option(equity=e, type=type, strike=strike, expiry=expiry2, style=style)

    assert o != o2


def test_option_parsing_european():
    input_str = "VIX Oct 16 '24 $19 Call"
    o = Option.from_str(input_str)

    assert o.type == OptionType.CALL
    assert o.strike == Amount(whole=19, part=0)
    assert date(2024, 10, 16) == o.expiry
    assert o.style == ExerciseStyle.EUROPEAN


def test_option_parsing_american():
    input_str = "RIOT Nov 08 '24 $7.50 Call"
    o = Option.from_str(input_str)

    assert o.type == OptionType.CALL
    assert o.strike == Amount(whole=7, part=50)
    assert date(2024, 11, 8) == o.expiry
    assert o.style == ExerciseStyle.AMERICAN
