import logging

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.priced_option import PricedOption
from fianchetto_tradebot.common.finance.option_type import OptionType
import datetime

logger = logging.getLogger(__name__)


class Chain:

    def __init__(self, equity: Equity):
        self.equity: Equity = equity
        # keyed on strike then date
        self.strike_expiry_chain_call: dict[datetime, dict[Amount, Price]] = dict()
        self.expiry_strike_chain_call: dict[Amount, dict[datetime, Price]] = dict()

        # keyed on date then strike
        self.strike_expiry_chain_put: dict[datetime, dict[Amount, Price]] = dict()
        self.expiry_strike_chain_put: dict[Amount, dict[datetime, Price]] = dict()

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

    def print(self, expiry: datetime):

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
            self.strike_expiry_chain_call[option.strike] = dict()
            self.strike_expiry_chain_call[option.strike][option.expiry] = price

        # update option.expiry_strike
        if option.expiry in self.expiry_strike_chain_call:
            if option.strike in self.expiry_strike_chain_call[option.expiry]:
                logger.warning("Overwriting value ")
            self.expiry_strike_chain_call[option.expiry][option.strike] = price
        else:
            self.expiry_strike_chain_call[option.expiry] = dict()
            self.expiry_strike_chain_call[option.expiry][option.strike] = price

    def _update_put_chain(self, priced_option: PricedOption):
        option = priced_option.option
        price = priced_option.price
        if option.strike in self.strike_expiry_chain_put:
            if self.strike_expiry_chain_put[option.strike]:
                logger.warning("Overwriting value ")
            self.strike_expiry_chain_put[option.strike][option.expiry] = price
        else:
            self.strike_expiry_chain_put[option.strike] = dict()
            self.strike_expiry_chain_put[option.strike][option.expiry] = price

        # update option.expiry_strike
        if option.expiry in self.expiry_strike_chain_put:
            if option.strike in self.expiry_strike_chain_put[option.expiry]:
                logger.warning("Overwriting value ")
            self.expiry_strike_chain_put[option.expiry][option.strike] = price
        else:
            self.expiry_strike_chain_put[option.expiry] = dict()
            self.expiry_strike_chain_put[option.expiry][option.strike] = price

    def add_chain(self, other):
        if other.equity != self.equity:
            raise Exception("Cannot add two chains with different equities")

        for expiry in other.expiry_strike_chain_put:
            if expiry not in self.expiry_strike_chain_put:
                self.expiry_strike_chain_put[expiry] = dict()
            for strike in other.expiry_strike_chain_put[expiry]:
                self.expiry_strike_chain_put[expiry][strike] = other.expiry_strike_chain_put[expiry][strike].copy_of()

        for expiry in other.expiry_strike_chain_call:
            if expiry not in self.expiry_strike_chain_call:
                self.expiry_strike_chain_call[expiry] = dict()
            for strike in other.expiry_strike_chain_call[expiry]:
                self.expiry_strike_chain_call[expiry][strike] = other.expiry_strike_chain_call[expiry][strike].copy_of()

        for strike in other.strike_expiry_chain_put:
            if strike not in self.strike_expiry_chain_put:
                self.strike_expiry_chain_put[strike] = dict()
            for expiry in other.strike_expiry_chain_put[strike]:
                self.strike_expiry_chain_put[strike][expiry] = other.strike_expiry_chain_put[strike][expiry].copy_of()

        for strike in other.strike_expiry_chain_call:
            if strike not in self.strike_expiry_chain_call:
                self.strike_expiry_chain_call[strike] = dict()
            for expiry in other.strike_expiry_chain_call[strike]:
                self.strike_expiry_chain_call[strike][expiry] = other.strike_expiry_chain_call[strike][expiry].copy_of()