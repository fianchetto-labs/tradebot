from datetime import datetime

import pytest
from dateutil.tz import tz

from fianchetto_tradebot.common.api.orders.order_util import OrderUtil


class TestOrderUtil:
    @pytest.mark.parametrize('ticker, time, outcome', [
        ("MARA", datetime(2025, 2,2,9,0, tzinfo=tz.gettz('US/Pacific')), False),
        ("MARA", datetime(2025, 2, 2, 16, 1, tzinfo=tz.gettz('US/Pacific')), False),
        ("VIX", datetime(2025, 2, 2, 16, 1, tzinfo=tz.gettz('US/Pacific')), True),
        ("MARA", datetime(2025, 2, 2, 15, 59, 0, tzinfo=tz.gettz('US/Pacific')), True),
        ("MARA", datetime(2026, 7, 4, 12, 0, tzinfo=tz.gettz('US/Pacific')), False),
        ("SPY", datetime(2026, 7, 4, 12, 0, tzinfo=tz.gettz('US/Pacific')), False),
        ("SPY", datetime(2026, 7, 5, 12, 0, tzinfo=tz.gettz('US/Pacific')), True)
    ]
    )
    def test_is_market_open(self, ticker, time, outcome):
        assert outcome == OrderUtil.is_exchange_open(ticker, time)