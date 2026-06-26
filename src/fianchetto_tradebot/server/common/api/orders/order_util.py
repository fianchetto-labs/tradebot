import string
from datetime import datetime, time
from random import choices

from dateutil.tz import tz

EASTERN_TZ = tz.gettz('US/Eastern')
EXTENDED_15_MINS_TICKERS = ["VIX", "VIXW", "SPY", "GLD"]


MARKET_CLOSED_DAYS_2025 = [
    datetime(2025, 1, 1, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 1, 20, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 2, 17, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 4, 18, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 5, 26, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 6, 19, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 7, 4, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 9, 1, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 11, 27, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2025, 12, 25, tzinfo=tz.gettz('US/Pacific')).date()
]

MARKET_CLOSED_DAYS_2026 = [
    datetime(2026, 1, 1, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 1, 19, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 2, 16, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 4, 3, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 5, 25, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 6, 19, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 7, 3, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 9, 7, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 11, 26, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2026, 12, 25, tzinfo=tz.gettz('US/Pacific')).date()
]

MARKET_CLOSED_DAYS_2027 = [
    datetime(2027, 1, 1, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 1, 18, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 2, 15, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 3, 26, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 5, 31, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 6, 18, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 7, 5, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 9, 6, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 11, 25, tzinfo=tz.gettz('US/Pacific')).date(),
    datetime(2027, 12, 24, tzinfo=tz.gettz('US/Pacific')).date()
]

MARKET_CLOSED_DAYS = {
    2025: MARKET_CLOSED_DAYS_2025,
    2026: MARKET_CLOSED_DAYS_2026,
    2027: MARKET_CLOSED_DAYS_2027
}

class OrderUtil:
    @staticmethod
    def generate_random_client_order_id():
        return "".join(choices(string.ascii_uppercase + string.digits, k=15))

    @staticmethod
    def is_market_open(symbol: str, current_time: datetime = None):
        # Market hours are expressed in US Eastern Time.
        input_time = _as_eastern(current_time or datetime.now(tz=EASTERN_TZ))
        current_year = input_time.year

        if input_time.weekday() >= 5:
            return False

        if input_time.date() in MARKET_CLOSED_DAYS.get(current_year, []):
            return False

        # Market closed to the day
        if input_time.time() >= time(16, 0) and not after_hours_exception(symbol, input_time):
            return False

        # Market not yet open for the day
        if input_time.time() < time(9, 30):
            return False

        return True

def after_hours_exception(symbol: str, now_eastern: datetime)->bool:
    return symbol.upper() in EXTENDED_15_MINS_TICKERS and now_eastern.time() > time(16, 0) and now_eastern.time() < time(16, 15)


def _as_eastern(input_time: datetime) -> datetime:
    if input_time.tzinfo is None:
        return input_time.replace(tzinfo=EASTERN_TZ)
    return input_time.astimezone(EASTERN_TZ)
