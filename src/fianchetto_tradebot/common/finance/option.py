from datetime import datetime


from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.order.tradable_type import TradableType
from fianchetto_tradebot.common.utils.local_ticker_lookup import LocalTickerLookup

from dateutil.parser import parse


class Option(Tradable):
    equity: Equity
    type: OptionType
    strike: Amount
    expiry: datetime
    style: ExerciseStyle = ExerciseStyle.AMERICAN

    def copy_of(self):
        return Option(tradable=self.equity, type=self.type, strike=self.strike, expiry=self.expiry, style=self.style)

    def get_type(self) -> TradableType:
        return TradableType.Option

    def __hash__(self):
        return hash((self.equity, self.type, self.strike, self.expiry, self.style))

    def __eq__(self, other):
        if not type(other) == type(self):
            raise Exception(f"Cannot compare option to non-option: {self.type}")

        if self.equity != other.equity:
            return False

        if self.type != other.type:
            return False

        if self.strike != other.strike:
            return False

        if self.expiry != other.expiry:
            return False

        if self.style != other.style:
            return False

        return True

    @staticmethod
    # Space-delimited info in the form $TICKET MM DD YY $STRIKE TYPE
    def from_str(input: str):
        components: list[str] = input.split(' ')
        ticker: str = str(components[0])
        expiry: datetime = parse(" ".join(components[1:4]))
        strike: Amount = Amount.from_string(components[4])
        type: OptionType = OptionType.from_str(components[5])

        company_name = LocalTickerLookup.lookup(ticker)

        return Option(equity=Equity(ticker=ticker, company_name=company_name), type=type, strike=strike, expiry=expiry, style=ExerciseStyle.from_ticker(ticker))