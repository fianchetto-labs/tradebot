from datetime import date
from pydantic import BaseModel


class GetOptionsChainAtExpiryRequest(BaseModel):
    ticker: str
    expiry: date