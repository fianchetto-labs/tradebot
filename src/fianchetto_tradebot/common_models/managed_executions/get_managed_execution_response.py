from typing import Optional

from fianchetto_tradebot.common_models.api.response import Response
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution


class GetManagedExecutionResponse(Response):
    managed_execution: Optional[ManagedExecution] = None