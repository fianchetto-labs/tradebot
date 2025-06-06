from fianchetto_tradebot.common_models.api.request import Request


class GetManagedExecutionRequest(Request):
    managed_execution_id: str