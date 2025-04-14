from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.options.option_order import OptionOrder, NAKED_CALL_REQUIRED_COLLATERAL_MULTIPLIER
from fianchetto_tradebot.common.finance.options.option_order_line import OptionOrderLine
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order_price import OrderPrice
from fianchetto_tradebot.common.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common.order.order_type import OrderType

DE_NORMALIZATION_CONSTANT = 100

class Spread(OptionOrder):
    def __init__(self, order_price: OrderPrice, options: list[OptionOrderLine]):
        if len(options) != 2:
            raise Exception("A spread requires exactly two ")
        super().__init__(order_price, options)

        self.o_1: OptionOrderLine = options[0]
        self.o_2: OptionOrderLine = options[1]

        self.option_1: Option = self.o_1.tradable
        self.action_1: Action = self.o_1.action
        self.option_2: Option = self.o_2.tradable
        self.action_2: Action = self.o_2.action

        if self.option_1.type != self.option_2.type:
            raise Exception("A spread needs to have the same OptionType.")

        self.spread_option_type = self.option_1.type

        if self.action_1 == self.action_2:
            raise Exception("A spread needs both a long and a short leg.")

        if self.o_1.quantity != self.o_2.quantity:
            raise Exception(f"A spread needs to be balanced, but this is not: {self.o_1.quantity} vs. {self.o_2.quantity}")

        if self.option_1.equity != self.option_2.equity:
            raise Exception(f"A spread needs to be against the same underlying.")

    def get_collateral_required(self) -> Amount:
        short_long: (Option, Option) = (self.o_1.tradable, self.o_2.tradable) if Action.is_short(Action[self.action_1]) else (self.o_2.tradable, self.o_1.tradable)
        short_option, long_option = short_long

        short_strike = short_option.strike
        long_strike = long_option.strike

        order_credit_debit: Amount = self.order_price.price * -1 if self.order_price.order_price_type == OrderPriceType.NET_DEBIT else self.order_price.price
        if short_option.expiry > long_option.expiry:
            # This is a naked situation
            if self.spread_option_type == OptionType.PUT:
                # Credit positive, debit negative
                return (short_option.strike - order_credit_debit) * DE_NORMALIZATION_CONSTANT
            else:
                return (short_option.strike * NAKED_CALL_REQUIRED_COLLATERAL_MULTIPLIER - order_credit_debit) * DE_NORMALIZATION_CONSTANT
        else:
            if self.spread_option_type == OptionType.PUT:
                if short_strike > long_strike:
                    # classic cash-secured put spread
                    return (short_strike - order_credit_debit)*DE_NORMALIZATION_CONSTANT
                else:
                    # The assumption is that it must be debit
                    if self.order_price.order_price_type != OrderPriceType.NET_DEBIT:
                        raise Exception(f"Implausible configuration to take a net credit with short option {short_option} and long option {long_option}")
                    return self.order_price.price * DE_NORMALIZATION_CONSTANT
            else:
                if short_strike < long_strike:
                    # classic cash-secured put spread
                    return (long_strike - short_strike - order_credit_debit) * DE_NORMALIZATION_CONSTANT
                else:
                    # The assumption is that it must be debit
                    if self.order_price.order_price_type != OrderPriceType.NET_DEBIT:
                        raise Exception(f"Implausible configuration to take a net credit with short option {short_option} and long option {long_option}")
                    return self.order_price.price * DE_NORMALIZATION_CONSTANT


    def get_order_type(self):
        return OrderType.SPREADS