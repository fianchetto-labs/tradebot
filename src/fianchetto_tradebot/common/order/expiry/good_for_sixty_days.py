from datetime import datetime, timedelta

from fianchetto_tradebot.common.order.expiry.good_until_date import GoodUntilDate


class GoodForSixtyDays(GoodUntilDate):
    def __init__(self):
        super().__init__(expiry_date=datetime.today() + timedelta(days=60))

    def __str__(self):
        return f"Good for Sixty Days: {self.expiry_date}"
