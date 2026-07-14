from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.serialization import serialize_amount_key
from tests.common.util.chain_testing_util import instantiate_simple_chain_builder


def test_amount_display_is_human_readable_and_pads_cents():
    assert str(Amount.from_float(5.99)) == "5.99 USD"
    assert str(Amount.from_float(1.09)) == "1.09 USD"
    assert str(Amount.from_float(0)) == "0.00 USD"
    assert str(Amount(whole=3, part=45, currency=Currency.EURO, negative=True)) == "-3.45 EUR"


def test_amount_display_and_serialized_key_are_separate_contracts():
    amount = Amount(whole=25, part=0, currency=Currency.US_DOLLARS)

    assert str(amount) == "25.00 USD"
    assert serialize_amount_key(amount) == "25.00 USD"


def test_price_display_is_a_compact_quote_row():
    price = Price(bid=1.0, ask=2.0)

    assert str(price) == "1.50\t|\t1.00\t|\t2.00\t"
    assert repr(price) == str(price)


def test_order_price_display_names_the_price_type_and_amount():
    assert str(OrderPrice(order_price_type=OrderPriceType.NET_EVEN)) == "NET_EVEN: 0.00 USD"
    assert (
        str(OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=1, part=25)))
        == "NET_DEBIT: 1.25 USD"
    )
    assert (
        str(OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=75)))
        == "NET_CREDIT: 0.75 USD"
    )


def test_order_line_display_summarizes_action_quantity_and_tradable():
    order_line = OrderLine(
        tradable=Equity(ticker="GE", company_name="General Electric"),
        action=Action.BUY,
        quantity=3,
    )

    assert str(order_line) == "BUY: 3 x GE: General Electric"


def test_chain_display_contains_readable_table_fragments():
    chain_builder = instantiate_simple_chain_builder()

    output = str(chain_builder)

    assert "2025-09-19:" in output
    assert "Mark\t|\tBid \t|\tAsk \t|\tStrike\t|\tMark\t|\tBid \t|\tAsk" in output
    assert "$25.00 USD" in output
    assert "1.50\t|\t1.00\t|\t2.00" in output
