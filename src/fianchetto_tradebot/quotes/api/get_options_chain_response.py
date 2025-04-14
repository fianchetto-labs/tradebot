from fianchetto_tradebot.common.finance.chain import Chain


class GetOptionsChainResponse:
    def __init__(self, options_chain: Chain):
        # Perhaps a date will also be required
        self.options_chain = options_chain