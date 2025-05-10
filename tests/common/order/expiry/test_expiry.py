import datetime

from fianchetto_tradebot.common_models.order.expiry.fill_or_kill import FillOrKill
from fianchetto_tradebot.common_models.order.expiry.good_for_sixty_days import GoodForSixtyDays


def test_fill_or_kill_is_all_or_nothing():
    expiry = FillOrKill()

    assert not expiry.all_or_none


def test_fill_or_kill_correct_expiry():
    now = datetime.datetime.now()
    fok = FillOrKill()

    assert fok.valid_at(now + datetime.timedelta(seconds=3))
    assert fok.valid_at(now + datetime.timedelta(seconds=10)) is False


def test_good_for_sixty_days():
    now: datetime = datetime.datetime.now()
    good_for_sixty_days_expiry: GoodForSixtyDays = GoodForSixtyDays()

    assert good_for_sixty_days_expiry.valid_at(now + datetime.timedelta(seconds=3))
    assert good_for_sixty_days_expiry.valid_at(now + datetime.timedelta(seconds=10))
    assert good_for_sixty_days_expiry.valid_at((now + datetime.timedelta(days=59)))
    assert good_for_sixty_days_expiry.valid_at((now + datetime.timedelta(days=61))) == False
