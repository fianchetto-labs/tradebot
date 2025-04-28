from pydantic import BaseModel


class GetOptionExpireDatesRequest(BaseModel):
    ticker: str