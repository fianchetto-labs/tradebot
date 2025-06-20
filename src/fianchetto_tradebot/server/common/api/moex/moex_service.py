import string
import threading
import time
from asyncio import Future
from random import choice
from threading import Lock
from venv import create

from fastapi import HTTPException

from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.get_order_request import GetOrderRequest
from fianchetto_tradebot.common_models.api.orders.get_order_response import GetOrderResponse
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_place_order_request import PreviewPlaceOrderRequest
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
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
from fianchetto_tradebot.common_models.managed_executions.list_managed_executions_request import \
    ListManagedExecutionsRequest
from fianchetto_tradebot.common_models.managed_executions.list_managed_executions_response import \
    ListManagedExecutionsResponse
from fianchetto_tradebot.common_models.managed_executions.moex_status import MoexStatus
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.common.api.orders.etrade.etrade_order_service import ETradeOrderService
from fianchetto_tradebot.server.common.api.orders.order_service import OrderService
from fianchetto_tradebot.server.common.api.orders.order_util import OrderUtil
from fianchetto_tradebot.server.common.brokerage.etrade.etrade_connector import ETradeConnector
from fianchetto_tradebot.server.common.service.service_key import ServiceKey
from fianchetto_tradebot.server.common.threading.persistent_thread_pool import PersistentThreadPool
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution, ManagedExecutionCreationParams, \
    ManagedExecutionCreationType
from fianchetto_tradebot.server.orders.tactics.execution_tactic import ExecutionTactic
from fianchetto_tradebot.server.quotes.etrade.etrade_quotes_service import ETradeQuotesService
from fianchetto_tradebot.server.quotes.quotes_service import QuotesService

class ManagedExecutionWorker:
    def __init__(self, moex: ManagedExecution, moex_id: str, quotes_services: dict[Brokerage, QuotesService], orders_services: dict[Brokerage, OrderService]):
        # This object gets modified in this process
        self.moex: ManagedExecution = moex
        self.moex_id: str = moex_id
        self.tactic: ExecutionTactic = moex.tactic
        self.quotes_services: dict[Brokerage, QuotesService] = quotes_services
        self.orders_services: dict[Brokerage, OrderService] = orders_services
        self.continue_processing = True

    def stop(self):
        print(f"Moex_id_thread {self.moex_id}: Received command to stop processing")
        self.continue_processing = False

    def __call__(self, *args, **kwargs):
        print(f"Executing order {self.moex_id}")
        orders_service = self.orders_services[self.moex.brokerage]
        quotes_service = self.quotes_services[self.moex.brokerage]
        order = self.moex.original_order
        account_id = self.moex.account_id
        try:
            # If the order is submitted, check its status. If it's not submitted, submit it.

            order_id = self.moex.current_brokerage_order_id
            order_metadata = None

            if not order_id:
                if not self.moex.original_order:
                    raise Exception("must provide order_id or order")
                order_type = self.moex.original_order.get_order_type()
                client_order_id = OrderUtil.generate_random_client_order_id()
                order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

                place_order_request: PreviewPlaceOrderRequest = PreviewPlaceOrderRequest(order_metadata=order_metadata, order=order)

                place_order_response = orders_service.preview_and_place_order(place_order_request)
                order_id = place_order_response.order_id

                if 'event_creation_lock' in kwargs:
                    event: threading.Event = kwargs['event_creation_lock']
                    print(f"Brokerage order {order_id} available for MOEX.")
                    event.set()
            else:
                # TODO: There is probably a more elegant way
                if 'event_creation_lock' in kwargs:
                    event: threading.Event = kwargs['event_creation_lock']
                    print(f"Brokerage order {order_id} available for MOEX.")
                    event.set()

            # Get order status
            self.moex.current_brokerage_order_id = order_id
            get_order_request = GetOrderRequest(account_id=account_id, order_id=order_id)
            get_order_response : GetOrderResponse = orders_service.get_order(get_order_request)

            current_status = get_order_response.placed_order.placed_order_details.status
            self.moex.status = current_status
            current_price = get_order_response.placed_order.placed_order_details.current_market_price

            order = get_order_response.placed_order.order
            if not order_metadata:
                length = 15
                characters = string.ascii_letters + string.digits
                new_client_order_id = ''.join(choice(characters) for _ in range(length))
                order_metadata: OrderMetadata = OrderMetadata(order_type=order.get_order_type(), account_id=account_id, client_order_id=new_client_order_id)

            while current_status != OrderStatus.EXECUTED and self.continue_processing:
                new_price, wait_time = self.tactic.new_price(get_order_response.placed_order.order, quotes_service)

                # Need to populate this --
                order.order_price = new_price

                preview_modify_order_request: PreviewModifyOrderRequest = PreviewModifyOrderRequest(order_id_to_modify=order_id, order_metadata=order_metadata, order=order)
                place_order_response: PlaceOrderResponse = orders_service.modify_order(preview_modify_order_request=preview_modify_order_request)

                order_id = place_order_response.order_id
                print(f"Successfully placed {place_order_response.order_id} for price {place_order_response.order.order_price}")
                self.moex.current_brokerage_order_id = order_id
                self.moex.status = OrderStatus.OPEN

                print(f"Sleeping {wait_time} seconds")
                time.sleep(wait_time)

                get_order_request = GetOrderRequest(account_id=account_id, order_id=order_id)
                get_order_response : GetOrderResponse = orders_service.get_order(get_order_request)

                current_status = get_order_response.placed_order.placed_order_details.status
                current_price = get_order_response.placed_order.order.order_price

            if not self.continue_processing:
                print(f"Moex id {self.moex_id} cancelled with latest order-id {order_id} at price {current_price}!")
            else:
                print(f"Moex id {self.moex_id} executed with latest order-id {order_id} at price {current_price}!")
        except Exception as e:
            print(f"Error occurred: {e}")

        print(f"Moex_id_thread {self.moex_id}: Finished")

    @staticmethod
    def generate_random_alphanumeric(length=15):
        characters = string.ascii_letters + string.digits
        return ''.join(choice(characters) for _ in range(length))

