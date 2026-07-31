from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage


def test_ibkr_is_the_canonical_interactive_brokers_name():
    assert Brokerage.IBKR.value == "ibkr"
