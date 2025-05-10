from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.tradable import Tradable


class PricedOption(Tradable):
    option: Option

    def copy_of(self):
        return PricedOption(option=self.option, price=self.price)
