import json
from time import sleep

from fianchetto_tradebot.common.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common.api.orders.etrade.converters.order_conversion_util import OrderConversionUtil
from fianchetto_tradebot.common.api.orders.etrade.etrade_order_response_message import ETradeOrderResponseMessage
from fianchetto_tradebot.common.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common.api.orders.order_cancellation_message import OrderCancellationMessage
from fianchetto_tradebot.common.api.orders.order_list_request import ListOrdersRequest
from fianchetto_tradebot.common.api.orders.order_list_response import ListOrdersResponse
from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_placement_message import OrderPlacementMessage
from fianchetto_tradebot.common.api.orders.order_preview import OrderPreview
from fianchetto_tradebot.common.api.orders.order_service import OrderService
from fianchetto_tradebot.common.api.orders.place_modify_order_request import PlaceModifyOrderRequest
from fianchetto_tradebot.common.api.orders.place_modify_order_response import PlaceModifyOrderResponse
from fianchetto_tradebot.common.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common.api.orders.preview_modify_order_response import PreviewModifyOrderResponse
from fianchetto_tradebot.common.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common.api.orders.preview_order_response import PreviewOrderResponse
from fianchetto_tradebot.common.api.request_status import RequestStatus
from fianchetto_tradebot.common.exchange.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.order.order import Order
from fianchetto_tradebot.common.order.order_status import OrderStatus
from fianchetto_tradebot.common.order.order_type import OrderType
from fianchetto_tradebot.common.order.placed_order import PlacedOrder

NOT_ENOUGH_SHARES_MSG_PORTION = "We did not find enough available shares of this security in your account"
DEFAULT_RETRY_SLEEP_SECONDS = 10
DEFAULT_NUM_RETRIES = 3

PARTIAL_EXECUTED_CODE = 167
ORDER_EXECUTED_OR_REJECTED_CODE = 5001

