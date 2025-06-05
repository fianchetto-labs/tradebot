from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage


class ListManagedExecutionsRequest(Request):
    accounts: dict[Brokerage, str]
    # TODO: Filter for active vs. finished, cancelled, etc.
