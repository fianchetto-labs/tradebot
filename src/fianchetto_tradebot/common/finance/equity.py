from typing import Optional, Annotated

from pydantic import PlainValidator

from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.order.tradable_type import TradableType


def validate_ticker(input: str):
    if not input:
        raise ValueError("Ticker symbol cannot be empty")

    if len(input) > 4:
        raise ValueError("Ticker symbol cannot greater than 4 characters")
    return input

class Equity(Tradable):
    ticker: Annotated[str, PlainValidator(validate_ticker)]
    company_name: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def set_price(self, price: Price):
        self.price = price

    def get_type(self) ->TradableType:
        return TradableType.Equity

    def __hash__(self):
        return hash(self.ticker)

    def __eq__(self, other):
        return self.ticker == other.ticker

    def __str__(self):
        return f'{self.ticker}: {self.company_name}'
