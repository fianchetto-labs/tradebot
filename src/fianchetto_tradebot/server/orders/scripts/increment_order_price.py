from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector


# TODO: Finish this

def get_latest_order():
    pass

def increment_order_price(order_id: str = None):
    pass


if __name__ == "__main__":
    # Assuming the service is up on the standard port
    connector: ETradeConnector = ETradeConnector()
    session, async_session, base_url = connector.load_connection()

    get_order_request = GetOrderRequest()


