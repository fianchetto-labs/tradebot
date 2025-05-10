from abc import ABC


class Connector(ABC):
    def get_brokerage(self):
        return self.brokerage
