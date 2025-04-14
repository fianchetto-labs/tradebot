from fianchetto_tradebot.common.account.computed_balance import ZERO_AMOUNT
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order_price import OrderPrice
from fianchetto_tradebot.common.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common.order.order_type import OrderType
from fianchetto_tradebot.common.order.placed_order import PlacedOrder
from fianchetto_tradebot.quotes.quote_service import QuoteService
from fianchetto_tradebot.oex.tactics.execution_tactic import ExecutionTactic
from fianchetto_tradebot.oex.trade_execution_util import TradeExecutionUtil

GAP_REDUCTION_RATIO = 1/3
DEFAULT_WAIT_SEC = 12
VERY_CLOSE_TO_MARKET_PRICE_WAIT = 30

class IncrementalPriceDeltaExecutionTactic(ExecutionTactic):
    @staticmethod
    def new_price(placed_order: PlacedOrder, quote_service: QuoteService=None)->(OrderPrice, int):
        current_market_price: Price = placed_order.placed_order_details.current_market_price
        current_market_mark_to_market_price: float = current_market_price.mark

        # This'll always be positive. We'd need to normalize it WRT to the price type..where do we get the rest of the info?
        current_order_price: float = placed_order.order.order_price.price.to_float()
        if placed_order.order.order_price.order_price_type == OrderPriceType.NET_DEBIT:
            current_order_price *= -1

        if not current_market_mark_to_market_price and quote_service:
            # After-hours it doesn't seem to provide this data in the E*Trade response. No matter, we can pull it from the exchange
            current_market_mark_to_market_price: float = TradeExecutionUtil.get_market_price(placed_order.order, quote_service).mark

        delta = current_order_price - current_market_mark_to_market_price

        if placed_order.order.get_order_type() == OrderType.EQ:
            return IncrementalPriceDeltaExecutionTactic.get_equity_new_price(delta, current_order_price, placed_order)
        else:
            return IncrementalPriceDeltaExecutionTactic.get_spread_new_price(delta, current_order_price)

    @staticmethod
    def get_spread_new_price(delta, current_order_price):
        if delta > 0:
            new_delta = delta * (1 - GAP_REDUCTION_RATIO)
            adjustment = round(min(new_delta - delta, -.01), 2)
        else:
            # If below the mark, adjust incrementally
            adjustment = -.01

        proposed_new_amount_float: float = round(current_order_price + adjustment, 2)
        proposed_new_amount = Amount.from_float(proposed_new_amount_float)
        if proposed_new_amount == ZERO_AMOUNT:
            return OrderPrice(OrderPriceType.NET_EVEN, Amount(0,0)), DEFAULT_WAIT_SEC
        elif proposed_new_amount < ZERO_AMOUNT:
            return OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=abs(proposed_new_amount)), DEFAULT_WAIT_SEC
        else:
            return OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=proposed_new_amount), DEFAULT_WAIT_SEC

    @staticmethod
    def get_equity_new_price(delta, current_order_price, placed_order: PlacedOrder):
        adjustment: float = 0
        if placed_order.order.order_price.order_price_type == OrderPriceType.LIMIT:
            # Why is only first order_line considered? TODO: Add more test cases!
            for order_line in placed_order.order.order_lines:
                action: Action = Action[order_line.action]
                if Action.is_short(action):
                    # decrease the value
                    new_delta = delta * (1 - GAP_REDUCTION_RATIO)
                    adjustment += round(min(new_delta - delta, -.01), 2)
                else:
                    # increase the value
                    new_delta = delta * (1 - GAP_REDUCTION_RATIO)
                    adjustment += round(max(new_delta - delta, .01), 2)
        else:
            raise Exception("For ")

        proposed_new_amount_float: float = round(current_order_price + adjustment, 2)
        proposed_new_amount = Amount.from_float(proposed_new_amount_float)

        return OrderPrice(order_price_type=OrderPriceType.LIMIT, price=proposed_new_amount), DEFAULT_WAIT_SEC