class ETradeOrderService(OrderService):
    def __init__(self, connector: ETradeConnector):
        super().__init__(connector)
        self.session, self.base_url = self.connector.load_connection()

    def list_orders(self, list_orders_request: ListOrdersRequest, exchange_specific_opts: dict[str, str]=None) -> ListOrdersResponse:
        account_id = list_orders_request.account_id
        path = f"/v1/accounts/{account_id}/orders.json"
        count = list_orders_request.count

        params = dict()
        params["count"] = count
        params["fromDate"] = list_orders_request.from_date.strftime("%m%d%Y")
        params["toDate"] = list_orders_request.to_date.strftime("%m%d%Y")

        if list_orders_request.status is not OrderStatus.ANY:
            params["status"] = list_orders_request.status.name

        if exchange_specific_opts:
            for k, v in exchange_specific_opts.items():
                params[k] = v

        url = self.base_url + path
        response = self.session.get(url, params=params)

        parsed_order_list: list[PlacedOrder] = ETradeOrderService._parse_order_list_response(response, account_id)
        return ListOrdersResponse(order_list=parsed_order_list)

    def get_order(self, get_order_request: GetOrderRequest) -> GetOrderResponse:
        account_id = get_order_request.account_id
        order_id = get_order_request.order_id
        path = f"/v1/accounts/{account_id}/orders/{order_id}.json"

        params = dict()
        params["status"] = "OPEN"

        url = self.base_url + path
        response = self.session.get(url, params=params)

        # TODO: Add option to pull current price for all tradables - FIA-
        return ETradeOrderService._parse_get_order_response(response, account_id, order_id)

    def cancel_order(self, cancel_order_request: CancelOrderRequest) -> CancelOrderResponse:
        account_id = cancel_order_request.account_id
        order_id = cancel_order_request.order_id

        headers = {"Content-Type": "application/xml", "consumerKey": account_id}

        # TODO: Weave through settings for priceType and possibly others.
        path = f"/v1/accounts/{account_id}/orders/cancel.json"
        payload = f"""
            <CancelOrderRequest>
              <orderId>{order_id}</orderId>
            </CancelOrderRequest>"""

        url = self.base_url + path
        response = self.session.put(url, header_auth=True, headers=headers, data=payload)
        print(response)
        return ETradeOrderService._parse_cancel_order_response(response, order_id)

    def preview_modify_order(self, preview_modify_order_request: PreviewModifyOrderRequest) -> PreviewModifyOrderResponse:
        order_metadata: OrderMetadata = preview_modify_order_request.order_metadata
        order_type = order_metadata.order_type
        account_id = order_metadata.account_id
        client_order_id = order_metadata.client_order_id

        order_id_to_modify = preview_modify_order_request.order_id_to_modify
        new_order = preview_modify_order_request.order

        headers = {"Content-Type": "application/xml", "consumerKey": account_id}
        path = f"/v1/accounts/{account_id}/orders/{order_id_to_modify}/change/preview.json"

        payload = ETradeOrderService._build_preview_order_xml(new_order, order_type, client_order_id)

        url = self.base_url + path
        return self._preview_order_resiliently(url, headers, payload, order_metadata)

    def preview_order(self, preview_order_request: PreviewOrderRequest) -> PreviewOrderResponse:
        order_metadata = preview_order_request.order_metadata
        order_type = order_metadata.order_type
        account_id = order_metadata.account_id
        client_order_id = order_metadata.client_order_id

        headers = {"Content-Type": "application/xml", "consumerKey": account_id}
        path = f"/v1/accounts/{account_id}/orders/preview.json"

        payload = ETradeOrderService._build_preview_order_xml(preview_order_request.order, order_type, client_order_id)

        url = self.base_url + path
        return self._preview_order_resiliently(url, headers, payload, order_metadata)

    def _preview_order_resiliently(self, url: object, headers: object, payload: object, order_metadata: object, previous_order_id = None,
                                   num_retries: int = DEFAULT_NUM_RETRIES) -> PreviewOrderResponse:
        if num_retries < 0:
            raise Exception(f"Retry count must not be negative! - {num_retries} provided")
        response = self.session.post(url, header_auth=True, headers=headers, data=payload)
        preview_order_response: PreviewOrderResponse = ETradeOrderService._parse_preview_order_response(response, order_metadata, previous_order_id)
        while num_retries:
            if preview_order_response.request_status == RequestStatus.FAILURE_DO_NOT_RETRY:
                raise Exception(f"Order not previewable - please fix {preview_order_response.order_message}")
            if preview_order_response.request_status == RequestStatus.FAILURE_RETRY_SUGGESTED:
                print(f"Sleeping {DEFAULT_RETRY_SLEEP_SECONDS} before retrying")
                sleep(DEFAULT_RETRY_SLEEP_SECONDS)

                response = self.session.post(url, header_auth=True, headers=headers, data=payload)
                preview_order_response = ETradeOrderService._parse_preview_order_response(response, order_metadata)
                num_retries -= 1
            if preview_order_response.request_status == RequestStatus.SUCCESS:
                return preview_order_response

        preview_order_response.request_status = RequestStatus.FAILURE_RETRIES_EXHAUSTED
        return preview_order_response

    def place_modify_order(self, place_modify_order_request: PlaceModifyOrderRequest) -> PlaceModifyOrderResponse:
        order_metadata = place_modify_order_request.order_metadata
        order_type = order_metadata.order_type
        account_id = order_metadata.account_id
        client_order_id = order_metadata.client_order_id

        previous_order_id = place_modify_order_request.order_id_to_modify

        headers = {"Content-Type": "application/xml", "consumerKey": account_id}

        preview_ids_xml: list[str] = []
        orders_xml: list[str] = []
        preview_id = place_modify_order_request.preview_id
        order = place_modify_order_request.order

        preview_ids_xml.append(f"<previewId>{preview_id}</previewId>")
        orders_xml.append(OrderConversionUtil.build_order(order))

        orders_str = "\n".join(orders_xml)
        preview_ids_str = "\n".join(preview_ids_xml)

        path = f"/v1/accounts/{account_id}/orders/{previous_order_id}/change/place.json"

        # TODO: Factor out this payload order so it can be used for order modification
        payload = f"""<PlaceOrderRequest>
                        <PreviewIds>
                        {preview_ids_str}
                        </PreviewIds>
                        <orderType>{order_type.name}</orderType>
                        <clientOrderId>{client_order_id}</clientOrderId>
                        {orders_str}
                      </PlaceOrderRequest>"""

        url = self.base_url + path
        response = self.session.put(url, header_auth=True, headers=headers, data=payload)
        return ETradeOrderService._parse_place_order_response(response, order_metadata, preview_id)

    def place_order(self, place_order_request: PlaceOrderRequest) -> PlaceOrderResponse:
        order_metadata = place_order_request.order_metadata
        order_type = order_metadata.order_type
        account_id = order_metadata.account_id
        client_order_id = order_metadata.client_order_id

        headers = {"Content-Type": "application/xml", "consumerKey": account_id}

        preview_ids_xml: list[str] = []
        orders_xml: list[str] = []
        preview_id = place_order_request.preview_id
        order = place_order_request.order

        preview_ids_xml.append(f"<previewId>{preview_id}</previewId>")
        orders_xml.append(OrderConversionUtil.build_order(order))

        orders_str = "\n".join(orders_xml)
        preview_ids_str = "\n".join(preview_ids_xml)

        path = f"/v1/accounts/{account_id}/orders/place.json"

        # TODO: Factor out this payload order so it can be used for order modification
        payload = f"""<PlaceOrderRequest>
                        <PreviewIds>
                        {preview_ids_str}
                        </PreviewIds>
                        <orderType>{order_type.name}</orderType>
                        <clientOrderId>{client_order_id}</clientOrderId>
                        {orders_str}
                      </PlaceOrderRequest>"""

        url = self.base_url + path
        response = self.session.post(url, header_auth=True, headers=headers, data=payload)
        return ETradeOrderService._parse_place_order_response(response, order_metadata, preview_id)

    def preview_and_place_order(self, preview_order_request: PreviewOrderRequest) -> PlaceOrderResponse:
        order_metadata = preview_order_request.order_metadata
        preview_order_response: PreviewOrderResponse = self.preview_order(preview_order_request)
        preview_id = preview_order_response.preview_id
        place_order_request: PlaceOrderRequest = PlaceOrderRequest(order_metadata, preview_id, preview_order_request.order)
        place_order_response: PlaceOrderResponse = self.place_order(place_order_request)

        return place_order_response

    @staticmethod
    def _parse_place_order_response(response, order_metadata: OrderMetadata, preview_id: str, previous_order_id=None)-> PlaceOrderResponse:
        data = json.loads(response.text)
        place_order_response = data["PlaceOrderResponse"]
        order_type = place_order_response['orderType'] if 'orderType' in place_order_response else None

        if not order_metadata.order_type:
            order_metadata.order_type = order_type

        order_id = place_order_response['OrderIds'][0]["orderId"]
        order_dict = place_order_response["Order"][0]

        messages = []
        for message in order_dict['messages']['Message']:
            description = message['description']
            code = message['code']
            message_type = message['type']
            messages.append(ETradeOrderResponseMessage(code=str(code), description=description, message_type=str(message_type)))

        # TODO: Why isn't this a PlacedOrder? b/c 'OrderDetail' isn't available from order_dict here.
        order: Order = OrderConversionUtil.to_order_from_json(order_dict)

        if previous_order_id:
            return PlaceModifyOrderResponse(order_metadata, preview_id, previous_order_id, order_id, order, messages)
        else:
            return PlaceOrderResponse(order_metadata=order_metadata, preview_id=str(preview_id), order_id=str(order_id), order=order, order_placement_messages=messages)

    @staticmethod
    def _parse_cancel_order_response(input, order_id:str)-> CancelOrderResponse:
        data = json.loads(input.text)
        if "CancelOrderResponse" not in data:
            print("There was no cancel order response!")
            error = data['Error']
            code = error['code']
            message = error['message']
            return CancelOrderResponse(order_id=order_id, cancel_time=None, messages=[OrderCancellationMessage(code, message)], request_status=RequestStatus.OPERATION_FAILED_BUT_NO_LONGER_REQUIRED)
        cancel_order_response = data["CancelOrderResponse"]

        order_id = cancel_order_response["orderId"]
        cancel_time = cancel_order_response["cancelTime"]

        messages = []
        for message in cancel_order_response['Messages']['Message']:
            description = message['description']
            code = message['code']
            message_type = message['type']
            messages.append(ETradeOrderResponseMessage(code, description, message_type))

        return CancelOrderResponse(order_id=order_id, cancel_time=cancel_time, messages=messages)

    @staticmethod
    def _parse_preview_order_response(response, order_metadata: OrderMetadata, previous_order_id=None)-> PreviewOrderResponse:
        data = json.loads(response.text)
        request_status = RequestStatus.SUCCESS
        if "PreviewOrderResponse" not in data:
            if 'Error' in data:
                error = data['Error']
                code = error['code'] if 'code' in error else None
                message = error['message'] if 'message' in error else None

                order_placement_message: OrderPlacementMessage = ETradeOrderResponseMessage(code=str(code), description=message)

                if NOT_ENOUGH_SHARES_MSG_PORTION in message or code == PARTIAL_EXECUTED_CODE:
                    request_status = RequestStatus.FAILURE_RETRY_SUGGESTED
                else:
                    request_status = RequestStatus.FAILURE_DO_NOT_RETRY
                if previous_order_id:
                    return PreviewModifyOrderResponse(order_metadata, None, previous_order_id, None, request_status=request_status, order_message=order_placement_message)
                else:
                    return PreviewOrderResponse(order_metadata=order_metadata, preview_id=None, preview_order_info=None, request_status=request_status, order_message=order_placement_message)
            else:
                request_status = RequestStatus.FAILURE_DO_NOT_RETRY

        preview_order_response = data["PreviewOrderResponse"]
        preview_ids: list[dict[str:str]] = preview_order_response["PreviewIds"]
        orders: list[dict] = preview_order_response["Order"]

        preview_id = preview_ids[0]["previewId"]
        order_dict = orders[0]

        estimated_total_amount: Amount = Amount.from_float(order_dict["estimatedTotalAmount"])
        estimated_commission: Amount = Amount.from_float(order_dict["estimatedCommission"])

        order = OrderConversionUtil.to_order_from_json(order_dict)
        order_preview: OrderPreview = OrderPreview(preview_id=str(preview_id), order=order, total_order_value=estimated_total_amount, estimated_commission=estimated_commission)

        # how to check if it replaces order
        if previous_order_id:
            return PreviewModifyOrderResponse(order_metadata=order_metadata, preview_id=preview_id, previous_order_id=str(previous_order_id), order_preview=order_preview, request_status=request_status)
        else:
            return PreviewOrderResponse(order_metadata=order_metadata, preview_id=str(preview_id), preview_order_info=order_preview, request_status=request_status)

    @staticmethod
    def _parse_order_list_response(response, account_id) -> list[PlacedOrder]:
        if response.status_code == '204':
            return list[PlacedOrder]()

        data = response.json()
        print(data)

        return_order_list: list[PlacedOrder] = []

        orders_response = data["OrdersResponse"]
        orders = orders_response['Order']

        for order in orders:
            order_detail = order["OrderDetail"][0]
            status: OrderStatus = OrderStatus[str(order_detail['status']).upper()]
            order_id = order["orderId"]

            placed_order: PlacedOrder = OrderConversionUtil.to_placed_order_from_json(order, account_id, order_id)

            if status == OrderStatus.EXECUTED:
                executed_order = OrderConversionUtil.to_executed_order_from_json(order, account_id=account_id)
                return_order_list.append(executed_order)
            else:
                return_order_list.append(placed_order)

        return return_order_list

    @staticmethod
    def _parse_get_order_response(response, account_id, order_id) -> GetOrderResponse:
        data = response.json()
        print(data)

        orders_response = data["OrdersResponse"]
        order = orders_response['Order'][0]

        placed_order: PlacedOrder = OrderConversionUtil.to_placed_order_from_json(order, account_id, order_id)

        if order["OrderDetail"][0]["status"] == OrderStatus.EXECUTED:
            executed_order = OrderConversionUtil.to_executed_order_from_json(order, account_id)
            return GetOrderResponse(placed_order=executed_order)
        else:
            return GetOrderResponse(placed_order=placed_order)

    @staticmethod
    def _build_preview_order_xml(order, order_type: OrderType, client_order_id: str)->str:
        orders_xml: list[str] = [OrderConversionUtil.build_order(order)]

        orders_str = "\n".join(orders_xml)
        return f"""<PreviewOrderRequest>
                       <orderType>{order_type.name}</orderType>
                       <clientOrderId>{client_order_id}</clientOrderId>
                       {orders_str}
                   </PreviewOrderRequest>"""

