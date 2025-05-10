from pydantic import BaseModel

from fianchetto_tradebot.common_models.finance.option import Option


class Contract(BaseModel):
    option: Option