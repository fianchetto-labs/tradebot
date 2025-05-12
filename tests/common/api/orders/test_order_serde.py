import json

from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType


class TestOrderSerde():
    def test_order_preview_json_reserialization(self):
        account_id = "acc123"
        client_order_id = "rand123"
        ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=100, part=1))
        o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)

        order_metadata: OrderMetadata = OrderMetadata(order_type=o.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PreviewOrderRequest(order_metadata=order_metadata, order=o)

        as_json = request.model_dump_json()
        as_request = request.model_validate_json(as_json)

        assert request.order.order_price.price == as_request.order.order_price.price

    def test_order_preview_dict_reserialization(self):
        account_id = "acc123"
        client_order_id = "rand123"
        ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=100, part=1))
        o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)

        order_metadata: OrderMetadata = OrderMetadata(order_type=o.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PreviewOrderRequest(order_metadata=order_metadata, order=o)

        as_dict = request.model_dump()
        as_request = request.model_validate(as_dict)

        assert request.order.order_price.price == as_request.order.order_price.price

    def test_order_preview_dict_dumps(self):
        account_id = "acc123"
        client_order_id = "rand123"
        ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.NET_DEBIT, price=Amount(whole=100, part=1))
        o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)

        order_metadata: OrderMetadata = OrderMetadata(order_type=o.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PreviewOrderRequest(order_metadata=order_metadata, order=o)

        as_dict = request.model_dump()
        json.dumps(as_dict)