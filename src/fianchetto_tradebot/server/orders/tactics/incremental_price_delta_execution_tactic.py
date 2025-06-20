from os.path import curdir

from fianchetto_tradebot.common_models.account.computed_balance import ZERO_AMOUNT
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic, register_tactic
from fianchetto_tradebot.server.orders.trade_execution_util import TradeExecutionUtil
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

GAP_REDUCTION_RATIO = 1/3
DEFAULT_WAIT_SEC = 5
VERY_CLOSE_TO_MARKET_PRICE_WAIT = 30

@register_tactic
class IncrementalPriceDeltaExecutionTactic(ExecutionTactic):
    @staticmethod
    def new_price(order: Order, quotes_service: QuotesService=None)->(OrderPrice, int):

        current_order_price: float = order.order_price.price.to_float()
        if order.get_order_type() == OrderType.EQ:
            # If it's a limit order for an equity, we need to be explicit here:
            action = order.order_lines[0].action
            if action in [Action.BUY, Action.BUY_OPEN, Action.BUY_CLOSE]:
                current_order_price = -1 * current_order_price

            elif action in [Action.SELL, Action.SELL_OPEN, Action.SELL_CLOSE]:
                # No action, but keeping possibility open
                pass
            else:
                raise Exception(f"Unrecognized action type {action} for equity trade")

        current_market_mark_to_market_price: float = TradeExecutionUtil.get_cost_or_proceeds_to_establish_position(order, quotes_service).mark

        # Delta always positive. We will decrement in either case.
        if current_order_price > current_market_mark_to_market_price:
            # 5 - 2 = 3
            delta = current_order_price - current_market_mark_to_market_price
        else:
            # -2 - (-5) = 3
            delta = current_market_mark_to_market_price - current_order_price

        if order.get_order_type() == OrderType.EQ:
            return IncrementalPriceDeltaExecutionTactic.get_equity_new_price(delta, order)
        else:
            return IncrementalPriceDeltaExecutionTactic.get_spread_new_price(delta, order)

    @staticmethod
    # TODO: This should be tested w/bids and asks that are negative to positive
    def get_spread_new_price(delta, current_order: Order):

        current_order_price: float = current_order.order_price.price.to_float()
        adjustment = max(round(delta * GAP_REDUCTION_RATIO, 2), .01)

        # Adjustments go in one direction -- less credit or more debit.
        proposed_new_amount_float: float = round(current_order_price - adjustment, 2)
        proposed_new_amount: Amount = Amount.from_float(proposed_new_amount_float)
        if proposed_new_amount == ZERO_AMOUNT:
            return OrderPrice(order_price_type=OrderPriceType.NET_EVEN, price=Amount(whole=0, part=0)), DEFAULT_WAIT_SEC
        elif proposed_new_amount < ZERO_AMOUNT:
            return OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=abs(proposed_new_amount)), DEFAULT_WAIT_SEC
        else:
            return OrderPrice(order_price_type=OrderPriceType.NET_CREDIT, price=proposed_new_amount), DEFAULT_WAIT_SEC

    @staticmethod
    def get_equity_new_price(delta, order: Order):
        # Here it's negative if long, positive if short. Essentially what it does to your cash balance
        current_order_price = order.order_price.price.to_float()
        new_amount = current_order_price
        if order.order_price.order_price_type == OrderPriceType.LIMIT:
            # first line considered b/c equity orders only have one line. Can't long & short in the same txn
            order_line = order.order_lines[0]
            action: Action = order_line.action
            new_delta = abs(delta * (1 - GAP_REDUCTION_RATIO))
            adjustment = round(max(delta - new_delta, .01), 2)
            if Action.is_short(action):
                # offering to sell for less
                new_amount -= adjustment
            else:
                # offering to pay more
                new_amount += adjustment
        else:
            raise Exception(f"For equity trade, unrecognized order price type {order.order_price.order_price_type}. Expected OrderPriceTYpe.LIMIT.")

        return OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount.from_float(new_amount)), DEFAULT_WAIT_SEC