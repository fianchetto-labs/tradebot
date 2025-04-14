from tests.common.util import chain_testing_util


def test_print_chain():
    c = chain_testing_util.build_chain()

    print(c)