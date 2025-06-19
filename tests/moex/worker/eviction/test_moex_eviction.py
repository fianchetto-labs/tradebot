from unittest.mock import MagicMock

import pytest

from common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_request import \
    CancelManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_response import \
    CancelManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import \
    CreateManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_response import \
    CreateManagedExecutionResponse
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.server.common.api.moex.moex_service import MoexService
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.orders.order_service import OrderService
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

@pytest.fixture
def order_id()->str:
    return "order_123"

@pytest.fixture
def account_id()->str:
    return "account_123"

@pytest.fixture
def order()->Order:
    return OrderTestUtil.build_spread_order()

@pytest.fixture
def sample_managed_execution(account_id: str, order_id: str, order: Order):
    managed_execution: ManagedExecution = ManagedExecution(brokerage=Brokerage.ETRADE, account_id=account_id,
                                                           original_order=order, latest_order_price=order.order_price,
                                                           reserve_order_price=order.order_price)
    return managed_execution

@pytest.fixture
def orders_service_map(account_id, order_id, order) -> dict[Brokerage, OrderService]:
    mock_etrade_orders_service: ETradeOrderService = MagicMock()

    order_metadata: OrderMetadata = OrderMetadata(order_type=OrderType.SPREADS, account_id=account_id)
    place_order_response: PlaceOrderResponse = PlaceOrderResponse(order_metadata=order_metadata, preview_id="preview_123", order_id=order_id, order=order)

    mock_etrade_orders_service.preview_and_place_order = MagicMock(return_value=place_order_response)
    order_service_map : dict[Brokerage, OrderService] = dict[Brokerage, OrderService]()
    order_service_map[Brokerage.ETRADE] = mock_etrade_orders_service

    return order_service_map

@pytest.fixture
def quotes_service_map()-> dict[Brokerage, QuotesService]:
    mock_etrade_quotes_service: ETradeQuotesService = MagicMock()
    quotes_service_map: dict[Brokerage, QuotesService] = dict[Brokerage, QuotesService]()
    quotes_service_map[Brokerage.ETRADE] = mock_etrade_quotes_service

    return quotes_service_map

# TODO: We want to perhaps add a service for this. Filed FIA-126 to discuss.
def test_all_managed_orders_closed_at_eod():
    # TODO: implement this
    pass

def test_order_cancelled_when_worker_killed(account_id: str, sample_managed_execution: ManagedExecution, quotes_service_map: dict[Brokerage, QuotesService], orders_service_map: dict[Brokerage, OrderService]):
    # Given
    # A user wants to cancel a managed execution.
    # The user has cancelled their order using the API
    # The request has been passed down into the MoexService
    # 1. Assume the MOEX is running. There is exactly 1 managed execution in progress
    mock_order_service = orders_service_map[Brokerage.ETRADE]
    moex_service = MoexService(quotes_services=quotes_service_map, orders_services=orders_service_map)
    create_managed_execution_request: CreateManagedExecutionRequest = CreateManagedExecutionRequest(account_id=account_id, managed_execution=sample_managed_execution)
    create_managed_execution_response: CreateManagedExecutionResponse = moex_service.create_managed_execution(create_managed_execution_request=create_managed_execution_request)

    # When
    # We issue the MOEX cancellation order.
    moex_id = create_managed_execution_response.managed_execution_id
    cancel_managed_execution_request: CancelManagedExecutionRequest = CancelManagedExecutionRequest(managed_execution_id=moex_id)
    cancel_managed_execution_response: CancelManagedExecutionResponse = moex_service.cancel_managed_execution(cancel_managed_executions_request=cancel_managed_execution_request)
    expected_order_id = cancel_managed_execution_response.managed_execution.current_brokerage_order_id

    if not cancel_managed_execution_response.managed_execution:
        raise Exception(f"Could not get managed_execution from cancel_managed_execution_response: {cancel_managed_execution_response}")

    if not cancel_managed_execution_response.managed_execution.current_brokerage_order_id:
        raise Exception(f"Could not get current_brokerage_order_id from"
                        f"cancel_managed_execution_response.managed_execution: {cancel_managed_execution_response.managed_execution.current_brokerage_order_id}")

    # Then
    # We see that the Brokerage Order is cancelled (using mocking).
    expected_input_to_cancel_order = CancelOrderRequest(account_id=account_id, order_id=expected_order_id)
    mock_order_service.cancel_order.assert_called_once_with(expected_input_to_cancel_order)


# TODO: Place into a separate class later
def test_order_price_competitive():
    # TODO: implement this
    pass

def test_worker_stopped_after_moex_cancellation_request():
    # TODO: implement this
    pass

def test_evicted_worker_no_longer_in_thread_pool():
    # TODO: implement this
    pass
