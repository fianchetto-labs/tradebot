from fianchetto_tradebot.common_models.finance.option_type import OptionType


def test_get_parse_from_string_put():
    input = "pUt"
    assert OptionType.PUT == OptionType.from_str(input)


def test_get_parse_from_string_call():
    input = "CaLL"
    assert OptionType.CALL == OptionType.from_str(input)