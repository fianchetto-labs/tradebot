import datetime

from pydantic import BaseModel

from fianchetto_tradebot.common.finance.amount import Amount


class ExecutionOrderDetails(BaseModel):
    order_value: Amount
    executed_time: datetime.datetime