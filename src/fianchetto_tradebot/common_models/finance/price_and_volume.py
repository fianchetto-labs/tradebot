from pydantic import BaseModel

from fianchetto_tradebot.common_models.finance.amount import Amount

class PriceAndVolume(BaseModel):
    price: Amount
    volume: float