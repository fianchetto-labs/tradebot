from fianchetto_tradebot.common.order.expiry.order_expiry import OrderExpiry


class GoodUntilDate(OrderExpiry):
    def __str__(self):
        return f"Good for until Date: {self.expiry_date}. All-or-none: {self.all_or_none}"
