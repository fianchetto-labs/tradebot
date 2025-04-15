from abc import ABC
from datetime import datetime, timedelta

from fianchetto_tradebot.common.api.orders.order_list_request import ListOrdersRequest
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.exchange.connector import Connector
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.order.placed_order import PlacedOrder

TWO_WEEKS_AGO = datetime.date=(datetime.today().date() - timedelta(days=14))
TODAY = datetime.today().date()

class Trader(ABC):
    def __init__(self, connector: Connector):
        self.connector: Connector = connector
        self.order_service: OrderService = OrderService(connector)

    def get_all_open_trades(self, account_id: str, from_date: datetime.date=TWO_WEEKS_AGO, to_date: datetime.date = TODAY) -> list[PlacedOrder]:
        # By default, we'll get trades from the last two weeks
        list_orders_request: ListOrdersRequest = ListOrdersRequest(account_id, status=OrderStatus.OPEN, from_date=from_date, to_date=to_date)
        return self.order_service.list_orders(list_orders_request).order_list

    def get_all_open_trades_for_symbol(self, equity: Equity):
        pass

    def get_options_chain(self):
        pass

    def get_option_details(self):
        pass

