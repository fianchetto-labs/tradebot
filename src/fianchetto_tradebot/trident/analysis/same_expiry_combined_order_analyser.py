import itertools

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order import Order
from fianchetto_tradebot.common.order.order_line import OrderLine
from fianchetto_tradebot.common.order.tradable_type import TradableType


class SameDayExpiryCombinedOrderAnalyser:
    def __init__(self, equity: Equity, orders: list[Order]):
        self.equity = equity
        self.orders: list[Order] = orders

        expiries = set()

        current_order_price: Amount = Amount(whole=0, part=0)
        for order in orders:
            order_amt: Amount = order.order_price.to_amount()
            current_order_price += order_amt
            for order_line in order.order_lines:
                if isinstance(order_line.tradable, Option):
                    option: Option = order_line.tradable
                    expiries.add(option.expiry)

        if len(expiries) != 1:
            raise Exception("All expiry dates must be the same")

        self.order_price = current_order_price

    def get_margin_equity_required(self) -> Amount:
        # The naive approach would be to go through all the orders and add/subtract their M/E's.
        # However, a full spread put/call spread would only take the max of the two
        # It also might be exchange-specific. RH and E*Trade treat some condors differently.
        return Amount(0, 0)

    def get_max_gain(self):
        # TODO: Implement this
        return Amount(0,0)

    def get_max_loss(self):
        # TODO: Implement this
        return Amount(0,0)

    def get_pl_for_given_price_at_expiry(self, at_price: float) -> Amount:
        value_at_price: Amount = self.get_value_for_given_price_at_expiry(at_price)
        order_price_amt: Amount = self.order_price * 100
        return_value = value_at_price + order_price_amt
        return return_value

    # This assumes that all options have the same expiry
    # This is harder to computer for equities and/or buy-writes. But for pure options, it's easy
    def get_value_for_given_price_at_expiry(self, at_price: float) -> Amount:
        # So it's literally just computing strikes against ending price

        nested_option_order_lines: list[list[OrderLine]] = [[order_line for order_line in order.order_lines if order_line.tradable.get_type() ==  TradableType.Option] for order in self.orders]
        nested_equity_order_lines: list[list[OrderLine]] = [
            [order_line for order_line in order.order_lines if order_line.tradable.get_type() == TradableType.Equity]
            for order in self.orders]

        option_order_lines: list[OrderLine] = list(itertools.chain(*nested_option_order_lines))
        equity_order_lines: list[OrderLine] = list(itertools.chain(*nested_equity_order_lines))

        option_iv_value = SameDayExpiryCombinedOrderAnalyser.get_option_iv_value(option_order_lines, at_price)
        equity_value = SameDayExpiryCombinedOrderAnalyser.get_equity_value(equity_order_lines, at_price)
        per_contract_iv_value = option_iv_value * 100 + equity_value

        return Amount.from_float(per_contract_iv_value)

    @staticmethod
    def get_equity_value(order_lines: list[OrderLine], at_price: float)->float:
        iv: float = 0
        for order_line in order_lines:
            quantity = order_line.quantity
            value = at_price * quantity
            iv += value

        return iv

    @staticmethod
    def get_option_iv_value(order_lines: list[OrderLine], at_price: float)->float:
        iv: float = 0
        for order_line in order_lines:
            quantity = order_line.quantity if Action.is_long(Action[order_line.action]) else -1 * order_line.quantity
            option: Option = order_line.tradable
            value = max(option.strike.to_float() - at_price, 0) if option.type == OptionType.PUT else max(
                at_price - option.strike.to_float(), 0)
            iv += quantity * value

        return iv