from datetime import datetime

from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType

DEFAULT_AMOUNT = strike=Amount(whole=100, part=0)
DEFAULT_EQUITY = Equity(ticker="GE", company_name="General Electric")

class OrderTestUtil:

    @staticmethod
    def build_equity_order(equity:Equity=DEFAULT_EQUITY, action=Action.BUY, price: Amount = DEFAULT_AMOUNT):
        ol_1 = OrderLine(tradable=equity, action=action, quantity=1)
        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=price)
        order_lines: list[OrderLine] = [ol_1]

        order = Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)
        return order

    @staticmethod
    # TODO: I may need to make this an OrderPrice, b/c negative values for amount don't work.
    # TODO: Find out if these things put in the API as LIMIT, or a NET_CREDIT? How does E*Trade think of them?
    def build_spread_order(order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=1,part=99)))->Order:
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="GE")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=160, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)
        tradable2: Option = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=155, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)

    @staticmethod
    def build_covered_call():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_nane="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=equity, action=Action.BUY, quantity=100)
        ol_2 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=3, part=84))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)


    @staticmethod
    def build_short_covered_call():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_nane="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 6, 20).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=equity, action=Action.SELL, quantity=100)
        ol_2 = OrderLine(tradable=tradable1, action=Action.BUY_CLOSE, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=2, part=99))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)


    @staticmethod
    def build_calendar_spread():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_nane="STITCH FIX INC COM CL A")
        option_expiry_1: datetime.date = datetime(2025, 1, 31).date()
        option_expiry_2: datetime.date = datetime(2025, 6, 20).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_1)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_2)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, strike=Amount(whole=0, part=45))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)

    @staticmethod
    def build_three_option_put_one_spread_one_naked():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_nane="STITCH FIX INC COM CL A")
        option_expiry_1: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(5, 0, Currency.US_DOLLARS), expiry=option_expiry_1)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(3, 0, Currency.US_DOLLARS), expiry=option_expiry_1)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=2)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, strike=Amount(whole=0, part=45))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)

    @staticmethod
    def build_diagonal_spread():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_nane="STITCH FIX INC COM CL A")
        option_expiry_1: datetime.date = datetime(2025, 1, 31).date()
        option_expiry_2: datetime.date = datetime(2025, 6, 20).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_1)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry_2)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, strike=Amount(whole=0, part=45))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)

    @staticmethod
    def build_horizontal_spread():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_nane="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(0, 45))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)

    @staticmethod
    def build_iron_butterfly():
        order_lines: list[OrderLine] = list()

        equity = Equity(ticker="SFIX", company_name="STITCH FIX INC COM CL A")
        option_expiry: datetime.date = datetime(2025, 1, 31).date()
        tradable1: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)
        tradable2: Option = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=5, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        tradable3: Option = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=4, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)
        tradable4: Option = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=3, part=0, currency=Currency.US_DOLLARS), expiry=option_expiry)

        ol_1 = OrderLine(tradable=tradable1, action=Action.SELL_OPEN, quantity=1)
        ol_2 = OrderLine(tradable=tradable2, action=Action.BUY_OPEN, quantity=1)
        ol_3 = OrderLine(tradable=tradable3, action=Action.SELL_OPEN, quantity=1)
        ol_4 = OrderLine(tradable=tradable4, action=Action.BUY_OPEN, quantity=1)

        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=59))

        order_lines.append(ol_1)
        order_lines.append(ol_2)

        order_lines.append(ol_3)
        order_lines.append(ol_4)

        return Order(expiry=GoodForDay(), order_lines=order_lines, order_price=order_price)