class MoexService:
    def __init__(self, quotes_services: dict[Brokerage, QuotesService], orders_services: dict[Brokerage, OrderService]):
        self.quotes_services: dict[Brokerage, QuotesService] = quotes_services
        self.orders_services: dict[Brokerage, OrderService] = orders_services

        # todo - figure out a way to keep this running until it's explicitly closed
        self.thread_pool_executor = PersistentThreadPool(max_workers=10)

        # Managed data structure
        # TODO: Replace with `ThreadSafeDict`
        self.managed_executions: dict[str, (ManagedExecution, ManagedExecutionWorker, Future)] = dict[str, (ManagedExecution, ManagedExecutionWorker, Future)]()

        self.managed_executions_lock: Lock = Lock()
        self.id_generation_lock: Lock = Lock()

        # TODO: This will shift into a distributed lock, or some sort of UUID mechanism
        self.current_id:int = 0

        self._shutdown_engage: bool = False

    def run(self):
        print(f"{ServiceKey.MOEX} service running")
        try:
            while not self._shutdown_engage:
                time.sleep(1)  # Idle loop, waiting for tasks
        except KeyboardInterrupt:
            print("Shutting down application...")
            self.shutdown()

    ### Managed Executions - to be cleaved off into a separate service
    def list_managed_executions(self, list_managed_executions_request: ListManagedExecutionsRequest)->ListManagedExecutionsResponse:
        account_ids: dict[Brokerage, str] = list_managed_executions_request.accounts
        output_list: list[(str, ManagedExecution)] = list[(str, ManagedExecution)]()

        # TODO: Write unit test for this
        for brokerage, account_id in account_ids.items():
            managed_executions_to_futures: list[(str, (ManagedExecution, ManagedExecutionWorker, Future))] = list(self.managed_executions.items())

            managed_executions_to_futures_for_account: list[(str, (ManagedExecution, ManagedExecutionWorker, Future))] = list(filter(lambda p: p[1][0].account_id == account_id and p[1][0].brokerage == brokerage, list(managed_executions_to_futures)))

            exec_list: list[(str, ManagedExecution)] = list(map(lambda managed_execution: (str(managed_execution[0]), managed_execution[1][0]), managed_executions_to_futures_for_account))
            output_list += exec_list

        return ListManagedExecutionsResponse(managed_executions_list=output_list)

    def get_managed_execution(self, get_managed_execution_request: GetManagedExecutionRequest)->GetManagedExecutionResponse:
        # TODO: Try := form
        managed_execution_id = get_managed_execution_request.managed_execution_id
        if managed_execution_id in self.managed_executions:
            managed_execution: ManagedExecution = self.managed_executions[managed_execution_id][0]
            return GetManagedExecutionResponse(managed_execution=managed_execution)
        else:
            # Raise 404 here
            raise HTTPException(status_code=404, detail=f"Managed execution {managed_execution_id} not found")

    def shutdown(self):
        print("...shutting down...")
        self._shutdown_engage = True

    def create_managed_execution(self, create_managed_execution_request: CreateManagedExecutionRequest)->CreateManagedExecutionResponse:
        new_id = self._increment_id()
        creation_request_params = create_managed_execution_request.managed_execution_creation_params
        managed_execution: ManagedExecution = ManagedExecution(brokerage=creation_request_params.brokerage, account_id=creation_request_params.account_id,
                                                               original_order=creation_request_params.creation_order,
                                                               original_order_id=creation_request_params.creation_order_id, current_brokerage_order_id=creation_request_params.creation_order_id, status=MoexStatus.PRE_SUBMISSION)

        # TODO: In a cleaner implementation, the wait would be internal to the Worker - FIA-127
        order_creation_event = threading.Event()

        with self.managed_executions_lock:
            worker: ManagedExecutionWorker = ManagedExecutionWorker(moex=managed_execution, moex_id=str(new_id), quotes_services=self.quotes_services, orders_services=self.orders_services)
            future: Future = self.thread_pool_executor.submit(worker, event_creation_lock=order_creation_event)

            # TODO: This ought to be configurable
            success = order_creation_event.wait(timeout=15)
            assert success, "Could not create event in a meaningful amount of time"

            self.managed_executions[str(new_id)] = (managed_execution, worker, future)
            print(f"Added new execution {new_id}")

        return CreateManagedExecutionResponse(managed_execution_id = str(new_id))

    def update_managed_execution(self):
        # See FIA-113 on implementation notes
        pass

    def cancel_managed_execution(self, cancel_managed_executions_request: CancelManagedExecutionRequest)->CancelManagedExecutionResponse:
        # Let's assume that it has not yet been executed
        managed_execution_id: str = cancel_managed_executions_request.managed_execution_id
        with self.managed_executions_lock:
            managed_execution, worker, future = self.managed_executions[managed_execution_id]

            # Cancel the future first so it doesn't create a new order after-the-fact
            worker: ManagedExecutionWorker = worker
            worker.stop()

            # cancel the order
            managed_execution : ManagedExecution = managed_execution
            order_service: OrderService = self.orders_services[managed_execution.brokerage]
            if managed_execution.current_brokerage_order_id:
                cancel_order_request: CancelOrderRequest = CancelOrderRequest(account_id=managed_execution.account_id, order_id=managed_execution.current_brokerage_order_id)
                cancel_order_response: CancelOrderResponse = order_service.cancel_order(cancel_order_request)
                print(f"Moex id: {managed_execution_id} - cancelled order {cancel_order_response.order_id} at {cancel_order_response.cancel_time}")
            else:
                print(f"There is currently no open order for {managed_execution_id}, so nothing to cancel.")

            return CancelManagedExecutionResponse(managed_execution=managed_execution)

    def _increment_id(self):
        with self.id_generation_lock:
            self.current_id += 1

        return self.current_id

