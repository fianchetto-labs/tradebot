from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.order import Order
from fianchetto_tradebot.quotes.api.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.quotes.api.get_tradable_response import GetTradableResponse
from fianchetto_tradebot.quotes.quote_service import QuoteService

ADJUSTED_NO_BIDS_WIDE_SPREAD_ASK = .03

class TradeExecutionUtil:
    # This can also be done via order Bid-Ask - advantage is fewer API calls. Downside is relying on ETrade's order service
    # This would be necessary to establish a first price for the order. Other issue is it wouldn't adjust for very wide spreads
    def get_market_price(order: Order, quote_service: QuoteService, adjust_excessive_spreads=True) -> Price:
        mark_to_market_price: float = 0
        best_price: float = 0
        worst_price: float = 0

        for order_line in order.order_lines:
            get_tradable_request: GetTradableRequest = GetTradableRequest(tradable=order_line.tradable)
            get_tradable_response: GetTradableResponse = quote_service.get_tradable_quote(get_tradable_request)
            quantity = order_line.quantity

            current_price = get_tradable_response.current_price

            if adjust_excessive_spreads and get_tradable_response.current_price.bid == 0 and get_tradable_response.current_price.ask > .04:
                current_price.ask = ADJUSTED_NO_BIDS_WIDE_SPREAD_ASK

            if Action.is_long(Action[order_line.action]):
                best_price -= current_price.bid * quantity
                worst_price -= current_price.ask * quantity

                mark_to_market_price -= get_tradable_response.current_price.mark
            else:
                # Logic - you're selling. If you're selling closer to the bid, that's bad. If you're selling closer to the ask, that's good.
                best_price += current_price.ask * quantity
                worst_price += current_price.bid * quantity

                mark_to_market_price += get_tradable_response.current_price.mark

        # This is not obvious and quite surprising. In cases where there's a credit, bid is the lower credit, ask is the higher credit.

        # This is for adjusting how the offer is displayed / presented
        # Where there is at least one debit, the higher price is the bid and the lower is the ask
        if worst_price >= 0:
            # Take on a credit to put on the trade
            lower = worst_price
            upper = best_price
        else:
            lower = best_price
            upper = worst_price

        return Price(bid=lower, ask=upper)