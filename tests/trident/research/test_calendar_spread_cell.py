import datetime

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.server.trident.research.calendar_spread_constructor import CalendarSpreadCell

expiry_1 = datetime.datetime(2024, 11, 18).date()
expiry_2 = datetime.datetime(2024, 11, 22).date()

option_delta_atm = (Amount(whole=1, part=28, currency=Currency.US_DOLLARS), Amount(whole=1, part=58, currency=Currency.US_DOLLARS))
option_delta_otm = Amount(whole=0, part=27, currency=Currency.US_DOLLARS), Amount(whole=0, part=47, currency=Currency.US_DOLLARS)

class TestCalendarSpreadCell:
    equity = Equity(ticker="SPY", company_name="SPDR")

    def test_division(self):
        cell = CalendarSpreadCell(expiry_1, expiry_2, option_delta_atm, option_delta_otm)
        assert cell.get_price_ratio() == round((1.58 - 1.28)/(.47-.27), 3)

    def test_subtraction(self):
        cell = CalendarSpreadCell(expiry_1, expiry_2, option_delta_atm, option_delta_otm)
        assert cell.get_price_difference() == Amount(whole=0, part=10, currency=Currency.US_DOLLARS)
