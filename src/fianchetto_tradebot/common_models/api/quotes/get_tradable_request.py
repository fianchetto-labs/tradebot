from pydantic import BaseModel

from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.finance.tradable import Tradable


class GetTradableRequest(Request):
    tradable: Tradable

    def get_tradable(self):
        return self.tradable

    def __eq__(self, other):
        if other.tradable != self.tradable:
            return False
        return True