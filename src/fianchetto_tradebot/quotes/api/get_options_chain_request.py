from datetime import date

from pydantic import BaseModel


class GetOptionsChainRequest(BaseModel):
    ticker: str
    expiry: date