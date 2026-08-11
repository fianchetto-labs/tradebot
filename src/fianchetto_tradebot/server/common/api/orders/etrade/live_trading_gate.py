from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlparse

ETRADE_LIVE_WRITES_ENABLED_ENV_VAR = "TRADEBOT_ALLOW_LIVE_ETRADE_WRITES"
LIVE_ETRADE_HOSTS = {"api.etrade.com"}
TRUE_VALUES = {"1", "true", "yes", "on"}


def require_live_etrade_write_enabled(
    base_url: str,
    operation: str,
    env: Mapping[str, str] | None = None,
) -> None:
    if not _is_live_etrade_base_url(base_url):
        return

    env = env if env is not None else os.environ
    if env.get(ETRADE_LIVE_WRITES_ENABLED_ENV_VAR, "").strip().lower() in TRUE_VALUES:
        return

    raise PermissionError(
        f"Live E*Trade {operation} is disabled. "
        f"Set {ETRADE_LIVE_WRITES_ENABLED_ENV_VAR}=true to enable live brokerage writes."
    )


def _is_live_etrade_base_url(base_url: str) -> bool:
    parsed_url = urlparse(base_url)
    return parsed_url.hostname in LIVE_ETRADE_HOSTS
