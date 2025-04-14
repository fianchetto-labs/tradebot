
from fianchetto_tradebot.common.order.executed_order_details import ExecutionOrderDetails
from fianchetto_tradebot.common.order.placed_order import PlacedOrder


class ExecutedOrder:
    def __init__(self, order: PlacedOrder, execution_order_details: ExecutionOrderDetails):
        self.order = order
        self.execution_details = execution_order_details

    def get_order(self):
        return self.order