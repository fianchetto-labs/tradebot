from fianchetto_tradebot.common.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common.api.orders.order_preview import OrderPreview
from fianchetto_tradebot.common.api.orders.preview_order_response import PreviewOrderResponse
from fianchetto_tradebot.common.api.request_status import RequestStatus


class PreviewModifyOrderResponse(PreviewOrderResponse):
    def __init__(self, order_metadata: OrderMetadata, preview_id, previous_order_id, order_preview: OrderPreview, request_status:RequestStatus = RequestStatus.SUCCESS):
        super().__init__(order_metadata, preview_id, order_preview, request_status=request_status)
        self.previous_order_id: str = previous_order_id
