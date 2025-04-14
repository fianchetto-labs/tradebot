import datetime

from fianchetto_tradebot.common.finance.amount import Amount


class ExecutionOrderDetails:
    def __init__(self, order_value: Amount, executed_time: datetime.datetime):
        self.order_value: Amount = order_value
        self.executed_time: datetime.datetime = executed_time