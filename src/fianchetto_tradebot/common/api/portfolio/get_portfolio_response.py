from fianchetto_tradebot.common.portfolio.portfolio import Portfolio

DEFAULT_NUM_POSITIONS = 1000

class GetPortfolioResponse:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
