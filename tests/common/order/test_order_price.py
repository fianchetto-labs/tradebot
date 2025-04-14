from fianchetto_tradebot.common.finance.amount import ZERO, Amount
from fianchetto_tradebot.common.order.order_price import OrderPrice
from fianchetto_tradebot.common.order.order_price_type import OrderPriceType


class TestOrderPrice:
    def test_limit_0_equals_even(self):
        assert OrderPrice(order_price_type=OrderPriceType.NET_EVEN) == OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=ZERO)
        assert OrderPrice(order_price_type=OrderPriceType.NET_EVEN) == OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=ZERO)

    def test_equality(self):
        assert OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=1, part=23)) == OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=1,part=23))
        assert OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=1, part=23)) == OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=1, part=23))

        assert OrderPrice(order_price_type=OrderPriceType.NET_EVEN) == OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=ZERO)
        assert OrderPrice(order_price_type=OrderPriceType.NET_EVEN) == OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=ZERO)

    def test_non_equality_diff_order_price_type(self):
            assert OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=1, part=23)) != OrderPrice(order_price_type=OrderPriceType.NET_DEBIT,
                                                                                      price=Amount(whole=1, part=23))
    def test_gt(self):
        assert OrderPrice(order_price_type=OrderPriceType.NET_EVEN) > OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=0, part=1))
        assert OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=1)) > OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=0, part=1))
        assert OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=2)) > OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=1))


    def test_lt(self):
        assert OrderPrice(order_price_type=OrderPriceType.NET_EVEN) < OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=1))

    def test_lt_two_debits(self):
        assert OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=0, part=2)) < OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=0, part=1))

    def test_lt_two_credits(self):
        assert OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=2)) < OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=3))
