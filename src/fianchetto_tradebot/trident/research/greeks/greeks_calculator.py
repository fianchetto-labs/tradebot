class GreeksCalculator:
    def __init__(self, current_interest_rate: float):
        self.current_interest_rate: float = current_interest_rate


    # First-Derivative of Price
    def get_delta(self):
        pass

    # Second-Derivative of Price
    def get_gamma(self):
        pass

    # Time Decay
    def get_theta(self):
        pass

    # Sensitivity to interest rates
    def get_rho(self):
        pass

    # Sensitivity to Implied Volatility
    def get_vega(self):
        pass