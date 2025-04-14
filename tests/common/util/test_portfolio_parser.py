import csv
import os

from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.portfolio.portfolio import Portfolio
from fianchetto_tradebot.common.utils import parsing

mara = Equity(ticker="MARA", company_name="Marathon Digital")
sfix = Equity(ticker="SFIX", company_name="StitchFix")
riot = Equity(ticker="RIOT", company_name="Riot Platforms")

#VIX Oct 16 '24 $18 Call
VIX_OCT_16_24_18_CALL = Option.from_str("VIX Oct 16 '24 $18 Call")

SAMPLE_PORTFOLIO_FILENAME = os.path.join(os.path.dirname(__file__), 'resources/sample_position_list.csv')


def test_parsing():
    with open(SAMPLE_PORTFOLIO_FILENAME) as file:
      df = csv.DictReader(file, delimiter=',')
      p: Portfolio = parsing.parse_into_portfolio(df)

      assert p.get_quantity(mara) == 3300
      assert p.get_quantity(sfix) == 8200
      assert p.get_quantity(riot) == 5800

      assert p.get_quantity(VIX_OCT_16_24_18_CALL) == 6