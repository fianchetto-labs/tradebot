import threading
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from common.api.orders.order_test_util import OrderTestUtil
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.price import Price
from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_request import \
    CancelManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.cancel_managed_execution_response import \
    CancelManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_request import \
    CreateManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.create_managed_execution_response import \
    CreateManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_request import \
    GetManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_response import \
    GetManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.managed_execution_status import ManagedExecutionStatus
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.executed_order import ExecutedOrder
from fianchetto_tradebot.common_models.order.executed_order_details import ExecutionOrderDetails
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.common_models.order.order_type import OrderType
from fianchetto_tradebot.common_models.order.placed_order import PlacedOrder
from fianchetto_tradebot.common_models.order.placed_order_details import PlacedOrderDetails
from fianchetto_tradebot.server.common.api.moex.moex_service import (
    ManagedExecutionWorker,
    MoexService,
)
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.orders.order_service import OrderService
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution, ManagedExecutionCreationParams, \
    ManagedExecutionCreationType
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
                                                           reserve_order_price=order.order_price, status=ManagedExecutionStatus.PRE_SUBMISSION)
    return managed_execution

@pytest.fixture
def orders_service_map(account_id, order_id, order) -> dict[Brokerage, OrderService]:
    mock_etrade_orders_service: ETradeOrderService = MagicMock()

    order_metadata: OrderMetadata = OrderMetadata(order_type=OrderType.SPREADS, account_id=account_id)
    place_order_response: PlaceOrderResponse = PlaceOrderResponse(order_metadata=order_metadata, preview_id="preview_123", order_id=order_id, order=order)
    get_order_response = _get_order_response(account_id=account_id, order_id=order_id, order=order)
    cancel_order_response = CancelOrderResponse(order_id=order_id, cancel_time="2026-07-30T12:00:00", messages=[])

    mock_etrade_orders_service.preview_and_place_order = MagicMock(return_value=place_order_response)
    mock_etrade_orders_service.get_order = MagicMock(return_value=get_order_response)
    mock_etrade_orders_service.cancel_order = MagicMock(return_value=cancel_order_response)
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

@pytest.mark.functional
def test_managed_execution_succeeds_when_brokerage_order_executes(
    account_id: str,
    order_id: str,
    order: Order,
    quotes_service_map: dict[Brokerage, QuotesService],
    orders_service_map: dict[Brokerage, OrderService],
    capsys: pytest.CaptureFixture,
):
    # Given
    # A new managed execution request whose brokerage order is immediately executed.
    mock_order_service = orders_service_map[Brokerage.ETRADE]
    moex_service = MoexService(quotes_services=quotes_service_map, orders_services=orders_service_map)
    managed_execution_creation_params = ManagedExecutionCreationParams(
        managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER,
        brokerage=Brokerage.ETRADE,
        account_id=account_id,
        creation_order=order,
    )
    create_managed_execution_request = CreateManagedExecutionRequest(
        managed_execution_creation_params=managed_execution_creation_params
    )

    # When
    # The MOEX service creates the managed execution and the caller reads it back.
    try:
        create_managed_execution_response = moex_service.create_managed_execution(
            create_managed_execution_request=create_managed_execution_request
        )
        get_managed_execution_response: GetManagedExecutionResponse = moex_service.get_managed_execution(
            GetManagedExecutionRequest(
                managed_execution_id=create_managed_execution_response.managed_execution_id
            )
        )
    finally:
        moex_service.thread_pool_executor.shutdown(wait=True)

    # Then
    # The managed execution preserves both its own lifecycle state and the brokerage order state.
    managed_execution = get_managed_execution_response.managed_execution
    assert managed_execution.status == ManagedExecutionStatus.EXECUTED
    assert managed_execution.current_order_status == OrderStatus.EXECUTED
    assert managed_execution.current_brokerage_order_id == order_id
    mock_order_service.cancel_order.assert_not_called()
    captured = capsys.readouterr()
    assert "Error occurred" not in captured.out
    assert captured.err == ""


