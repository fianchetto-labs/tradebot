from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order_line import OrderLine

# TODO: Set up to use Pydantic
class OptionOrderLine(OrderLine):
    def __init__(self, option: Option, action: Action,
                 quantity: int):
        if type(option) != Option:
            raise Exception(f"Cannot have an OptionOrderLine with type {type(option)}")
        super().__init__(option, action, quantity)
