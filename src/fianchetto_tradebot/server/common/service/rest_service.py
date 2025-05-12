from abc import ABC
from typing import Final

import uvicorn
from fastapi import FastAPI, APIRouter

from fianchetto_tradebot.server.common.brokerage.connector import Connector
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector, DEFAULT_CONFIG_FILE
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.server.common.brokerage.ikbr.ikbr_connector import IkbrConnector, DEFAULT_IKBR_CONFIG_FILE
from fianchetto_tradebot.server.common.brokerage.schwab.schwab_connector import SchwabConnector, DEFAULT_SCHWAB_CONFIG_FILE
from fianchetto_tradebot.server.common.service.service_key import ServiceKey

DEFAULT_BROKERAGE_CONFIGS: Final[dict[Brokerage, str]] = {
    Brokerage.ETRADE : DEFAULT_CONFIG_FILE,
    Brokerage.IKBR : DEFAULT_IKBR_CONFIG_FILE,
    Brokerage.SCHWAB : DEFAULT_SCHWAB_CONFIG_FILE
}

ETRADE_ONLY_BROKERAGE_CONFIG: Final[dict[Brokerage, str]] = {
    Brokerage.ETRADE : DEFAULT_CONFIG_FILE,
}

IKBR_ONLY_BROKERAGE_CONFIG: Final[dict[Brokerage, str]] = {
    Brokerage.IKBR : DEFAULT_CONFIG_FILE,
}

SCHWAB_ONLY_BROKERAGE_CONFIG: Final[dict[Brokerage, str]] = {
    Brokerage.SCHWAB : DEFAULT_SCHWAB_CONFIG_FILE,
}


class RestService(ABC):
    def __init__(self, service_key: ServiceKey, credential_config_files: dict[Brokerage, str]):
        self.service_key = service_key
        self.app = FastAPI()
        self.router = APIRouter()
        self._establish_connections(config_files=credential_config_files)
        self._register_endpoints()
        self._setup_brokerage_services()

    def _register_endpoints(self):
        self.app.add_api_route(path="/health-check", endpoint=self.health_check, methods=['GET'])
        self.app.add_api_route(path="/", endpoint=self.get_root, methods=['GET'])

    def _establish_connections(self, config_files: dict[Brokerage, str]):
        self.connectors: dict[Brokerage, Connector] = dict()

        for brokerage, brokerage_config_file in config_files.items():
            if brokerage == Brokerage.ETRADE:
                etrade_connector: ETradeConnector = ETradeConnector(config_file=brokerage_config_file)
                self.connectors[Brokerage.ETRADE] = etrade_connector
            elif brokerage == Brokerage.SCHWAB:
                schwab_connector: SchwabConnector = SchwabConnector(config_file=brokerage_config_file)
                self.connectors[Brokerage.SCHWAB] = schwab_connector
            elif brokerage == Brokerage.IKBR:
                ikbr_connector: IkbrConnector = IkbrConnector(config_file=brokerage_config_file)
                self.connectors[Brokerage.IKBR] = ikbr_connector
            else:
                raise Exception(f"Brokerage {brokerage} not recognized")

    def run(self, *args, **kwargs):
        uvicorn.run(self.app, *args, **kwargs)

    def get_root(self):
        return f"{self.service_key.name} Service"

    def health_check(self):
        return f"{self.service_key.name} Service Up"

    def _setup_brokerage_services(self):
        # Delegated to subclass
        pass