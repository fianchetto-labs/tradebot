from datetime import datetime
from unittest.mock import MagicMock

import pytest

from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.server.common.brokerage.connector import Connector
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.server.orders.trade_execution_util import TradeExecutionUtil
from fianchetto_tradebot.common_models.api.quotes.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

equity = Equity(ticker="GE", company_name="General Electric")

short_put = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=195, part=0), expiry=datetime(2025, 5, 16).date())
long_put = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=185, part=0), expiry=datetime(2025, 5, 16).date())

cs_short_put = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=202, part=50), expiry=datetime(2025, 2, 14).date())
cs_long_put = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=197, part=50), expiry=datetime(2025, 2, 21).date())
cs_long_put_2 = Option(equity=equity, type=OptionType.PUT, strike=Amount(whole=195, part=0), expiry=datetime(2025, 5, 14).date())

short_call = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=200, part=0), expiry=datetime(2025, 5, 16).date())
long_call = Option(equity=equity, type=OptionType.CALL, strike=Amount(whole=210, part=0), expiry=datetime(2025, 5, 16).date())

sell_put_order_line = OrderLine(tradable=short_put, action=Action.SELL_OPEN, quantity=1)
buy_put_order_line = OrderLine(tradable=long_put, action=Action.BUY_OPEN, quantity=1)

sell_call_order_line = OrderLine(tradable=short_call, action=Action.SELL_OPEN, quantity=1)
buy_call_order_line = OrderLine(tradable=long_call, action=Action.BUY_OPEN, quantity=1)

put_credit_spread_orderlines = [sell_put_order_line, buy_put_order_line]
call_credit_spread_orderlines = [sell_call_order_line, buy_call_order_line]


@pytest.fixture
def quote_service():
    # return a mock quote service
    c: Connector = Connector()
    qs: QuotesService = QuotesService(c)

    qs.get_tradable_quote = MagicMock(side_effect=return_market_prices)
    return qs

def test_put_credit_spread(quote_service):
    order: Order = Order(expiry=GoodForDay(), order_lines=put_credit_spread_orderlines, order_price=OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=3, part=18)))

    market_price: Price = TradeExecutionUtil.get_market_price(order, quote_service)

    assert market_price.bid == 2.30
    assert market_price.ask == 4.05
    assert market_price.mark == 3.17

def test_call_credit_spread(quote_service):
    order: Order = Order(expiry=GoodForDay(), order_lines=call_credit_spread_orderlines, order_price=OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=5, part=28)))

    market_price: Price = TradeExecutionUtil.get_market_price(order, quote_service)

    assert market_price.bid == 4.65
    assert market_price.ask == 5.90
    assert market_price.mark == 5.28

def test_put_debit_spread(quote_service):
    cs_short_put_order_line = OrderLine(tradable=cs_short_put, action=Action.SELL_OPEN, quantity=1)
    cs_long_put_order_line = OrderLine(tradable=cs_long_put, action=Action.BUY_OPEN, quantity=1)
    cs_long_put_2_order_line = OrderLine(tradable=cs_long_put_2, action=Action.BUY_OPEN, quantity=1)

    call_debit_spread_order_lines = [cs_short_put_order_line, cs_long_put_order_line, cs_long_put_2_order_line]
    order: Order = Order(expiry=GoodForDay(), order_lines=call_debit_spread_order_lines,
                         order_price=OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=Amount(whole=0, part=7)))

    market_price: Price = TradeExecutionUtil.get_market_price(order, quote_service)

    assert market_price.bid == .42
    assert market_price.ask == -.29
    assert market_price.mark == .07


# If python had a proper mocking framework, this contrivance wouldn't be necessary
def return_market_prices(get_tradable_request: GetTradableRequest)->GetTradableResponse:
    if get_tradable_request == GetTradableRequest(tradable=short_put):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=7, part=15).to_float(), ask=Amount(whole=8, part=30).to_float()), volume=5)
    elif get_tradable_request == GetTradableRequest(tradable=long_put):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=4, part=25).to_float(), ask=Amount(whole=4, part=85).to_float()), volume=5)
    elif get_tradable_request == GetTradableRequest(tradable=short_call):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=15, part=20).to_float(), ask=Amount(whole=15, part=75).to_float()), volume=5)
    elif get_tradable_request == GetTradableRequest(tradable=long_call):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=9, part=85).to_float(), ask=Amount(whole=10, part=55).to_float()), volume=5)
    elif get_tradable_request == GetTradableRequest(tradable=cs_short_put):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=3, part=20).to_float(), ask=Amount(whole=3, part=50).to_float()), volume=5)
    elif get_tradable_request == GetTradableRequest(tradable=cs_long_put):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=1, part=99).to_float(), ask=Amount(whole=2, part=30).to_float()), volume=5)
    elif get_tradable_request == GetTradableRequest(tradable=cs_long_put_2):
        return GetTradableResponse(tradable=get_tradable_request.tradable, response_time=None, current_price=Price(bid=Amount(whole=1, part=9).to_float(), ask=Amount(whole=1, part=19).to_float()), volume=5)
    else:
        raise Exception("Option not recognized")