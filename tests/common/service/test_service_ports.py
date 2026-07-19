from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.orders.order_service import OrderService
from fianchetto_tradebot.server.common.service.ports import OrderServicePort, QuoteServicePort
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService


class FakeOrderService:
    def get_order(self, get_order_request):
        pass

    def cancel_order(self, cancel_order_request):
        pass

    def preview_and_place_order(self, preview_order_request):
        pass

    def modify_order(self, preview_modify_order_request):
        pass


class FakeQuoteService:
    def get_tradable_quote(self, request):
        pass


def test_order_port_is_runtime_structural_contract():
    assert isinstance(FakeOrderService(), OrderServicePort)
    assert isinstance(object.__new__(OrderService), OrderServicePort)
    assert isinstance(object.__new__(ETradeOrderService), OrderServicePort)


def test_quote_port_is_runtime_structural_contract():
    assert isinstance(FakeQuoteService(), QuoteServicePort)
    assert isinstance(object.__new__(QuotesService), QuoteServicePort)
    assert isinstance(object.__new__(ETradeQuotesService), QuoteServicePort)
