from datetime import date

from pydantic import BaseModel


class GetOptionExpireDatesResponse(BaseModel):
    expire_dates: list[date]
