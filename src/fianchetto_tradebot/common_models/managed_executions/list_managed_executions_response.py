from fianchetto_tradebot.common_models.api.response import Response
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution


class ListManagedExecutionsResponse(Response):
    managed_executions_list: list[ManagedExecution]

    def get_managed_execution_list(self) -> list[ManagedExecution]:
        return self.managed_executions_list

    def __str__(self):
        return f"Managed Execution List: {str(self.managed_executions_list)}"

    def __repr__(self):
        return self.__str__()