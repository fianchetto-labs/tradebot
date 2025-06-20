import pytest

from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import \
    CreateManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.moex_status import MoexStatus
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution, ManagedExecutionCreationParams, \
    ManagedExecutionCreationType
from fianchetto_tradebot.server.orders.tactics.incremental_price_delta_execution_tactic import \
    IncrementalPriceDeltaExecutionTactic


@pytest.fixture
def account_id():
    return "abc123"

@pytest.fixture
def order():
    ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
    order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=100, part=1))
    o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)
    return o

@pytest.fixture
def managed_execution(account_id):
    ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
    order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=100, part=1))
    reserve_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=120, part=1))
    o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)

    return ManagedExecution(brokerage=Brokerage.ETRADE, account_id=account_id, original_order=o, status=MoexStatus.PRE_SUBMISSION,
                                         latest_order_price=o.order_price, reserve_order_price=reserve_price)

def test_managed_execution_json_serde(managed_execution, account_id):
    # serialize to json
    as_json = managed_execution.model_dump_json()

    # deserialize from json
    reserialized_from_json: ManagedExecution = ManagedExecution.model_validate_json(as_json)

    assert reserialized_from_json.account_id == account_id
    assert reserialized_from_json.tactic == IncrementalPriceDeltaExecutionTactic

def test_managed_execution_dict_serde(managed_execution: ManagedExecution, account_id: str):
    # serialize to json
    as_dict = managed_execution.model_dump()

    # deserialize from json
    reserialized: ManagedExecution = ManagedExecution.model_validate(as_dict)

    assert reserialized.account_id == account_id
    assert reserialized.tactic == IncrementalPriceDeltaExecutionTactic

def test_create_managed_execution_request_json_serde(managed_execution, account_id):
    create_managed_execution_request: CreateManagedExecutionRequest = CreateManagedExecutionRequest(account_id=account_id, managed_execution=managed_execution)

    # serialize to json
    as_json: str = create_managed_execution_request.model_dump_json()

    # deserialize from json
    reserialized_from_json: ManagedExecution = CreateManagedExecutionRequest.model_validate_json(as_json)

    assert reserialized_from_json.account_id == account_id
    assert reserialized_from_json.managed_execution.tactic == IncrementalPriceDeltaExecutionTactic

def test_create_managed_execution_request_json_serde(managed_execution, account_id, order):
    # TODO: Add more tests for the various other option types
    managed_execution_creation_params: ManagedExecutionCreationParams = ManagedExecutionCreationParams(managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER, brokerage=Brokerage.ETRADE, account_id=account_id, creation_order=order)
    create_managed_execution_request: CreateManagedExecutionRequest = CreateManagedExecutionRequest(managed_execution_creation_params=managed_execution_creation_params)

    # serialize to dict
    as_dict: str = create_managed_execution_request.model_dump()

    # deserialize from dict
    reserialized_from_json: CreateManagedExecutionRequest = CreateManagedExecutionRequest.model_validate(as_dict)

    assert reserialized_from_json.managed_execution_creation_params.account_id == account_id
    assert reserialized_from_json.managed_execution_creation_params.tactic == IncrementalPriceDeltaExecutionTactic

def test_managed_execution_new_order_creation_request_from_string():
    input = '{"managed_execution_creation_type":"AS_NEW_ORDER","brokerage":"etrade","account_id":"ABC123","reserve_order_price":null,"tactic":"IncrementalPriceDeltaExecutionTactic","creation_order":{"expiry":{"expiry_date":null,"all_or_none":false},"order_lines":[{"tradable":{"__type__":"Equity","price":null,"ticker":"GE","company_name":null},"action":"BUY","quantity":1,"quantity_filled":-1}],"order_price":{"order_price_type":"LIMIT","price":{"whole":100,"part":1,"currency":"USD","negative":false}}},"creation_order_id":null}'
    managed_execution_creation_params: ManagedExecutionCreationParams = ManagedExecutionCreationParams.model_validate_json(input)

    assert managed_execution_creation_params.account_id == "ABC123"
