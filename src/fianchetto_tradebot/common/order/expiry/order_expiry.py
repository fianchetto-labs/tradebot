from abc import ABC
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class OrderExpiry(ABC, BaseModel):
    expiry_date: Optional[datetime] = None
    all_or_none: bool = False

    def valid_at(self, trade_date: datetime) -> bool:
        return trade_date < self.expiry_date

    def __str__(self):
        return f"Expiry date: {self.expiry_date} | All or None: {self.all_or_none}"

    def __repr__(self):
        return f"OrderExpiry({self.expiry_date}, {self.all_or_none})"

    def __eq__(self, other):
        if self.all_or_none != other.all_or_none:
            return False
        if self.expiry_date != other.expiry_date:
            return False

        return True