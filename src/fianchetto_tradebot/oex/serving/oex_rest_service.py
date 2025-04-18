from datetime import datetime

from flask import Flask, jsonify, make_response
from flask import request

from fianchetto_tradebot.common.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.common.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common.api.orders.order_list_request import ListOrdersRequest
from fianchetto_tradebot.common.api.orders.order_list_response import ListOrdersResponse
from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common.api.orders.preview_order_response import PreviewOrderResponse
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.exchange.exchange_name import ExchangeName
from fianchetto_tradebot.common.order.order import Order
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.service.rest_service import RestService, ETRADE_ONLY_EXCHANGE_CONFIG
from fianchetto_tradebot.common.service.service_key import ServiceKey
from fianchetto_tradebot.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.quotes.quotes_service import QuotesService

JAN_1_2024 = datetime(2024,1,1).date()
DEFAULT_START_DATE = JAN_1_2024
DEFAULT_COUNT = 100


class OexRestService(RestService):
    def __init__(self, credential_config_files: dict[ExchangeName, str]=ETRADE_ONLY_EXCHANGE_CONFIG):
        super().__init__(ServiceKey.OEX, credential_config_files)

    @property
    def app(self) -> Flask:
        return self._app

    @app.setter
    def app(self, app: Flask):
        self._app = app

    def _register_endpoints(self):
        super()._register_endpoints()
        self.app.add_url_rule(rule='/api/v1/<exchange>/<account_id>/orders', endpoint='list-orders', view_func=self.list_orders, methods=['GET'])
        self.app.add_url_rule(rule='/api/v1/<exchange>/<account_id>/orders/<order_id>', endpoint='get-order',
                              view_func=self.get_order, methods=['GET'])

        self.app.add_url_rule(rule='/api/v1/<exchange>/<account_id>/orders/preview', endpoint='preview-order',
                              view_func=self.preview_order, methods=['POST'])

        self.app.add_url_rule(rule='/api/v1/<exchange>/<account_id>/orders/preview/<preview_id>', endpoint='place-order',
                              view_func=self.place_order, methods=['POST'])

        self.app.add_url_rule(rule='/api/v1/<exchange>/<account_id>/orders/preview_and_place', endpoint='preview-and-place-order',
                              view_func=self.preview_and_place_order, methods=['POST'])

    def _setup_exchange_services(self):
        self.order_services: dict[ExchangeName, OrderService] = dict()
        self.quotes_services: dict[ExchangeName, QuotesService] = dict()

        # E*Trade
        etrade_key: ExchangeName = ExchangeName.ETRADE
        etrade_connector: ETradeConnector = self.connectors[ExchangeName.ETRADE]
        etrade_order_service = ETradeOrderService(etrade_connector)
        etrade_quotes_service = ETradeQuotesService(etrade_connector)

        self.order_services[etrade_key] = etrade_order_service
        self.quotes_services[etrade_key] = etrade_quotes_service

        # TODO: Add for IKBR and Schwab

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

    def list_orders(self, exchange: str, account_id: str):
        args = request.args
        status_str = args.get('status')
        status = OrderStatus.ANY if not status_str else OrderStatus[status_str]
        from_date = DEFAULT_START_DATE if not 'from_date' in args else datetime.datetime.strptime(args.get('from_date'), '%yyyy-mm-dd').date()
        to_date = datetime.today().date() if not 'to_date' in args else datetime.datetime.strptime(args.get('to_date'), '%yyyy-mm-dd').date()

        count = args.get('count') if 'count' in args else DEFAULT_COUNT

        order_service: OrderService = self.order_services[ExchangeName[exchange.upper()]]
        list_order_request = ListOrdersRequest(account_id=account_id, status=status, from_date=from_date, to_date=to_date, count=count)

        resp: ListOrdersResponse = order_service.list_orders(list_order_request)

        return jsonify(resp)

    def get_order(self, exchange: str, account_id: str, order_id: str):
        if not order_id:
            # TODO: Factor this out
            # TODO: Put HTTP response codes in an eum
            resp = make_response(f"Order {order_id} not found", 400)
            resp.headers['X-Something'] = 'A value'
            return resp

        order_service: OrderService = self.order_services[ExchangeName[exchange.upper()]]
        get_order_request = GetOrderRequest(account_id=account_id, order_id=order_id)

        resp: GetOrderResponse = order_service.get_order(get_order_request)

        return jsonify(resp)

    def preview_order(self, exchange, account_id: str):
        content_type = request.headers.get('Content-Type')
        if (content_type != 'application/json'):
            return 'Content-Type not supported!'

        preview_order_request = PreviewOrderRequest.model_validate(request.json)
        if not preview_order_request.order_metadata.account_id:
            preview_order_request.order_metadata.account_id = account_id

        order_service: OrderService = self.order_services[ExchangeName[exchange.upper()]]
        response: PreviewOrderResponse = order_service.preview_order(preview_order_request)

        return jsonify(response)

    def place_order(self, exchange, account_id: str, preview_id: str):
        content_type = request.headers.get('Content-Type')
        if (content_type != 'application/json'):
            return 'Content-Type not supported!'

        place_order_request = PlaceOrderRequest.model_validate(request.json)
        if not place_order_request.order_metadata.account_id:
            place_order_request.order_metadata.account_id = account_id

        place_order_request.preview_id = preview_id

        order_service: OrderService = self.order_services[ExchangeName[exchange.upper()]]
        response: PlaceOrderResponse = order_service.place_order(place_order_request)

        return jsonify(response)

    def preview_and_place_order(self, exchange, account_id: str):
        content_type = request.headers.get('Content-Type')
        if (content_type != 'application/json'):
            return 'Content-Type not supported!'

        preview_order_request = PreviewOrderRequest.model_validate(request.json)
        if not preview_order_request.order_metadata.account_id:
            preview_order_request.order_metadata.account_id = account_id

        order_service: OrderService = self.order_services[ExchangeName[exchange.upper()]]
        preview_order_response: PreviewOrderResponse = order_service.preview_order(preview_order_request)
        preview_id = preview_order_response.preview_id

        order_metadata: OrderMetadata = preview_order_request.order_metadata
        order: Order = preview_order_request.order
        place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata=order_metadata, preview_id=preview_id,
                                                                   order=order)
        place_order_response: PlaceOrderResponse = order_service.place_order(place_order_request)
        return jsonify(place_order_response)

    def cancel_order(self, exchange: str, account_id: str, order_id: str):
        content_type = request.headers.get('Content-Type')
        if (content_type != 'application/json'):
            return 'Content-Type not supported!'

        cancel_order_request = CancelOrderRequest(account_id=account_id, order_id=order_id)
        order_service: OrderService = self.order_services[ExchangeName[exchange.upper()]]
        cancel_order_response: CancelOrderResponse = order_service.cancel_order(cancel_order_request)

        return jsonify(cancel_order_response)

if __name__ == "__main__":
    # Login To Exchange Here
    oex_app = OexRestService()
    oex_app.run(host="0.0.0.0", port=8080)