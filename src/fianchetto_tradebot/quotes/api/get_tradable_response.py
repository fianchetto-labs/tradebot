from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from fianchetto_tradebot.common.api.finance.greeks.greeks import Greeks
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.api.response import Response


class GetTradableResponse(Response, BaseModel):
    tradable: Tradable
    response_time: Optional[datetime] = None
    current_price: Price
    volume: int
    greeks: Optional[Greeks] = None
