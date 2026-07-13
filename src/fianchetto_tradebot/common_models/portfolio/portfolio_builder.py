import logging
from datetime import datetime, date

from pydantic import BaseModel, field_validator, field_serializer

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.finance.tradable import Tradable
from fianchetto_tradebot.common_models.order.tradable_type import TradableType
from fianchetto_tradebot.common_models.serialization import (
    deserialize_amount_key,
    deserialize_date_key,
    deserialize_enum_key,
    serialize_amount_key,
    serialize_date_key,
    serialize_enum_key,
)

logger = logging.getLogger(__name__)

class Portfolio(BaseModel):
    equities: dict
    options: dict[str, dict[date, dict[Amount, dict[OptionType, float]]]]

    @field_serializer('options', when_used='always')
    def serialize_options(self, options: dict):
        serialized = dict()
        for symbol, date_map in options.items():
            serialized[symbol] = dict()
            for expiry, amount_map in date_map.items():
                expiry_key = serialize_date_key(expiry)
                serialized[symbol][expiry_key] = {}
                for amount_obj, opttype_map in amount_map.items():
                    amount_key = serialize_amount_key(amount_obj)
                    serialized[symbol][expiry_key][amount_key] = {}
                    for option_type, quantity in opttype_map.items():
                        serialized[symbol][expiry_key][amount_key][serialize_enum_key(option_type)] = quantity
        return serialized

    @field_validator('options', mode='before')
    def deserialize_options(cls, v):
        # Rebuild Amount keys (deep inside)
        if isinstance(v, dict):
            rebuilt = {}
            for symbol, date_map in v.items():
                rebuilt[symbol] = {}
                for expiry, amount_map in date_map.items():
                    expiry_obj = deserialize_date_key(expiry)
                    rebuilt[symbol][expiry_obj] = {}
                    for amount_key, opttype_map in amount_map.items():
                        amount_obj = deserialize_amount_key(amount_key)
                        rebuilt[symbol][expiry_obj][amount_obj] = {}
                        for option_type, quantity in opttype_map.items():
                            rebuilt[symbol][expiry_obj][amount_obj][deserialize_enum_key(OptionType, option_type)] = quantity
            return rebuilt
        return v

class PortfolioBuilder:
    def __init__(self):

        # equities[equity] = count
        self.equities = dict[str, float]()
        # options[equity][expiry][strike][type:put/call] = count
        self.options = dict[str, dict[date, dict[Amount, dict[OptionType, float]]]]()

    def add_position(self, tradable: Tradable, quantity: int):
        if isinstance(tradable, Option):
            ticker: str = tradable.equity.ticker
            strike: Amount = tradable.strike
            type: OptionType = tradable.type
            expiry: datetime = tradable.expiry

            if ticker not in self.options:
                self.options[ticker] = dict[date, dict[Amount, dict[OptionType, float]]]()
                self.options[ticker][expiry] = dict[Amount, dict[OptionType, float]]()
                self.options[ticker][expiry][strike] = dict[OptionType, float]()
            elif expiry not in self.options[ticker]:
                self.options[ticker][expiry] = dict[Amount, dict[OptionType, float]]()
                self.options[ticker][expiry][strike] = dict[OptionType, float]()
            elif strike not in self.options[ticker][expiry]:
                self.options[ticker][expiry][strike] = dict[OptionType, float]()

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