def create_moex_with_new_order_list_and_cancel(existing_order_id: str = None):
    quotes_services = dict[Brokerage, QuotesService]()
    orders_services = dict[Brokerage, OrderService]()

    connector: ETradeConnector = ETradeConnector()
    quotes_services[Brokerage.ETRADE] = ETradeQuotesService(connector)
    orders_services[Brokerage.ETRADE] = ETradeOrderService(connector)

    moex_service: MoexService = MoexService(quotes_services, orders_services)
    app_thread = threading.Thread(target=moex_service.run)
    app_thread.start()

    account_id = "1XRq48Mv_HUiP8xmEZRPnA"
    if not existing_order_id:
        ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
        order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=100, part=1))
        o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)

        managed_execution_creation_params = ManagedExecutionCreationParams(
            managed_execution_creation_type=ManagedExecutionCreationType.AS_NEW_ORDER, brokerage=Brokerage.ETRADE,
            account_id=account_id, creation_order=o)
    else:
        managed_execution_creation_params = ManagedExecutionCreationParams(
            managed_execution_creation_type=ManagedExecutionCreationType.FROM_EXISTING_ORDER, brokerage=Brokerage.ETRADE,
            account_id=account_id, creation_order_id=existing_order_id)

    create_managed_execution_request = CreateManagedExecutionRequest(
        managed_execution_creation_params=managed_execution_creation_params)

    as_json = create_managed_execution_request.model_dump_json()
    print(as_json)

    moex_service.create_managed_execution(create_managed_execution_request=create_managed_execution_request)
    brokerage_to_accounts: dict[Brokerage, str] = dict[Brokerage, str]()
    brokerage_to_accounts[Brokerage.ETRADE] = account_id

    list_managed_executions_request = ListManagedExecutionsRequest(accounts=brokerage_to_accounts)
    executions = moex_service.list_managed_executions(
        list_managed_executions_request=list_managed_executions_request)
    print(executions.managed_executions_list)

    exec_id = executions.managed_executions_list[0][0]
    get_managed_execution_response: GetManagedExecutionResponse = moex_service.get_managed_execution(
        GetManagedExecutionRequest(account_id=account_id, managed_execution_id=exec_id))
    print(get_managed_execution_response.managed_execution)

    #cancel_managed_execution_request: CancelManagedExecutionRequest = CancelManagedExecutionRequest(
    #    managed_execution_id=exec_id)
    #cancel_managed_execution_response: CancelManagedExecutionResponse = moex_service.cancel_managed_execution(
    #    cancel_managed_execution_request)
    #print(cancel_managed_execution_response)
    moex_service.shutdown()

if __name__ == "__main__":
    #print("Testing with new order:")
    #create_moex_with_new_order_list_and_cancel()
    #print("End test with new order")

    existing_order_id = 91488
    print(f"Testing with new order: {existing_order_id}")
    create_moex_with_new_order_list_and_cancel(str(existing_order_id))
    print("End test with new order")


