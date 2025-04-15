from pydantic import BaseModel


class OrderCancellationMessage(BaseModel):
    code: str
    message: str