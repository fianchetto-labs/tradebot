from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest


class PlaceModifyOrderRequest(PlaceOrderRequest):
    order_id_to_modify: str