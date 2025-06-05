from fianchetto_tradebot.common_models.api.request import Request


class GetManagedExecutionRequest(Request):
    # TODO: In theory this may benefit from a Brokerage being specified
    account_id: str
    managed_execution_id: str