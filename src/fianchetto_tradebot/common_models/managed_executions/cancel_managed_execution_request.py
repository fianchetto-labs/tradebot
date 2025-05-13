from fianchetto_tradebot.common_models.api.request import Request


class CancelManagedExecutionRequest(Request):
    managed_execution_id: str
