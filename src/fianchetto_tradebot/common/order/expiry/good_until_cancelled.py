from fianchetto_tradebot.common.order.expiry.order_expiry import OrderExpiry


class GoodUntilCancelled(OrderExpiry):
    def __init__(self, all_or_none: bool=False):
        super().__init__(expiry_date=None, all_or_none=all_or_none)

    def __str__(self):
        return f"Good for until cancelled. All-or-none: {self.all_or_none}"
