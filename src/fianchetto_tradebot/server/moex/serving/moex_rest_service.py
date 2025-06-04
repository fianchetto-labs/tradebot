from datetime import datetime

from fastapi import FastAPI

from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_response import \
    CancelManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import \
    CreateManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_response import \
    CreateManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_response import \
    GetManagedExecutionResponse
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
        self.app.add_api_route(
            path='/api/v1/{brokerage}/accounts/{account_id}/managed-executions/',
            endpoint=self.list_managed_executions, methods=['GET'], response_model=ListManagedExecutionsResponse)
        self.app.add_api_route(
            path='/api/v1/{brokerage}/accounts/{account_id}/managed-executions/{managed_execution_id}',
            endpoint=self.get_managed_execution, methods=['GET'], response_model=GetManagedExecutionResponse)
        self.app.add_api_route(
            path='/api/v1/{brokerage}/accounts/{account_id}/managed-executions',
            endpoint=self.create_managed_execution, methods=['POST'], response_model=CreateManagedExecutionResponse)
        self.app.add_api_route(
            path='/api/v1/{brokerage}/accounts/{account_id}/managed-executions/{managed_execution_id}',
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

    ### Managed Executions - to be cleaved off into a separate service
    def list_managed_executions(self, brokerage: str, account_id: str, status: str = None, from_date: str=None, to_date: str=None, count:int=DEFAULT_COUNT):
        return ListManagedExecutionsResponse()

    def get_managed_execution(self, brokerage: str, account_id: str, managed_execution_id: str)->GetManagedExecutionResponse:
        return GetManagedExecutionResponse()

    def create_managed_execution(self, brokerage: str, account_id: str, create_managed_execution_request: CreateManagedExecutionRequest):
        return self.moex_service.create_managed_execution(create_managed_execution_request=create_managed_execution_request)

    def cancel_managed_execution(self, brokerage: str, account_id: str):
        return CancelManagedExecutionResponse()


if __name__ == "__main__":
    oex_app = MoexRestService()
    oex_app.run(host="0.0.0.0", port=8082)