@pytest.mark.functional
def test_worker_signals_initial_order_ready_after_order_state_is_recorded(
    account_id: str,
    order_id: str,
    order: Order,
    quotes_service_map: dict[Brokerage, QuotesService],
    orders_service_map: dict[Brokerage, OrderService],
    capsys: pytest.CaptureFixture,
):
    # Given
    # A worker creating the first brokerage order for a managed execution.
    managed_execution = ManagedExecution(
        brokerage=Brokerage.ETRADE,
        account_id=account_id,
        original_order=order,
        status=ManagedExecutionStatus.PRE_SUBMISSION,
    )
    worker = ManagedExecutionWorker(
        moex=managed_execution,
        moex_id="moex-1",
        quotes_services=quotes_service_map,
        orders_services=orders_service_map,
    )
    readiness_event = MagicMock()

    def assert_initial_order_state_is_ready():
        assert managed_execution.current_brokerage_order_id == order_id
        assert managed_execution.current_order_status == OrderStatus.EXECUTED
        assert managed_execution.status == ManagedExecutionStatus.EXECUTED

    # The callback keeps us honest: if the worker signals early, these assertions fail.
    readiness_event.set.side_effect = assert_initial_order_state_is_ready

    # When
    # The worker reaches the initial readiness boundary.
    worker(event_creation_lock=readiness_event)

    # Then
    # The worker placed the order, fetched its first status, and signaled exactly once.
    mock_order_service = orders_service_map[Brokerage.ETRADE]
    mock_order_service.preview_and_place_order.assert_called_once()
    mock_order_service.get_order.assert_called_once_with(
        GetOrderRequest(account_id=account_id, order_id=order_id)
    )
    readiness_event.set.assert_called_once_with()
    assert managed_execution.current_brokerage_order_id == order_id
    assert managed_execution.current_order_status == OrderStatus.EXECUTED
    assert managed_execution.status == ManagedExecutionStatus.EXECUTED
    captured = capsys.readouterr()
    assert "Error occurred" not in captured.out
    assert captured.err == ""


@pytest.mark.functional
def test_cancel_request_does_not_change_executed_managed_execution(
    account_id: str,
    order: Order,
    quotes_service_map: dict[Brokerage, QuotesService],
    orders_service_map: dict[Brokerage, OrderService],
    capsys: pytest.CaptureFixture,
):
    # Given
    # A managed execution that reaches a terminal EXECUTED state before cancellation.
    mock_order_service = orders_service_map[Brokerage.ETRADE]
    moex_service = MoexService(quotes_services=quotes_service_map, orders_services=orders_service_map)
    managed_execution_creation_params: ManagedExecutionCreationParams = ManagedExecutionCreationParams(
        managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER,
        brokerage=Brokerage.ETRADE, account_id=account_id, creation_order=order)

    create_managed_execution_request: CreateManagedExecutionRequest = CreateManagedExecutionRequest(managed_execution_creation_params=managed_execution_creation_params)
    try:
        create_managed_execution_response: CreateManagedExecutionResponse = moex_service.create_managed_execution(create_managed_execution_request=create_managed_execution_request)

        # When
        # A caller requests cancellation after the terminal state has already been recorded.
        moex_id = create_managed_execution_response.managed_execution_id
        cancel_managed_execution_request: CancelManagedExecutionRequest = CancelManagedExecutionRequest(managed_execution_id=moex_id)
        cancel_managed_execution_response: CancelManagedExecutionResponse = moex_service.cancel_managed_execution(cancel_managed_executions_request=cancel_managed_execution_request)
        expected_order_id = cancel_managed_execution_response.managed_execution.current_brokerage_order_id
    finally:
        moex_service.thread_pool_executor.shutdown(wait=True)

    if not cancel_managed_execution_response.managed_execution:
        raise Exception(f"Could not get managed_execution from cancel_managed_execution_response: {cancel_managed_execution_response}")

    if not cancel_managed_execution_response.managed_execution.current_brokerage_order_id:
        raise Exception(f"Could not get current_brokerage_order_id from"
                        f"cancel_managed_execution_response.managed_execution: {cancel_managed_execution_response.managed_execution.current_brokerage_order_id}")

    # Then
    # The terminal managed execution state is not rewritten or cancelled downstream.
    mock_order_service.get_order.assert_called_once_with(GetOrderRequest(account_id=account_id, order_id=expected_order_id))
    mock_order_service.cancel_order.assert_not_called()
    assert cancel_managed_execution_response.managed_execution.status == ManagedExecutionStatus.EXECUTED
    assert cancel_managed_execution_response.managed_execution.current_order_status == OrderStatus.EXECUTED
    captured = capsys.readouterr()
    assert "Error occurred" not in captured.out
    assert captured.err == ""


@pytest.mark.functional
def test_worker_stops_before_next_broker_poll_after_cancellation(
    account_id: str,
    order_id: str,
    order: Order,
    quotes_service_map: dict[Brokerage, QuotesService],
    orders_service_map: dict[Brokerage, OrderService],
    capsys: pytest.CaptureFixture,
):
    # Given
    # A worker that has placed a replacement order and then receives a cancellation request.
    replacement_order_id = "replacement_order_123"
    managed_execution = ManagedExecution(
        brokerage=Brokerage.ETRADE,
        account_id=account_id,
        original_order=order,
        status=ManagedExecutionStatus.PRE_SUBMISSION,
    )
    worker = ManagedExecutionWorker(
        moex=managed_execution,
        moex_id="moex-1",
        quotes_services=quotes_service_map,
        orders_services=orders_service_map,
    )
    worker.tactic.new_price = MagicMock(return_value=(order.order_price, 0))

    mock_order_service = orders_service_map[Brokerage.ETRADE]
    mock_order_service.get_order = MagicMock(
        return_value=_get_placed_order_response(
            account_id=account_id,
            order_id=order_id,
            order=order,
            status=OrderStatus.OPEN,
        )
    )

    def cancel_after_replacement_order_is_placed(*args, **kwargs):
        worker.stop()
        return PlaceOrderResponse(
            order_metadata=OrderMetadata(order_type=OrderType.SPREADS, account_id=account_id),
            preview_id="replacement_preview_123",
            order_id=replacement_order_id,
            order=order,
        )

    mock_order_service.modify_order = MagicMock(side_effect=cancel_after_replacement_order_is_placed)

    # When
    # The cancellation arrives before the worker performs another broker read.
    worker()

    # Then
    # The worker does not poll the broker again and leaves the managed execution cancelled.
    mock_order_service.get_order.assert_called_once_with(
        GetOrderRequest(account_id=account_id, order_id=order_id)
    )
    assert managed_execution.current_brokerage_order_id == replacement_order_id
    assert managed_execution.status == ManagedExecutionStatus.CANCEL_REQUESTED
    captured = capsys.readouterr()
    assert "Error occurred" not in captured.out
    assert captured.err == ""


