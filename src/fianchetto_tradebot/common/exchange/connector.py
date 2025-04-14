from abc import ABC


class Connector(ABC):
    def get_exchange(self):
        return self.exchange
