import logging
from datetime import date

from pydantic import BaseModel, field_serializer, field_validator

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.priced_option import PricedOption

logger = logging.getLogger(__name__)


class Chain(BaseModel):
    equity: Equity
    strike_expiry_chain_call: dict[Amount, dict[date, Price]]
    expiry_strike_chain_call: dict[date, dict[Amount, Price]]
    strike_expiry_chain_put: dict[Amount, dict[date, Price]]
    expiry_strike_chain_put: dict[date, dict[Amount, Price]]

    # We get a dictionary .. we give it a better one

    @field_serializer('strike_expiry_chain_call', when_used='always')
    def serialize_strike_expiry_chain_call(self, strike_expiry_chain_call:dict):
        serialized: dict = dict()
        for amount, date_price_dict in strike_expiry_chain_call.items():
            amount_str = str(amount)
            serialized[amount_str] = date_price_dict

        return serialized

    @field_validator('strike_expiry_chain_call', mode='before')
    def deserialize_strike_expiry_chain_call(cls, v):
        # Rebuild Amount keys (deep inside)
        if isinstance(v, dict):
            rebuilt = dict()
            for amount, date_price_map in v.items():
                if isinstance(amount, Amount):
                    amount_obj = amount
                else:
                    amount_obj = Amount.from_string(amount)
                rebuilt[amount_obj] = dict()
                for date_key, price in date_price_map.items():
                    rebuilt[amount_obj][date_key] = price
            return rebuilt
        return v

    @field_serializer('strike_expiry_chain_put', when_used='always')
    def serialize_strike_expiry_chain_put(self, strike_expiry_chain_put: dict):
        serialized: dict = dict()
        for amount, date_price_dict in strike_expiry_chain_put.items():
            amount_str = str(amount)
            serialized[amount_str] = date_price_dict

        return serialized

    @field_validator('strike_expiry_chain_put', mode='before')
    def deserialize_strike_expiry_chain_put(cls, v):
        # Rebuild Amount keys (deep inside)
        if isinstance(v, dict):
            rebuilt = {}
            for amount, date_price_map in v.items():
                if isinstance(amount, Amount):
                    amount_obj = amount
                else:
                    amount_obj = Amount.from_string(amount)
                rebuilt[amount_obj] = dict()
                for date_key, price in date_price_map.items():
                    rebuilt[amount_obj][date_key] = price
            return rebuilt
        return v

    @field_serializer('expiry_strike_chain_call', when_used='always')
    def serialize_expiry_strike_chain_call(self, expiry_strike_chain_call: dict):
        serialized: dict = dict()
        for expiry, strike_to_price in expiry_strike_chain_call.items():
            serialized[expiry] = dict()
            for strike, price in strike_to_price.items():
                serialized[expiry][strike] = price

        return serialized

    @field_validator('expiry_strike_chain_call', mode='before')
    def deserialize_expiry_strike_chain_call(cls, v):
        # Rebuild Amount keys (deep inside)
        if isinstance(v, dict):
            rebuilt = {}
            for expiry, strike_price_map in v.items():
                rebuilt[expiry] = dict()
                for strike, price in strike_price_map.items():
                    if isinstance(strike, Amount):
                        amount_obj = strike
                    else:
                        amount_obj = Amount.from_string(strike)
                    rebuilt[expiry][amount_obj] = price
            return rebuilt
        return v

    @field_serializer('expiry_strike_chain_put', when_used='always')
    def serialize_expiry_strike_chain_put(self, expiry_strike_chain_put: dict):
        serialized: dict = dict()
        for expiry, strike_to_price in expiry_strike_chain_put.items():
            serialized[expiry] = dict()
            for strike, price in strike_to_price.items():
                serialized[expiry][strike] = price

        return serialized

    @field_validator('expiry_strike_chain_put', mode='before')
    def deserialize_expiry_strike_chain_put(cls, v):
        # Rebuild Amount keys (deep inside)
        if isinstance(v, dict):
            rebuilt = {}
            for expiry, strike_price_map in v.items():
                rebuilt[expiry] = dict()
                for strike, price in strike_price_map.items():
                    if isinstance(strike, Amount):
                        amount_obj = strike
                    else:
                        amount_obj = Amount.from_string(strike)
                    rebuilt[expiry][amount_obj] = price
            return rebuilt
        return v

