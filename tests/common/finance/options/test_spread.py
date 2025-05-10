from datetime import datetime

import pytest

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.finance.options.equity_order_line import EquityOrderLine
from fianchetto_tradebot.common_models.finance.options.mixed.buy_write import BuyWrite
from fianchetto_tradebot.common_models.finance.options.option_order_line import OptionOrderLine
from fianchetto_tradebot.common_models.finance.options.spread import Spread, DE_NORMALIZATION_CONSTANT
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType


class TestSpread:

    @pytest.fixture
    def sfix_covered_call(self):
        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = EquityOrderLine(equity, Action.BUY, 100)
        ol_2 = OptionOrderLine(tradable1, Action.SELL_OPEN, 1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=44))

        option_order_lines: list[OrderLine] = list[OrderLine]()

        option_order_lines.append(ol_2)

        return BuyWrite(order_price, ol_1, option_order_lines)

    @pytest.fixture
    def sfix_call_credit_spread(self) -> Spread:
        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=44))

        order_lines: list[OrderLine] = list[OrderLine]()
        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Spread(order_price, order_lines)

    @pytest.fixture
    def sfix_call_debit_diagonal_spread(self) -> Spread:
        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")
        option_expiry_1: datetime.date = datetime(2025, 1, 31).date()
        option_expiry_2: datetime.date = datetime(2025, 2, 6).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_1)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_2)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=0, part=5))

        order_lines: list[OrderLine] = list[OrderLine]()
        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Spread(order_price, order_lines)

    @pytest.fixture
    def sfix_put_credit_calendar_spread(self) -> Spread:
        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")
        option_expiry_1: datetime.date = datetime(2025, 1, 31).date()
        option_expiry_2: datetime.date = datetime(2025, 2, 6).date()
        tradable1: Option = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_1)
        tradable2: Option = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_2)

        ol_1 = OrderLine(tradable=tradable1, action=Action.BUY_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.SELL_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=5))

        order_lines: list[OrderLine] = list[OrderLine]()
        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Spread(order_price, order_lines)

    @pytest.fixture
    def sfix_call_debit_spread(self) -> Spread:
        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=tradable1, action=Action.BUY_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.SELL_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=0, part=44))

        order_lines: list[OrderLine] = list[OrderLine]()
        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Spread(order_price, order_lines)

    def test_vertical_call_credit_spread_collateral_requirement(self, sfix_call_credit_spread: Spread):
        expected_collateral_required = Amount(whole=100, part=0) - Amount(whole=0, part=44) * DE_NORMALIZATION_CONSTANT
        collateral_required: Amount = sfix_call_credit_spread.get_collateral_required()

        assert collateral_required == expected_collateral_required

    def test_diagonal_call_debit_spread_collateral_requirement(self, sfix_call_debit_diagonal_spread: Spread):
        expected_collateral_required = Amount(whole=100, part=0) + Amount(whole=0, part=5) * DE_NORMALIZATION_CONSTANT
        collateral_required: Amount = sfix_call_debit_diagonal_spread.get_collateral_required()

        assert collateral_required == expected_collateral_required

    def test_put_calendar_credit_spread_collateral_requirement(self, sfix_put_credit_calendar_spread: Spread):
        expected_collateral_required = Amount(whole=500, part=0) - Amount(whole=0, part=5) * DE_NORMALIZATION_CONSTANT
        collateral_required: Amount = sfix_put_credit_calendar_spread.get_collateral_required()

        assert collateral_required == expected_collateral_required

    def test_vertical_call_debit_spread_collateral_requirement(self, sfix_call_debit_spread: Spread):
        expected_collateral_required = Amount(whole=0, part=44) * DE_NORMALIZATION_CONSTANT
        collateral_required: Amount = sfix_call_debit_spread.get_collateral_required()

        assert collateral_required == expected_collateral_required

    def test_diagonal_put_spread_collateral_requirement(self):
        pass

    def test_call_spread_vertical_spread_collateral_requirement(self):
        pass

    def test_spread_to_order(self):
        pass

    def test_order_to_spread(self):
        pass