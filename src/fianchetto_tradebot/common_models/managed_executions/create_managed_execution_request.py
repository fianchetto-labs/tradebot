from pydantic import ConfigDict

from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution


class CreateManagedExecutionRequest(Request):
    account_id: str
    managed_execution: ManagedExecution

    def model_dump_json(self, **kwargs):
        return super().model_dump_json(
            **kwargs,
            fallback=self._fallback
        )

    @staticmethod
    def _fallback(obj):
        if isinstance(obj, type):
            return obj.__name__
        raise TypeError(f"Cannot serialize object of type {type(obj).__name__}")