from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order_line import OrderLine


class EquityOrderLine(OrderLine):
    def __init__(self, option: Equity, action: Action,
                 quantity: int):
        if type(option) != Equity:
            raise Exception(f"Cannot have an EquityOrderLine with type {type(option)}")
        super().__init__(option, action, quantity)
