from datetime import datetime

from fastapi import FastAPI

from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_request import \
    CancelManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_response import \
    CancelManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import \
    CreateManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_response import \
    CreateManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_request import \
    GetManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_response import \
    GetManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.list_managed_executions_request import \
    ListManagedExecutionsRequest
from fianchetto_tradebot.common_models.managed_executions.list_managed_executions_response import \
    ListManagedExecutionsResponse
from fianchetto_tradebot.server.common.api.moex.moex_service import MoexService
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.orders.order_service import OrderService
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.service.rest_service import RestService, ETRADE_ONLY_BROKERAGE_CONFIG
from fianchetto_tradebot.server.common.service.service_key import ServiceKey
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

JAN_1_2024 = datetime(2024,1,1).date()
DEFAULT_START_DATE = JAN_1_2024
DEFAULT_COUNT = 100


class MoexRestService(RestService):
    def __init__(self, credential_config_files: dict[Brokerage, str]=ETRADE_ONLY_BROKERAGE_CONFIG):
        super().__init__(ServiceKey.MOEX, credential_config_files)

    @property
    def app(self) -> FastAPI:
        return self._app

    @app.setter
    def app(self, app: FastAPI):
        self._app = app

    def _register_endpoints(self):
        super()._register_endpoints()
        # TODO: See FIA-115 to endpoint consolidation
        self.app.add_api_route(
            path='/api/v1/{brokerage}/accounts/{account_id}/managed-executions/',
            endpoint=self.list_managed_executions, methods=['GET'], response_model=ListManagedExecutionsResponse)
        self.app.add_api_route(
            path='/api/v1/managed-executions/{managed_execution_id}',
            endpoint=self.get_managed_execution, methods=['GET'], response_model=GetManagedExecutionResponse)
        self.app.add_api_route(
            path='/api/v1/managed-executions',
            endpoint=self.create_managed_execution, methods=['POST'], response_model=CreateManagedExecutionResponse)
        self.app.add_api_route(
            path='/api/v1/managed-executions/{managed_execution_id}',
            endpoint=self.cancel_managed_execution, methods=['DELETE'], response_model=CancelManagedExecutionResponse)


    def _setup_brokerage_services(self):
        self.order_services: dict[Brokerage, OrderService] = dict()
        self.quotes_services: dict[Brokerage, QuotesService] = dict()

        # E*Trade
        etrade_key: Brokerage = Brokerage.ETRADE
        etrade_connector: ETradeConnector = self.connectors[Brokerage.ETRADE]
        etrade_order_service = ETradeOrderService(etrade_connector)
        etrade_quotes_service = ETradeQuotesService(etrade_connector)

        self.order_services[etrade_key] = etrade_order_service
        self.quotes_services[etrade_key] = etrade_quotes_service

        # TODO: Add for IKBR and Schwab
        self.moex_service = MoexService(self.quotes_services, self.order_services)

    def list_managed_executions(self, brokerage: str, account_id: str):
        # TODO - FIA-114:
        #  Add filtering on managed executions, e.g: status: str = None, from_date: str=None, to_date: str=None, count:int=DEFAULT_COUNT
        as_brokerage: Brokerage = Brokerage(brokerage)
        accounts_dict = dict[Brokerage, str]()
        accounts_dict[as_brokerage] = account_id
        list_managed_executions_request: ListManagedExecutionsRequest = ListManagedExecutionsRequest(accounts=accounts_dict)
        list_managed_executions_response = self.moex_service.list_managed_executions(list_managed_executions_request=list_managed_executions_request)
        return list_managed_executions_response

    def get_managed_execution(self, managed_execution_id: str)->GetManagedExecutionResponse:
        get_managed_executions_request: GetManagedExecutionRequest = GetManagedExecutionRequest(managed_execution_id=managed_execution_id)
        self.moex_service.get_managed_execution(get_managed_executions_request)
        return GetManagedExecutionResponse()

    def create_managed_execution(self, create_managed_execution_request: CreateManagedExecutionRequest):
        return self.moex_service.create_managed_execution(create_managed_execution_request=create_managed_execution_request)

    def cancel_managed_execution(self, managed_execution_id: str):
        cancel_managed_execution_request: CancelManagedExecutionRequest = CancelManagedExecutionRequest(managed_execution_id=managed_execution_id)
        return self.moex_service.cancel_managed_execution(cancel_managed_execution_request)


if __name__ == "__main__":
    oex_app = MoexRestService()
    oex_app.run(host="0.0.0.0", port=8082)
