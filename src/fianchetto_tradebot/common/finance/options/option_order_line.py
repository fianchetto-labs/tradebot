from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order_line import OrderLine


class OptionOrderLine(OrderLine):
    def __init__(self, option: Option, action: Action,
                 quantity: int):
        if type(option) != Option:
            raise Exception(f"Cannot have an OptionOrderLine with type {type(option)}")
        super().__init__(option, action, quantity)