@pytest.mark.functional
def test_worker_cancellation_interrupts_wait_before_next_broker_poll(
    account_id: str,
    order_id: str,
    order: Order,
    quotes_service_map: dict[Brokerage, QuotesService],
    orders_service_map: dict[Brokerage, OrderService],
    capsys: pytest.CaptureFixture,
):
    # Given
    # A worker that would otherwise wait before checking a replacement order again.
    replacement_order_id = "replacement_order_123"
    managed_execution = ManagedExecution(
        brokerage=Brokerage.ETRADE,
        account_id=account_id,
        original_order=order,
        status=ManagedExecutionStatus.PRE_SUBMISSION,
    )
    worker = ManagedExecutionWorker(
        moex=managed_execution,
        moex_id="moex-1",
        quotes_services=quotes_service_map,
        orders_services=orders_service_map,
    )
    worker.tactic.new_price = MagicMock(return_value=(order.order_price, 60))

    mock_order_service = orders_service_map[Brokerage.ETRADE]
    mock_order_service.get_order = MagicMock(
        return_value=_get_placed_order_response(
            account_id=account_id,
            order_id=order_id,
            order=order,
            status=OrderStatus.OPEN,
        )
    )
    replacement_order_placed = threading.Event()

    def mark_replacement_order_placed(*args, **kwargs):
        replacement_order_placed.set()
        return PlaceOrderResponse(
            order_metadata=OrderMetadata(order_type=OrderType.SPREADS, account_id=account_id),
            preview_id="replacement_preview_123",
            order_id=replacement_order_id,
            order=order,
        )

    mock_order_service.modify_order = MagicMock(side_effect=mark_replacement_order_placed)

    # When
    # Cancellation is requested while the worker is waiting before the next broker poll.
    worker_thread = threading.Thread(target=worker)
    worker_thread.start()
    assert replacement_order_placed.wait(timeout=1)
    worker.stop()
    worker_thread.join(timeout=1)

    # Then
    # The worker wakes promptly and does not perform the follow-up broker poll.
    assert not worker_thread.is_alive()
    mock_order_service.get_order.assert_called_once_with(
        GetOrderRequest(account_id=account_id, order_id=order_id)
    )
    mock_order_service.modify_order.assert_called_once()
    assert managed_execution.current_brokerage_order_id == replacement_order_id
    assert managed_execution.status == ManagedExecutionStatus.CANCEL_REQUESTED
    captured = capsys.readouterr()
    assert "Error occurred" not in captured.out
    assert captured.err == ""


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


def _get_order_response(account_id: str, order_id: str, order: Order) -> GetOrderResponse:
    placed_order = _placed_order(
        account_id=account_id,
        order_id=order_id,
        order=order,
        status=OrderStatus.EXECUTED,
    )
    return GetOrderResponse(
        placed_order=ExecutedOrder(
            order=placed_order,
            execution_order_details=ExecutionOrderDetails(
                order_value=Amount.from_float(100.0),
                executed_time=datetime(2026, 7, 30, 12, 1, 0),
            ),
        )
    )


def _get_placed_order_response(
    account_id: str,
    order_id: str,
    order: Order,
    status: OrderStatus,
) -> GetOrderResponse:
    return GetOrderResponse(
        placed_order=_placed_order(
            account_id=account_id,
            order_id=order_id,
            order=order,
            status=status,
        )
    )


def _placed_order(
    account_id: str,
    order_id: str,
    order: Order,
    status: OrderStatus,
) -> PlacedOrder:
    placed_order_details = PlacedOrderDetails(
        account_id=account_id,
        brokerage_order_id=order_id,
        status=status,
        order_placed_time=datetime(2026, 7, 30, 12, 0, 0),
        current_market_price=Price(bid=1.0, ask=1.2),
    )
    return PlacedOrder(order=order, placed_order_details=placed_order_details)
