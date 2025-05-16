from fianchetto_tradebot.common_models.account.computed_balance import ZERO_AMOUNT
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic
from fianchetto_tradebot.server.orders.trade_execution_util import TradeExecutionUtil
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

GAP_REDUCTION_RATIO = 1/3
DEFAULT_WAIT_SEC = 3
VERY_CLOSE_TO_MARKET_PRICE_WAIT = 30

class IncrementalPriceDeltaExecutionTactic(ExecutionTactic):
    @staticmethod
    def new_price(order: Order, quotes_service: QuotesService=None)->(OrderPrice, int):

        # This'll always be positive. We'd need to normalize it WRT to the price type..where do we get the rest of the info?
        current_order_price: float = order.order_price.price.to_float()
        current_market_mark_to_market_price: float = TradeExecutionUtil.get_cost_or_proceeds_to_establish_position(order, quotes_service).mark

        # TODO: Make this calculation more precise with OrderPrice arithmetic, FIA-104
        # Changed to positive...
        delta = current_order_price + current_market_mark_to_market_price

        if order.get_order_type() == OrderType.EQ:
            return IncrementalPriceDeltaExecutionTactic.get_equity_new_price(delta, current_order_price, order)
        else:
            return IncrementalPriceDeltaExecutionTactic.get_spread_new_price(delta, current_order_price, order)

    @staticmethod
    # TODO: This should be tested w/bids and asks that are negative to positive
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
    def get_equity_new_price(delta, current_order_price, order: Order):
        adjustment: float = 0
        if order.order_price.order_price_type == OrderPriceType.LIMIT:
            # first line considered b/c equity orders only have one line. Can't long & short in the same txn
            for order_line in order.order_lines:
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