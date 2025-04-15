from fianchetto_tradebot.common.finance.amount import Amount

# TODO: Incorporate this
class PriceAndVolume:
    def __init__(self, price: Amount, volume: float):
        self.price = price
        self.volume = volume