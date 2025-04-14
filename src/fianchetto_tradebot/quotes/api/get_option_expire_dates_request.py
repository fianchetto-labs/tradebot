class GetOptionExpireDatesRequest:
    def __init__(self, symbol: str):
        # Perhaps a date will also be required
        self.symbol = symbol