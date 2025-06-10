from fianchetto_tradebot.common_models.api.response import Response
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution


class CancelManagedExecutionResponse(Response):
    managed_execution: ManagedExecution
    # TODO: Consider adding a timestamp or maybe some kind of audit history