import pytest

from fianchetto_tradebot.trident.research.oracles.binomial_pricing.binomial_pricing import binomial_call_option


# Test cases
def test_binomial_call_option_at_current_strike():
    assert abs(binomial_call_option(50, 50, 0.05, 1, 60, 40) - 5.975) < 0.1, "Test Case 1 Failed"

def test_binomial_call_option_at_higher_strike():
    assert abs(binomial_call_option(50, 55, 0.05, 1, 60, 40) - 2.988) < 0.1, "Test Case 2 Failed"

def test_binomial_call_option_at_higher_strike_with_lower_rate():
    assert abs(binomial_call_option(50, 55, 0.03, 1, 60, 40) - 2.796) < 0.1, "Test Case 3 Failed"

def test_binomial_call_option_at_higher_strike_with_lower_rate_and_less_time():
    assert abs(binomial_call_option(50, 55, 0.03, .5, 60, 40) - 2.649) < 0.1, "Test Case 4 Failed"


def test_binomial_put_option_at_higher_strike_with_lower_rate_and_less_time():
    assert abs(binomial_call_option(40, 40, 0.06, .25, 45, 35) - 2.761) < 0.1, "Test Case 4 Failed"

def test_binomial_call_option_with_specified_option_values():
    assert abs(binomial_call_option(40, 40, 0.06, .25, 45, 35) - 2.761) < 0.1, "Test Case 4 Failed"


if __name__ == "__main__":
    pytest.main()