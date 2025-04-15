from datetime import datetime

from fianchetto_tradebot.common.exchange.market_session import MarketSession
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.equity import Equity
from fianchetto_tradebot.common.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common.finance.option import Option
from fianchetto_tradebot.common.finance.option_type import OptionType
from fianchetto_tradebot.common.finance.price import Price
from fianchetto_tradebot.common.finance.tradable import Tradable
from fianchetto_tradebot.common.order.action import Action
from fianchetto_tradebot.common.order.executed_order import ExecutedOrder
from fianchetto_tradebot.common.order.executed_order_details import ExecutionOrderDetails
from fianchetto_tradebot.common.order.expiry.fill_or_kill import FillOrKill
from fianchetto_tradebot.common.order.expiry.good_for_day import GoodForDay
from fianchetto_tradebot.common.order.expiry.good_for_sixty_days import GoodForSixtyDays
from fianchetto_tradebot.common.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common.order.expiry.good_until_date import GoodUntilDate
from fianchetto_tradebot.common.order.expiry.order_expiry import OrderExpiry
from fianchetto_tradebot.common.order.order import Order
from fianchetto_tradebot.common.order.order_line import OrderLine, QUANTITY_FILLED_NOT_SPECIFIED
from fianchetto_tradebot.common.order.order_price import OrderPrice
from fianchetto_tradebot.common.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.order.placed_order import PlacedOrder
from fianchetto_tradebot.common.order.placed_order_details import PlacedOrderDetails
from fianchetto_tradebot.common.order.tradable_type import TradableType


