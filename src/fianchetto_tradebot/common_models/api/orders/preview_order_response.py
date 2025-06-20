from typing import Optional

from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.order_placement_message import OrderPlacementMessage
from fianchetto_tradebot.common_models.api.orders.order_preview import OrderPreview
from fianchetto_tradebot.common_models.api.request_status import RequestStatus
from fianchetto_tradebot.common_models.api.response import Response


class PreviewOrderResponse(Response):
    order_metadata: OrderMetadata
    preview_id: Optional[str]
    preview_order_info: Optional[OrderPreview]
    request_status: RequestStatus = RequestStatus.SUCCESS
    order_messages: Optional[list[OrderPlacementMessage]] = []
