from datetime import datetime
from typing import Optional, Union

from fianchetto_tradebot.common.api.finance.greeks.greeks import Greeks
from fianchetto_tradebot.common.api.response import Response
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.price import Price


class GetTradableResponse(Response):
    tradable: Union[Equity, Option]
    response_time: Optional[datetime] = None
    current_price: Price
    volume: int
    greeks: Optional[Greeks] = None