class OrderConversionUtil:

    @staticmethod
    def to_executed_order_from_json(input_order: dict, account_id):
        placed_order: PlacedOrder = OrderConversionUtil.to_placed_order_from_json(input_order, query_account_id=account_id)

        order_detail = input_order["OrderDetail"][0]
        execution_order_details: ExecutionOrderDetails = ExecutionOrderDetails(
        Amount.from_float(order_detail["orderValue"]), datetime.fromtimestamp(order_detail["executedTime"] / 1000))

        return ExecutedOrder(placed_order, execution_order_details)

    @staticmethod
    def to_placed_order_from_json(input_order: dict, query_account_id = None, query_order_id: str = None)->PlacedOrder:
        order_id = input_order["orderId"] if "orderId" in input_order else query_order_id
        order_detail = input_order["OrderDetail"][0]
        account_id = order_detail["accountId"] if "accountId" in order_detail else query_account_id
        order: Order = OrderConversionUtil.to_order_from_json(order_detail)

        status: OrderStatus = OrderStatus[str(order_detail['status']).upper()]
        order_placed_time: datetime = datetime.fromtimestamp(order_detail["placedTime"] / 1000)
        replaces_order_id = str(order_detail['replacesOrderId']) if 'replacesOrderId' in order_detail else None
        market_session = MarketSession[order_detail["marketSession"]]
        ratio = order_detail['ratio'] if 'ratio' in order_detail else None

        # TODO: These seem to be zero .. not sure if that's an after-hours issue, or something more fundamental
        # TODO: This is very odd, but these actually come back in the API was negative values when they should be positive.
        # The order is for a credit, and E*Trade reports the range in this example as positive for both bid and ask
        mark_price:float = order_detail['netPrice'] * -1
        bid_price = order_detail['netBid'] * -1
        ask_price = order_detail['netAsk'] * -1

        current_market_price: Price = Price(bid=bid_price, ask=ask_price, mark=mark_price)

        placed_order_details = PlacedOrderDetails(account_id=account_id, exchange_order_id=str(order_id), status=status, order_placed_time=order_placed_time, current_market_price=current_market_price, market_session=market_session, replaces_order_id=replaces_order_id)

        return PlacedOrder(order=order, placed_order_details=placed_order_details)

    @staticmethod
    def to_order_from_json(input_order: dict)->Order:
        expiry: OrderExpiry = OrderConversionUtil.get_expiry_from_order(input_order)

        order_price_type = OrderPriceType[input_order["priceType"]]
        limit_price: OrderPrice = OrderPrice(order_price_type=order_price_type, price=Amount.from_float(input_order["limitPrice"]))

        order_lines: list[OrderLine] = OrderConversionUtil.process_instrument_to_orderlines(input_order)

        input_order: Order = Order(expiry=expiry, order_lines=order_lines, order_price=limit_price)
        return input_order

    @staticmethod
    def process_instrument_to_orderlines(order: dict)->list[OrderLine]:
        order_lines: list[OrderLine] = list[OrderLine]()
        for instrument in order["Instrument"]:
            quantity = instrument['orderedQuantity'] if 'orderedQuantity' in instrument else instrument['quantity']
            filled_quantity: int = instrument["filledQuantity"] if "filledQuantity" in instrument else QUANTITY_FILLED_NOT_SPECIFIED
            order_action = Action[instrument['orderAction']]
            product = instrument["Product"]
            symbol = product['symbol']
            equity = Equity(ticker=symbol, company_name=None)
            security_type = product["securityType"]

            if security_type == TradableType.Equity.value:
                order_lines.append(OrderLine(tradable=equity, action=order_action, quantity=quantity, quantity_filled=filled_quantity))
            elif security_type == TradableType.Option.value:
                call_put: OptionType = OptionType.from_str(product['callPut'])
                expiry_year = product['expiryYear']
                expiry_month = product['expiryMonth']
                expiry_day = product['expiryDay']
                strike_price = Amount.from_float(product['strikePrice'])

                option_expiry = datetime(expiry_year, expiry_month, expiry_day).date()

                o: Option = Option(equity=equity, type=call_put, strike=strike_price, expiry=option_expiry, style=ExerciseStyle.from_ticker(symbol))
                order_lines.append(OrderLine(tradable=o, action=order_action, quantity=quantity, quantity_filled=filled_quantity))
            else:
                raise Exception(f"Could not parse info for security type {security_type}")

        return order_lines

    @staticmethod
    def to_xml_from_order(order: Order)->str:
        pass

    @staticmethod
    def get_expiry_from_order(json: dict) -> OrderExpiry:
        all_or_none: bool = json["allOrNone"]
        order_term = json["orderTerm"]
        if order_term == "GOOD_FOR_DAY":
            return GoodForDay()
        if order_term == "GOOD_TILL_CANCELLED" or order_term == "GOOD_UNTIL_CANCEL":
            return GoodUntilCancelled(all_or_none)
        if order_term == "GOOD_TILL_DATE":
            # TODO: It's not clear where we get the value for GoodUntilDate
            return GoodUntilDate(datetime.date.today(), all_or_none)

    @staticmethod
    def build_order(order: Order) -> str:

        order_term = "GOOD_FOR_DAY"
        if type(order.expiry) == GoodForDay:
            order_term = "GOOD_FOR_DAY"
        elif type(order.expiry) == GoodForSixtyDays:
            order_term = "GOOD_TILL_DATE"
        elif type(order.expiry) == GoodUntilCancelled:
            order_term = "GOOD_UNTIL_CANCEL"
        elif type(order.expiry) == FillOrKill:
            order_term = "FILL_OR_KILL"

        instruments = list[str]()
        for order_line in order.order_lines:
            instruments.append(OrderConversionUtil.build_instrument(order_line))

        instrument_xml = "\n".join(instruments)

        return f"""<Order>
                               <allOrNone>{order.expiry.all_or_none}</allOrNone>
                               <priceType>{order.order_price.order_price_type.name}</priceType>
                               <orderTerm>{order_term}</orderTerm>
                               <marketSession>REGULAR</marketSession>
                               <stopPrice />
                               <limitPrice>{order.order_price.price}</limitPrice>
                               {instrument_xml}
                       </Order>
            """

    @staticmethod
    def build_instrument(order_line: OrderLine) -> str:
        product_xml = OrderConversionUtil.build_product_xml(order_line.tradable)
        quantity = order_line.quantity
        action = order_line.action

        # TODO: See if `orderedQuantity` is necessary
        return f"""
               <Instrument>
                 <orderAction>{action}</orderAction>
                 <orderedQuantity>{quantity}</orderedQuantity>
                 <quantity>{quantity}</quantity>
                 {product_xml}
               </Instrument>
            """

    @staticmethod
    def build_product_xml(tradable: Tradable) -> str:
        security_type = TradableType[type(tradable).__name__].value
        if type(tradable) is Equity:
            e: Equity = tradable
            symbol = e.ticker

            return f"""<Product>
                             <securityType>{security_type}</securityType>
                             <symbol>{symbol}</symbol>
                           </Product>
                """

        elif type(tradable) is Option:
            o: Option = tradable

            symbol = o.equity.ticker
            strike_price: Amount = o.strike
            call_put = str(o.type.name).upper()

            expiry: datetime = o.expiry
            expiry_day: int = expiry.day
            expiry_month: int = expiry.month
            expiry_year: int = expiry.year

            return f"""<Product>
                             <securityType>{security_type}</securityType>
                             <symbol>{symbol}</symbol>
                             <strikePrice>{strike_price.to_float()}</strikePrice>
                             <expiryDay>{expiry_day}</expiryDay>
                             <expiryMonth>{expiry_month}</expiryMonth>
                             <expiryYear>{expiry_year}</expiryYear>
                             <callPut>{call_put}</callPut>
                           </Product>
                """
        else:
            raise Exception(f"Tradable type not recognized, {type(tradable)}")
