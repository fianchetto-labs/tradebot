from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest

class PreviewModifyOrderRequest(PreviewOrderRequest):
    order_id_to_modify: str