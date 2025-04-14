from typing import Callable

from fianchetto_tradebot.common.finance.amount import Amount
from fianchetto_tradebot.common.finance.options.order_analysis import OrderAnalysis


class OptionOrderAnalysis(OrderAnalysis):
    def get_value_at_expiry_function(self) -> Callable[[Amount], Amount]:
        pass
