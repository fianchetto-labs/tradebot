from datetime import date
from pydantic import BaseModel

from fianchetto_tradebot.common_models.api.quotes.get_options_chain_request import GetOptionsChainRequest


class GetOptionsChainAtExpiryRequest(GetOptionsChainRequest):
    ticker: str
    expiry: date