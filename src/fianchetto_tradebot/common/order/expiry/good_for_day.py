import datetime

from fianchetto_tradebot.common.order.expiry.order_expiry import OrderExpiry


class GoodForDay(OrderExpiry):
    def __init__(self):
        super().__init__(expiry_date=datetime.datetime.today().date())

    def __str__(self):
        return f"Good for Day: {self.expiry_date}"
