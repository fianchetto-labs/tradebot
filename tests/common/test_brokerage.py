from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage


def test_ibkr_is_the_canonical_interactive_brokers_name():
    assert Brokerage.IBKR.value == "ibkr"


def test_ikbr_spelling_is_supported_as_a_backward_compatible_alias():
    assert Brokerage.IKBR is Brokerage.IBKR
    assert Brokerage("ikbr") is Brokerage.IBKR
