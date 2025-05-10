from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order_line import OrderLine


# TODO: Set up to use Pydantic
class EquityOrderLine(OrderLine):
    def __init__(self, equity: Equity, action: Action,
                 quantity: int):
        if type(equity) != Equity:
            raise Exception(f"Cannot have an EquityOrderLine with type {type(equity)}")
        super().__init__(tradable=equity, action=action, quantity=quantity)
