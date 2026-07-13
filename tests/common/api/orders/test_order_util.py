import inspect
from datetime import datetime

import pytest
from dateutil.tz import tz

from fianchetto_tradebot.server.common.api.orders.order_util import OrderUtil


class TestOrderUtil:
    @pytest.mark.parametrize('ticker, time, outcome', [
        ("MARA", datetime(2025, 2, 3, 9, 0, tzinfo=tz.gettz('US/Eastern')), False),
        ("MARA", datetime(2025, 2, 3, 16, 1, tzinfo=tz.gettz('US/Eastern')), False),
        ("VIX", datetime(2025, 2, 3, 16, 1, tzinfo=tz.gettz('US/Eastern')), True),
        ("MARA", datetime(2025, 2, 3, 15, 59, 0, tzinfo=tz.gettz('US/Eastern')), True),
        ("MARA", datetime(2025, 2, 2, 15, 59, 0, tzinfo=tz.gettz('US/Eastern')), False),
        ("MARA", datetime(2026, 7, 4, 12, 0, tzinfo=tz.gettz('US/Pacific')), False),
        ("SPY", datetime(2026, 7, 3, 12, 0, tzinfo=tz.gettz('US/Eastern')), False),
        ("SPY", datetime(2026, 7, 6, 12, 0, tzinfo=tz.gettz('US/Eastern')), True),
        ("SPY", datetime(2028, 7, 5, 12, 0, tzinfo=tz.gettz('US/Eastern')), True),
    ]
    )
    def test_is_market_open(self, ticker, time, outcome):
        assert outcome == OrderUtil.is_market_open(ticker, time)

    def test_is_market_open_default_time_is_evaluated_at_call_time(self):
        signature = inspect.signature(OrderUtil.is_market_open)
        assert signature.parameters["current_time"].default is None