class ChainBuilder:
    def __init__(self, equity: Equity):
        self.equity: Equity = equity
        # keyed on strike then date
        self.strike_expiry_chain_call: dict = dict[Amount, dict[date, Price]]()
        self.expiry_strike_chain_call: dict = dict[date, dict[Amount, Price]]()

        # keyed on date then strike
        self.strike_expiry_chain_put: dict = dict[Amount, dict[date, Price]]()
        self.expiry_strike_chain_put: dict = dict[date, dict[Amount, Price]]()

    def add(self, priced_option: PricedOption):
        option = priced_option.option
        if option.equity != self.equity:
            raise Exception(f"Adding incorrect equity in chain for {self.equity}")

        if not option.type:
            raise Exception(f"Could not determine if put or call")

        if option.type is OptionType.CALL:
            self._update_call_chain(priced_option)

        elif option.type is OptionType.PUT:
            self._update_put_chain(priced_option)

        else:
            raise Exception(f"Unrecognized option type {option.type}")

    def __str__(self):
        full_set = []
        keyset = set()
        keyset.update(list(self.expiry_strike_chain_put.keys()))
        keyset.update(list(self.expiry_strike_chain_call.keys()))
        for expiry in keyset:
            full_set.append(self.print(expiry))

        return '\n' + '\n'.join(full_set)

    def print(self, expiry: date):

        # Collect all the strikes for a given expiry:
        if expiry not in self.expiry_strike_chain_call or expiry not in self.expiry_strike_chain_put:
            logger.warning(f"expiry {expiry} missing from put or call chain")
            return ""

        strikes = set()
        strikes.update(self.expiry_strike_chain_call[expiry].keys())
        strikes.update(self.expiry_strike_chain_put[expiry].keys())

        strike_to_line_map = []
        for strike in sorted(strikes):
            put_price = str(self.expiry_strike_chain_put[expiry][strike]) if strike in self.expiry_strike_chain_put[expiry] else "___"
            call_price = str(self.expiry_strike_chain_call[expiry][strike]) if strike in self.expiry_strike_chain_call[expiry] else "___"

            strike_to_line_map.append(f"{put_price}\t${strike}\t\t{call_price}")

        return f'{expiry}:\n' + f"\nMark\t|\tBid \t|\tAsk \t|\tStrike\t|\tMark\t|\tBid \t|\tAsk \t\n" + '\n'.join(strike_to_line_map) + '\n'

    def _update_call_chain(self, priced_option: PricedOption):
        option = priced_option.option
        price = priced_option.price

        if option.strike in self.strike_expiry_chain_call:
            if self.strike_expiry_chain_call[option.strike]:
                logger.warning("Overwriting value ")
            self.strike_expiry_chain_call[option.strike][option.expiry] = price
        else:
            self.strike_expiry_chain_call[option.strike] = dict[date, Price]()
            self.strike_expiry_chain_call[option.strike][option.expiry] = price

        # update option.expiry_strike
        if option.expiry in self.expiry_strike_chain_call:
            if option.strike in self.expiry_strike_chain_call[option.expiry]:
                logger.warning("Overwriting value ")
            self.expiry_strike_chain_call[option.expiry][option.strike] = price
        else:
            self.expiry_strike_chain_call[option.expiry] = dict[Amount, Price]()
            self.expiry_strike_chain_call[option.expiry][option.strike] = price

    def _update_put_chain(self, priced_option: PricedOption):
        option = priced_option.option
        price = priced_option.price
        if option.strike in self.strike_expiry_chain_put:
            if self.strike_expiry_chain_put[option.strike]:
                logger.warning("Overwriting value ")
            self.strike_expiry_chain_put[option.strike][option.expiry] = price
        else:
            self.strike_expiry_chain_put[option.strike] = dict[date, Price]()
            self.strike_expiry_chain_put[option.strike][option.expiry] = price

        # update option.expiry_strike
        if option.expiry in self.expiry_strike_chain_put:
            if option.strike in self.expiry_strike_chain_put[option.expiry]:
                logger.warning("Overwriting value ")
            self.expiry_strike_chain_put[option.expiry][option.strike] = price
        else:
            self.expiry_strike_chain_put[option.expiry] = dict[Amount, Price]()
            self.expiry_strike_chain_put[option.expiry][option.strike] = price

    def add_chain(self, other: Chain):
        if other.equity != self.equity:
            raise Exception("Cannot add two chains with different equities")

        for expiry in other.expiry_strike_chain_put:
            if expiry not in self.expiry_strike_chain_put:
                self.expiry_strike_chain_put[expiry] = dict[Amount, Price]()
            for strike in other.expiry_strike_chain_put[expiry]:
                self.expiry_strike_chain_put[expiry][strike] = other.expiry_strike_chain_put[expiry][strike].copy_of()

        for expiry in other.expiry_strike_chain_call:
            if expiry not in self.expiry_strike_chain_call:
                self.expiry_strike_chain_call[expiry] = dict[Amount, Price]()
            for strike in other.expiry_strike_chain_call[expiry]:
                self.expiry_strike_chain_call[expiry][strike] = other.expiry_strike_chain_call[expiry][strike].copy_of()

        for strike in other.strike_expiry_chain_put:
            if strike not in self.strike_expiry_chain_put:
                self.strike_expiry_chain_put[strike] = dict[date, Price]()
            for expiry in other.strike_expiry_chain_put[strike]:
                self.strike_expiry_chain_put[strike][expiry] = other.strike_expiry_chain_put[strike][expiry].copy_of()

        for strike in other.strike_expiry_chain_call:
            if strike not in self.strike_expiry_chain_call:
                self.strike_expiry_chain_call[strike] = dict[date, Price]()
            for expiry in other.strike_expiry_chain_call[strike]:
                self.strike_expiry_chain_call[strike][expiry] = other.strike_expiry_chain_call[strike][expiry].copy_of()

    def to_chain(self):
        return Chain(equity=self.equity, strike_expiry_chain_call=self.strike_expiry_chain_call, expiry_strike_chain_call=self.expiry_strike_chain_call, strike_expiry_chain_put=self.strike_expiry_chain_put, expiry_strike_chain_put=self.expiry_strike_chain_put)