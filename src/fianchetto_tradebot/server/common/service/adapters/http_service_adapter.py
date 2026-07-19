from typing import Any

import httpx
from pydantic import BaseModel

from fianchetto_tradebot.server.common.service.adapters.http_service_adapter_error import HttpServiceAdapterError

DEFAULT_HTTP_TIMEOUT_SECONDS = 10.0


class HttpServiceAdapter:
    def __init__(self, base_url: str, client: httpx.Client | None = None, timeout: float = DEFAULT_HTTP_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client()
        self.timeout = timeout

    @staticmethod
    def _json_payload(model: BaseModel) -> dict[str, Any]:
        return model.model_dump(mode="json")

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        response = self.client.request(method, self._url(path), timeout=self.timeout, **kwargs)
        if response.is_error:
            raise HttpServiceAdapterError(
                message=f"{method} {response.url} failed with HTTP {response.status_code}",
                status_code=response.status_code,
                response_text=response.text,
            )
        return response
