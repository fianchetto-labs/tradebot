import math


def binomial_call_option(current_equity_price, strike_price, rate, time_in_years, up_equity_price, down_equity_price, up_option_value=None, down_option_value=None):
    """
    Computes the call option price using a single-period binomial model.

    Returns:
    Call option price at the current time
    """
    return binomial_option(current_equity_price, strike_price, rate, time_in_years, up_equity_price,
                                down_equity_price, True, up_option_value, down_option_value)


def binomial_put_option(current_equity_price, strike_price, rate, time_in_years, up_equity_price, down_equity_price, up_option_value=None, down_option_value=None):
    """
    Computes the call option price using a single-period binomial model.

    Returns:
    Call option price at the current time
    """
    return binomial_option(current_equity_price, strike_price, rate, time_in_years, up_equity_price, down_equity_price, False, up_option_value, down_option_value)


def binomial_option(current_equity_price, strike_price, rate, time_in_years, up_equity_price, down_equity_price, is_call: bool, up_option_value=None, down_option_value=None):
    """
    Computes the call option price using a single-period binomial model.

    Returns:
    Call option price at the current time
    """
    # Compute up and down factors ..
    # This is a reference implementation. Normally u and d are inverses and u is calculated using
    # the risk-free rate, along with the time step size. If doing it this way, we will have a
    # non-combining tree, which may slow computation.
    up_equity_ratio = up_equity_price / current_equity_price
    down_equity_ratio = down_equity_price / current_equity_price

    # Risk-neutral probability
    p = (math.exp(rate * time_in_years) - down_equity_ratio) / (up_equity_ratio - down_equity_ratio)

    # TODO: In the recursive case, this would need to be take into account the time value (not just intrinsic value)
    # of these options. This can be easily done by supplying it as an argument and calculating the default
    # values via strikes otherwise.
    if not up_option_value:
        if is_call:
        # Compute option payoffs at final step
            up_option_value = max(up_equity_price - strike_price, 0)  # Call option value if price goes up
        else:
            up_option_value = max(strike_price - up_equity_price, 0)  # Put option value if price goes up

    if not down_option_value:
        if is_call:
            down_option_value = max(down_equity_price - strike_price, 0)  # Call option value if price goes down
        else:
            down_option_value = max(strike_price - down_equity_price, 0)  # Put option value if price goes down

    # Discounted expected value
    option_0 = math.exp(-rate * time_in_years) * (p * up_option_value + (1 - p) * down_option_value)

    return option_0


if __name__ == "__main__":
    # Example usage
    current_stock_price = 40  # Current stock price
    strike_price = 51  # Strike price
    r = 0.05  # Risk-free interest rate (5%)
    time_to_expiry_years = 3/12  # Time to expiration (1 year)
    stock_price_up = 53  # Stock price if it goes up
    stock_price_down = 47.5  # Stock price if it goes down
    option_price_up = 2.91
    option_price_down = 0

    call_price = binomial_call_option(current_stock_price, strike_price, r, time_to_expiry_years, stock_price_up, stock_price_down,option_price_up, option_price_down)
    print(f"The call option price at time 0 is: ${call_price:.2f}")
