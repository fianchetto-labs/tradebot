import os
from dataclasses import dataclass
from typing import Mapping

DEFAULT_ORDERS_SERVICE_URL = "http://localhost:8080"
DEFAULT_QUOTES_SERVICE_URL = "http://localhost:8081"
ORDERS_SERVICE_URL_ENV_VAR = "TRADEBOT_ORDERS_SERVICE_URL"
QUOTES_SERVICE_URL_ENV_VAR = "TRADEBOT_QUOTES_SERVICE_URL"


@dataclass(frozen=True)
class HttpServiceAdapterConfig:
    orders_base_url: str = DEFAULT_ORDERS_SERVICE_URL
    quotes_base_url: str = DEFAULT_QUOTES_SERVICE_URL


def load_http_service_adapter_config(env: Mapping[str, str] = os.environ) -> HttpServiceAdapterConfig:
    return HttpServiceAdapterConfig(
        orders_base_url=env.get(ORDERS_SERVICE_URL_ENV_VAR, DEFAULT_ORDERS_SERVICE_URL),
        quotes_base_url=env.get(QUOTES_SERVICE_URL_ENV_VAR, DEFAULT_QUOTES_SERVICE_URL),
    )
