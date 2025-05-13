from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_response import \
    CancelManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import \
    CreateManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_response import \
    GetManagedExecutionResponse
from fianchetto_tradebot.server.common.api.orders.order_service import OrderService
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService


class MoexService:
    def __init__(self, quotes_services: dict[Brokerage, QuotesService], orders_services: dict[Brokerage, OrderService]):
        self.quotes_services: dict[Brokerage, QuotesService] = quotes_services
        self.orders_services: dict[Brokerage, OrderService] = orders_services

        # Managed data structure
        self.managed_executions = dict[str, ManagedExecution]()



    ### Managed Executions - to be cleaved off into a separate service
    def list_managed_executions(self, brokerage: str, account_id: str, status: str = None, from_date: str=None, to_date: str=None, count:int=50):

        return None

    def get_managed_execution(self, brokerage: str, account_id: str, managed_execution_id: str)->GetManagedExecutionResponse:
        return None

    def create_managed_execution(self, brokerage: str, account_id: str, create_managed_execution_request: CreateManagedExecutionRequest)->GetManagedExecutionResponse:
        return None

    def cancel_managed_execution(self, brokerage: str, account_id: str)->CancelManagedExecutionResponse:
        return None

