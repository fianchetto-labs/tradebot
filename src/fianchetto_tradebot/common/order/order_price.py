from pydantic import BaseModel

from fianchetto_tradebot.common.finance.amount import Amount, ZERO
from fianchetto_tradebot.common.order.order_price_type import OrderPriceType


class OrderPrice(BaseModel):
    order_price_type: OrderPriceType
    price: Amount = ZERO

    def to_amount(self)->Amount:
        if self.order_price_type == OrderPriceType.NET_EVEN:
            return ZERO
        if self.order_price_type == OrderPriceType.NET_CREDIT:
            return self.price
        if self.order_price_type == OrderPriceType.NET_DEBIT:
            return self.price * -1

    def __validate__(order_price_type, price):
        if order_price_type is OrderPriceType.NET_EVEN and price != Amount(0, 0):
            raise Exception("Cannot have a price when it is supposed to be EVEN")


    def __str__(self):
        return f"{self.order_price_type.name}: {self.price}"

    def __eq__(self, other):
        # TODO: Unit test this
        if self.order_price_type != other.order_price_type:
            if (self.order_price_type == OrderPriceType.NET_EVEN and other.price == ZERO) or (other.order_price_type == OrderPriceType.NET_EVEN and self.price == ZERO):
                print("Logical equality, though not object equality")
            else:
                return False
        if self.price != other.price:
            return False
        return True

    def __gt__(self, other):
        # TODO: Make sure this doesn't return true something when it's equal
        self_absolute_amount = self.price if self.order_price_type != OrderPriceType.NET_DEBIT else self.price * -1
        other_absolute_amount = other.price if other.order_price_type != OrderPriceType.NET_DEBIT else other.price * -1

        return self_absolute_amount > other_absolute_amount

    def __lt__(self, other):
        # TODO: Make sure this doesn't return true something when it's equal
        self_absolute_amount = self.price if self.order_price_type != OrderPriceType.NET_DEBIT else self.price * -1
        other_absolute_amount = other.price if other.order_price_type != OrderPriceType.NET_DEBIT else other.price * -1

        return self_absolute_amount < other_absolute_amount