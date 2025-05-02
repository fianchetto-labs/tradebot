from abc import ABC
from typing import Final

from flask import Flask

from fianchetto_tradebot.common.api.encoding.custom_json_provider import CustomJSONProvider
from fianchetto_tradebot.common.exchange.connector import Connector
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector, DEFAULT_CONFIG_FILE
from fianchetto_tradebot.common.exchange.exchange_name import ExchangeName
from fianchetto_tradebot.common.exchange.ikbr.ikbr_connector import IkbrConnector, DEFAULT_IKBR_CONFIG_FILE
from fianchetto_tradebot.common.exchange.schwab.schwab_connector import SchwabConnector, DEFAULT_SCHWAB_CONFIG_FILE
from fianchetto_tradebot.common.service.service_key import ServiceKey

DEFAULT_EXCHANGE_CONFIGS: Final[dict[ExchangeName, str]] = {
    ExchangeName.ETRADE : DEFAULT_CONFIG_FILE,
    ExchangeName.IKBR : DEFAULT_IKBR_CONFIG_FILE,
    ExchangeName.SCHWAB : DEFAULT_SCHWAB_CONFIG_FILE
}


ETRADE_ONLY_EXCHANGE_CONFIG: Final[dict[ExchangeName, str]] = {
    ExchangeName.ETRADE : DEFAULT_CONFIG_FILE,
}

IKBR_ONLY_EXCHANGE_CONFIG: Final[dict[ExchangeName, str]] = {
    ExchangeName.IKBR : DEFAULT_CONFIG_FILE,
}

SCHWAB_ONLY_EXCHANGE_CONFIG: Final[dict[ExchangeName, str]] = {
    ExchangeName.SCHWAB : DEFAULT_SCHWAB_CONFIG_FILE,
}

class RestService(ABC):
    def __init__(self, service_key: ServiceKey, credential_config_files: dict[ExchangeName, str]):
        self.service_key = service_key
        self._app = Flask(self.service_key)
        self._app.json_provider_class = CustomJSONProvider(self._app)  # Tell Flask to use the custom encoder
        self._app.json = CustomJSONProvider(self._app)
        self._establish_connections(config_files=credential_config_files)
        self._register_endpoints()
        self._setup_exchange_services()

    @property
    def app(self) -> Flask:
        return self._app

    @app.setter
    def app(self, app: Flask):
        self._app = app

    def _establish_connections(self, config_files: dict[ExchangeName, str]):
        self.connectors: dict[ExchangeName, Connector] = dict()

        for exchange, exchange_config_file in config_files.items():
            if exchange == ExchangeName.ETRADE:
                etrade_connector: ETradeConnector = ETradeConnector(config_file=exchange_config_file)
                self.connectors[ExchangeName.ETRADE] = etrade_connector
            elif exchange == ExchangeName.SCHWAB:
                schwab_connector: SchwabConnector = SchwabConnector(config_file=exchange_config_file)
                self.connectors[ExchangeName.SCHWAB] = schwab_connector
            elif exchange == ExchangeName.IKBR:
                ikbr_connector: IkbrConnector = IkbrConnector(config_file=exchange_config_file)
                self.connectors[ExchangeName.IKBR] = ikbr_connector
            else:
                raise Exception(f"Exchange {exchange} not recognized")

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

    def get_root(self):
        return f"{self.service_key.name} Service"

    def health_check(self):
        return f"{self.service_key.name} Service Up"

    def _register_endpoints(self):
        self.app.add_url_rule(rule='/', endpoint='root', view_func=self.get_root, methods=['GET'])
        self.app.add_url_rule(rule='/health-check', endpoint='health-check', view_func=self.health_check, methods=['GET'])


    def _setup_exchange_services(self):
        # Delegated to subclass
        pass

