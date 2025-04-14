from fianchetto_tradebot.common.finance.options.equity_order_line import EquityOrderLine
from fianchetto_tradebot.common.finance.options.option_order import OptionOrder
from fianchetto_tradebot.common.finance.options.option_order_line import OptionOrderLine
from fianchetto_tradebot.common.order.order_price import OrderPrice


class BuyWrite(OptionOrder):
    def __init__(self, order_price: OrderPrice, equity: EquityOrderLine, options: list[OptionOrderLine], margin_capital_requirement = 1):
        if len(options) != 1:
            raise Exception("Buy-writes should only have one option leg")
        self.equity = equity

        # In the case that margin trading is supported, a trader may only be required to put up a portion
        self.margin_capital_requirement: float = 1.0
        super().__init__(order_price, options)
