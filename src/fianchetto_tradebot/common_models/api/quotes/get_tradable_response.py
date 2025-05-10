from datetime import datetime
from typing import Optional, Union

from fianchetto_tradebot.common_models.api.finance.greeks.greeks import Greeks
from fianchetto_tradebot.common_models.api.response import Response
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.price import Price


class GetTradableResponse(Response):
    tradable: Union[Equity, Option]
    response_time: Optional[datetime] = None
    current_price: Price
    volume: int
    greeks: Optional[Greeks] = None
