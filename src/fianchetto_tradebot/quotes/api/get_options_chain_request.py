from datetime import datetime

from fianchetto_tradebot.common.finance.equity import Equity


class GetOptionsChainRequest:
    def __init__(self, equity: Equity, expiry: datetime.date):
        # Perhaps a date will also be required
        self.equity = equity
        self.expiry: datetime.date = expiry