import copy

from pydantic import BaseModel

from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.expiry.order_expiry import OrderExpiry
from fianchetto_tradebot.common.order.order_line import OrderLine
from fianchetto_tradebot.common.order.order_price import OrderPrice
from fianchetto_tradebot.common.order.order_type import OrderType
from fianchetto_tradebot.common.order.tradable_type import TradableType

# TODO: Add ratio
class Order(BaseModel):
    expiry: OrderExpiry
    order_lines: list[OrderLine]
    order_price: OrderPrice

    def __eq__(self, other):
        if self.expiry != other.expiry:
            return False
        if self.order_price != other.order_price:
            return False
        if len(self.order_lines) != len(other.order_lines):
            return False
        ols = set[OrderLine]()
        for order_line in other.order_lines:
            ols.add(order_line)
        for order_line in self.order_lines:
            if order_line not in ols:
                return False

        return True

    # TODO: Move this into a util class
    def get_order_type(self)->OrderType:
        equity_types: list[TradableType] = [order_line.tradable.get_type() for order_line in self.order_lines]

        # No Options:
        if TradableType.Option not in equity_types:
            return OrderType.EQ

        # Mixed
        if TradableType.Equity in equity_types:
            if len(equity_types) == 2:
                return OrderType.BUY_WRITES
            else:
                # this is more complicated
                # it'd be a buy-write and maybe a Spread?
                # TODO: Figure this case out
                return OrderType.BUY_WRITES

        # Only Options
        # Now we need more info
        options: list[(Option, Action)] = [(order_line.tradable, order_line.action) for order_line in self.order_lines]

        # TODO: Be clever here, maybe. Otherwise, just enumerate the types
        option_types : list[(OptionType, Action)] = [(option[0], option[1]) for option in options]

        # TODO: This is for the ratios. Finish later.
        num_puts = sum(1 for option in option_types if option[0].type == OptionType.PUT)
        num_calls = sum(1 for option in option_types if option[0].type == OptionType.CALL)



        return OrderType.SPREADS

    def __copy__(self):
        return Order(self.order_id, self.expiry, copy.deepcopy(self.order_lines), self.order_price)