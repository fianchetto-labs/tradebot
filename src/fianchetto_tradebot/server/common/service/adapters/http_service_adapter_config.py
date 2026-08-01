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


class HttpServiceAdapterConfigurationError(ValueError):
    pass


def load_http_service_adapter_config(env: Mapping[str, str] = os.environ) -> HttpServiceAdapterConfig:
    return HttpServiceAdapterConfig(
        orders_base_url=_service_url_or_default(
            env,
            ORDERS_SERVICE_URL_ENV_VAR,
            DEFAULT_ORDERS_SERVICE_URL,
        ),
        quotes_base_url=_service_url_or_default(
            env,
            QUOTES_SERVICE_URL_ENV_VAR,
            DEFAULT_QUOTES_SERVICE_URL,
        ),
    )


def load_required_http_service_adapter_config(env: Mapping[str, str] = os.environ) -> HttpServiceAdapterConfig:
    orders_base_url = _service_url_or_none(env, ORDERS_SERVICE_URL_ENV_VAR)
    quotes_base_url = _service_url_or_none(env, QUOTES_SERVICE_URL_ENV_VAR)
    missing_env_vars = [
        env_var
        for env_var, value in (
            (ORDERS_SERVICE_URL_ENV_VAR, orders_base_url),
            (QUOTES_SERVICE_URL_ENV_VAR, quotes_base_url),
        )
        if value is None
    ]

    if missing_env_vars:
        raise HttpServiceAdapterConfigurationError(
            "HTTP service adapter mode requires explicit service URLs: "
            f"{', '.join(missing_env_vars)}. "
            "Set them for deployed service dependencies or use local mode."
        )

    return HttpServiceAdapterConfig(
        orders_base_url=orders_base_url,
        quotes_base_url=quotes_base_url,
    )


def _service_url_or_default(
    env: Mapping[str, str],
    env_var: str,
    default: str,
) -> str:
    return _service_url_or_none(env, env_var) or default


def _service_url_or_none(env: Mapping[str, str], env_var: str) -> str | None:
    value = env.get(env_var)
    if value is None:
        return None

    stripped_value = value.strip()
    if not stripped_value:
        return None

    return stripped_value
