from pydantic import BaseModel

from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.api.request import Request


class GetTradableRequest(Request, BaseModel):
    tradable: Tradable

    def get_tradable(self):
        return self.tradable

    def __eq__(self, other):
        if other.tradable != self.tradable:
            return False
        return True