from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution


class CreateManagedExecutionRequest(Request):
    account_id: str
    managed_execution: ManagedExecution
