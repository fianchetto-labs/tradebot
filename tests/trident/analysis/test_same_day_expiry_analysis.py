import pytest

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.tradable_type import TradableType
from fianchetto_tradebot.trident.analysis.same_expiry_combined_order_analyser import SameDayExpiryCombinedOrderAnalyser
from tests.common.api.orders.order_test_util import OrderTestUtil


class TestSameDayExpiryAnalysis:
    def test_option_spread(self):
        spread_order: Order = OrderTestUtil.build_spread_order(order_price = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=1, part=50)))
        tradable = spread_order.order_lines[0].tradable
        equity: Equity = tradable if isinstance(tradable, Equity) else tradable.equity

        at_price: float = Amount(whole=157, part=50).to_float()

        analyser = SameDayExpiryCombinedOrderAnalyser(equity, [spread_order])

        assert analyser.get_value_for_given_price_at_expiry(at_price) == Amount(whole=250, part=0, negative=True)
        assert analyser.get_pl_for_given_price_at_expiry(at_price) == Amount(whole=100, part=0, negative=True)

    @pytest.mark.parametrize("closing_option_desc,equity_price,expected_order_value,expected_pl", [(("otm"), Amount(whole=3, part=95), Amount(whole=395,part=0), Amount(whole=11,part=0)),
                                                                                     (("atm"), Amount(whole=4, part=0), Amount(whole=400,part=0), Amount(whole=16,part=0)),
                                                                                     (("atm"), Amount(whole=4, part=5), Amount(whole=400,part=0), Amount(whole=16, part=0))])
    def test_covered_call(self, closing_option_desc: str, equity_price: Amount, expected_order_value: Amount, expected_pl: Amount):
        covered_call_order: Order = OrderTestUtil.build_covered_call()
        equity: Equity = list(filter(lambda ol: ol.tradable.get_type() == TradableType.Equity, covered_call_order.order_lines))[0].tradable

        analyser = SameDayExpiryCombinedOrderAnalyser(equity, [covered_call_order])

        analysed_order_value = analyser.get_value_for_given_price_at_expiry(equity_price.to_float())
        assert analysed_order_value == expected_order_value
        assert analyser.get_pl_for_given_price_at_expiry(equity_price.to_float()) == expected_pl

    @pytest.mark.parametrize("closing_option_desc,equity_price,expected_order_value,expected_pl", [(("a"), Amount(whole=5, part=15), Amount(whole=100,part=0, negative=True), Amount(whole=41,part=0, negative=True)),
                                                                                     ("b", Amount(whole=4, part=75), Amount(whole=75, part=0, negative=True), Amount(whole=16, part=0, negative=True)),
                                                                                     ("c", Amount(whole=4, part=0), Amount(whole=0, part=0), Amount(whole=59, part=0)),
                                                                                     ("d", Amount(whole=3, part=15), Amount(whole=85, part=0, negative=True), Amount(whole=26, part=0, negative=True)),
                                                                                     ("e", Amount(whole=2, part=95), Amount(whole=100, part=0, negative=True), Amount(whole=41, part=0, negative=True))])

    def test_iron_butterfly(self, closing_option_desc: str, equity_price: Amount, expected_order_value: Amount, expected_pl: Amount):
        iron_butterfly_order: Order = OrderTestUtil.build_iron_butterfly()
        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")

        analyser = SameDayExpiryCombinedOrderAnalyser(equity, [iron_butterfly_order])

        analysed_order_value = analyser.get_value_for_given_price_at_expiry(equity_price.to_float())
        assert analysed_order_value == expected_order_value
        assert analyser.get_pl_for_given_price_at_expiry(equity_price.to_float()) == expected_pl