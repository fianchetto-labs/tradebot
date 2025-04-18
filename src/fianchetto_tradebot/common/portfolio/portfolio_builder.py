import logging
from datetime import datetime

from pydantic import BaseModel

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.order.tradable_type import TradableType

logger = logging.getLogger(__name__)

class Portfolio(BaseModel):
    equities: dict
    options: dict

class PortfolioBuilder:
    def __init__(self):

        # equities[equity] = count
        self.equities = dict()
        # options[equity][expiry][strike][type:put/call] = count
        self.options = dict()

    def add_position(self, tradable: Tradable, quantity: int):
        if isinstance(tradable, Option):
            ticker: str = tradable.equity.ticker
            strike: Amount = tradable.strike
            type: OptionType = tradable.type
            expiry: datetime = tradable.expiry

            if ticker not in self.options:
                self.options[ticker] = dict()
                self.options[ticker][expiry] = dict()
                self.options[ticker][expiry][strike] = dict()
                self.options[ticker][expiry][strike][type] = dict()
            elif expiry not in self.options[ticker]:
                self.options[ticker][expiry] = dict()
                self.options[ticker][expiry][strike] = dict()
                self.options[ticker][expiry][strike][type] = dict()
            elif strike not in self.options[ticker][expiry]:
                self.options[ticker][expiry][strike] = dict()
                self.options[ticker][expiry][strike][type] = dict()

            self.options[ticker][expiry][strike][type] = float(quantity)
        elif isinstance(tradable, Equity):
            ticker = tradable.ticker
            self.equities[ticker] = quantity

    def remove_position(self, tradable) -> None:
        if isinstance(tradable, Option):
            if self._option_value_present(tradable):
                self.options[tradable.equity.ticker][tradable.expiry][tradable.strike][tradable.type] = 0
        elif isinstance(tradable, Equity):
            self.equities[tradable.ticker] = 0

    def get_quantity(self, tradable) -> int:
        if tradable.get_type() == TradableType.Option:
            if self._option_value_present(tradable):
                return int(self.options[tradable.equity.ticker][tradable.expiry][tradable.strike][tradable.type])
            else:
                return 0

        elif tradable.get_type() == TradableType.Equity:
            if tradable.ticker in self.equities:
                return float(self.equities[tradable.ticker])
            else:
                return 0
        else:
            logger.warning(f"Type not recognized {tradable.get_type()}")
            return 0

    def _option_value_present(self, tradable):
        ticker = tradable.equity.ticker
        expiry = tradable.expiry
        strike = tradable.strike
        return (ticker in self.options and expiry in self.options[ticker] and
                strike in self.options[ticker][expiry] and
                tradable.type in self.options[ticker][expiry][strike])

    def to_portfolio(self)->Portfolio:
        return Portfolio(equities=self.equities, options=self.options)


