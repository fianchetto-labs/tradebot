from abc import ABC

from fianchetto_tradebot.common.exchange.connector import Connector


class ApiService(ABC):
    def __init__(self, connector: Connector):
        self.connector = connector