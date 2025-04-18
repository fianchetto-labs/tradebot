from pydantic import BaseModel

from fianchetto_tradebot.common.portfolio.portfolio_builder import Portfolio

DEFAULT_NUM_POSITIONS = 1000

class GetPortfolioResponse(BaseModel):
    portfolio: Portfolio
