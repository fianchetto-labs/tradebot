import datetime

from fianchetto_tradebot.common.order.expiry.order_expiry import OrderExpiry


class FillOrKill(OrderExpiry):

    def __init__(self):
        five_seconds_from_now = datetime.datetime.now() + datetime.timedelta(seconds=5)
        super().__init__(expiry_date=five_seconds_from_now, all_or_none=False)

    def __str__(self):
        return f"Fill or Kill: {self.expiry_date}"
