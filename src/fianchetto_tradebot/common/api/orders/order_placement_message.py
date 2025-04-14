from pydantic import BaseModel


class OrderPlacementMessage(BaseModel):
    message: str