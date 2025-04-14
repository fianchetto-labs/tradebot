import datetime
from typing import Optional

from pydantic import BaseModel

from fianchetto_tradebot.common.exchange.market_session import MarketSession
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.order.order_status import OrderStatus


class PlacedOrderDetails(BaseModel):
    account_id: str
    exchange_order_id: str
    status: OrderStatus
    order_placed_time: datetime.datetime
    current_market_price: Price
    market_session: Optional[MarketSession] = MarketSession.REGULAR
    replaces_order_id: Optional[str] = None
