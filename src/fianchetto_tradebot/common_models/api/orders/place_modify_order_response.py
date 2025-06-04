from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse


class PlaceModifyOrderResponse(PlaceOrderResponse):
    previous_order_id: str
