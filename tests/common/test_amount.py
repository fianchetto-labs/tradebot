from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.currency import Currency


def test_add_two_amounts():
    a1 = Amount(whole=10, part=15, currency=Currency.US_DOLLARS)
    a2 = Amount(whole=2, part=95, currency=Currency.US_DOLLARS)

    a3 = a1 + a2

    assert a3.whole == 13
    assert a3.part == 10
    assert a3.currency == Currency.US_DOLLARS
    assert not a3.negative

def test_no_trailing_zero_after_decimal():
    assert Amount.from_string("5.2") == Amount(whole=5, part=20)


def test_part_less_than_10():
    assert Amount.from_float(5.02) == Amount(whole=5, part=2)

def test_part_less_than_10_2():
    assert Amount.from_float(1.09) == Amount(whole=1, part=9)

def test_part_less_than_10_str_rep():
    actual = str(Amount.from_float(1.09))
    assert actual == "1.09 USD"

def test_negative_value_str_rep():
    assert str(Amount.from_float(-1.09)) == "-1.09 USD"

def test_subtract_two_amounts():
    a1 = Amount(whole=10, part=15, currency=Currency.US_DOLLARS)
    a2 = Amount(whole=2, part=95, currency=Currency.US_DOLLARS)

    a3 = a1 - a2

    assert a3.whole == 7
    assert a3.part == 20
    assert a3.currency == Currency.US_DOLLARS
    assert not a3.negative

def test_equals_respects_negative():
    a1 = Amount(whole=1, part=0, currency=Currency.US_DOLLARS, negative=False)
    a2 = Amount(whole=1, part=0, currency=Currency.US_DOLLARS, negative=True)
    assert a1 != a2

    a3 = Amount(whole=1, part=0, currency=Currency.US_DOLLARS, negative=True)
    assert a2 == a3

def test_subtract_two_amounts_negative_result():
    a1 = Amount(whole=10, part=15, currency=Currency.US_DOLLARS)
    a2 = Amount(whole=2, part=95, currency=Currency.US_DOLLARS)

    a3 = a2 - a1

    assert a3.whole == 7
    assert a3.part == 20
    assert a3.currency == Currency.US_DOLLARS
    assert a3.negative

def test_divide_two_amounts():
    a1 = Amount(whole=10, part=15, currency=Currency.US_DOLLARS)
    a2 = Amount(whole=6, part=3, currency=Currency.US_DOLLARS)

    a3 = a1 / a2

    assert a3 == 1.68

def test_add_negative_number():
    input_1 = Amount(whole=0, part=0)
    input_2 = Amount(whole=3, part=84, negative=True)

    expected_result = Amount(whole=3, part=84, negative=True)

    assert input_1 + input_2 == expected_result
    assert input_2 + input_1 == expected_result

def test_abs():
    assert abs(Amount(whole=1, part=4, negative=False)) == abs(Amount(whole=1, part=4, negative=True))

def test_abs_returns_amount():
    assert abs(Amount(whole=1, part=4, negative=True)) == Amount(whole=1, part=4, negative=False)

def test_multiply_two_amounts():
    a1 = Amount(whole=10, part=15, currency=Currency.US_DOLLARS)
    a2 = 2.95

    a3 = a1 * a2

    assert a3.whole == 29
    assert a3.part == 94
    assert a3.currency == Currency.US_DOLLARS
    print(a3.negative)
    assert False is a3.negative

def test_multiply_two_amounts_is_negative():
    a1 = Amount(whole=10, part=15, currency=Currency.US_DOLLARS)
    negative_scalar = -2.5

    a3 = a1 * negative_scalar

    assert a3.whole == 25
    assert a3.part == 38
    assert a3.currency == Currency.US_DOLLARS
    print(a3.negative)
    assert True is a3.negative


def test_amount_str_and_repr():
    amt = Amount(whole=5, part=99, currency="USD", negative=False)

    assert str(amt) == "5.99 USD"
    assert repr(amt) == "Amount(whole=5, part=99, currency='USD', negative=False)"

    neg_amt = Amount(whole=3, part=45, currency="EUR", negative=True)

    assert str(neg_amt) == "-3.45 EUR"
    assert repr(neg_amt) == "Amount(whole=3, part=45, currency='EUR', negative=True)"