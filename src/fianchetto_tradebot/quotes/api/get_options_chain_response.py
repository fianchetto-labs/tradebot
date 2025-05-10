from pydantic import BaseModel

from fianchetto_tradebot.common_models.finance.chain import Chain


class GetOptionsChainResponse(BaseModel):
    options_chain: Chain