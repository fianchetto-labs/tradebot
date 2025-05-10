from datetime import date
from typing import Optional

from pydantic import BaseModel


class GetOptionsChainRequest(BaseModel):
    ticker: str
    expiry: Optional[date] = None