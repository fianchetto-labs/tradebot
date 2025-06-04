import threading
import time
from asyncio import Future
from threading import Lock, Thread

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
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_request import \
    GetManagedExecutionRequest
from fianchetto_tradebot.common_models.managed_executions.get_managed_execution_response import \
    GetManagedExecutionResponse
from fianchetto_tradebot.common_models.managed_executions.list_managed_executions_request import \
    ListManagedExecutionsRequest
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
from fianchetto_tradebot.server.orders.managed_order_execution import ManagedExecution
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

    def __call__(self, *args, **kwargs):
        print(f"Executing order {self.moex_id}")
        orders_service = self.orders_services[self.moex.brokerage]
        quotes_service = self.quotes_services[self.moex.brokerage]
        order = self.moex.original_order
        account_id = self.moex.account_id
        try:
            # If the order is submitted, check its status. If it's not submitted, submit it.
            order_id = self.moex.current_brokerage_order_id
            if not order_id:
                order_type = self.moex.original_order.get_order_type()
                client_order_id = OrderUtil.generate_random_client_order_id()
                order_metadata: OrderMetadata = OrderMetadata(order_type=order_type, account_id=account_id, client_order_id=client_order_id)

                place_order_request: PreviewPlaceOrderRequest = PreviewPlaceOrderRequest(order_metadata=order_metadata, order=order)
                place_order_response = orders_service.preview_and_place_order(place_order_request)

                order_id = place_order_response.order_id

            # Get order status
            get_order_request = GetOrderRequest(account_id=account_id, order_id=order_id)
            get_order_response : GetOrderResponse = orders_service.get_order(get_order_request)

            current_status = get_order_response.placed_order.placed_order_details.status
            current_price = get_order_response.placed_order.placed_order_details.current_market_price

            while current_status != OrderStatus.EXECUTED:
                new_price, wait_time = self.tactic.new_price(place_order_response.order, quotes_service)
                order.order_price = new_price

                preview_modify_order_request: PreviewModifyOrderRequest = PreviewModifyOrderRequest(order_id_to_modify=order_id, order_metadata=order_metadata, order=order)
                place_order_response: PlaceOrderResponse = orders_service.modify_order(preview_modify_order_request=preview_modify_order_request)

                order_id = place_order_response.order_id
                print(f"Successfully placed {place_order_response.order_id} for price {place_order_response.order.order_price}")

                print(f"Sleeping {wait_time} seconds")
                time.sleep(wait_time)

                get_order_request = GetOrderRequest(account_id=account_id, order_id=order_id)
                get_order_response : GetOrderResponse = orders_service.get_order(get_order_request)

                current_status = get_order_response.placed_order.placed_order_details.status
                current_price = get_order_response.placed_order.order.order_price

            print(f"Order {order_id} executed at price {current_price}!")
        except Exception as e:
            print(f"Error occurred: {e}")

class MoexService:
    def __init__(self, quotes_services: dict[Brokerage, QuotesService], orders_services: dict[Brokerage, OrderService]):
        self.quotes_services: dict[Brokerage, QuotesService] = quotes_services
        self.orders_services: dict[Brokerage, OrderService] = orders_services

        # todo - figureout a way to keep this running until it's explicitly closed
        self.thread_pool_executor = PersistentThreadPool(max_workers=10)

        # Managed data structure
        # TODO: Replace with `ThreadSafeDict`
        self.managed_executions: dict[str, (ManagedExecution, Future)] = dict[str, (ManagedExecution, Future)]()

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
    def list_managed_executions(self, list_managed_executions_request: ListManagedExecutionsRequest):
        return None

    def get_managed_execution(self, get_managed_execution_request: GetManagedExecutionRequest)->GetManagedExecutionResponse:

        return None

    def shutdown(self):
        print("...shutting down...")
        self._shutdown_engage = True

    def create_managed_execution(self, create_managed_execution_request: CreateManagedExecutionRequest)->GetManagedExecutionResponse:
        new_id = self._increment_id()

        managed_execution = create_managed_execution_request.managed_execution
        worker: ManagedExecutionWorker = ManagedExecutionWorker(moex=managed_execution, moex_id=str(new_id), quotes_services=self.quotes_services, orders_services=self.orders_services)
        future: Future = self.thread_pool_executor.submit(worker)

        with self.managed_executions_lock:
            self.managed_executions[str(new_id)] = (managed_execution,  future)
        print(f"Added new execution {new_id}")

        res = future.result()
        print(res)

    def cancel_managed_execution(self, cancel_managed_executions_request: CancelManagedExecutionRequest)->CancelManagedExecutionResponse:
        # Let's assume that it has not yet been executed
        managed_execution_id: str = cancel_managed_executions_request.managed_execution_id
        with self.managed_executions_lock:
            managed_execution, thread = self.managed_executions[managed_execution_id]
            # TODO: Implement cancelling this
            thread: Thread = thread
            pass

    def _increment_id(self):
        with self.id_generation_lock:
            self.current_id += 1

        return self.current_id

if __name__ == "__main__":

    quotes_services = dict[Brokerage, QuotesService]()
    orders_services = dict[Brokerage, OrderService]()

    connector: ETradeConnector = ETradeConnector()
    quotes_services[Brokerage.ETRADE] = ETradeQuotesService(connector)
    orders_services[Brokerage.ETRADE] = ETradeOrderService(connector)

    moex_service: MoexService = MoexService(quotes_services, orders_services)

    app_thread = threading.Thread(target=moex_service.run)
    app_thread.start()

    account_id = "1XRq48Mv_HUiP8xmEZRPnA"
    ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=1)
    order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=100, part=1))
    reserve_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=120, part=1))
    o: Order = Order(expiry=GoodUntilCancelled(), order_lines=[ol], order_price=order_price)

    managed_execution = ManagedExecution(brokerage=Brokerage.ETRADE, account_id=account_id, original_order=o, latest_order_price=o.order_price, reserve_order_price=reserve_price)

    create_managed_execution_request = CreateManagedExecutionRequest(account_id=account_id, managed_execution=managed_execution)

    moex_service.create_managed_execution(create_managed_execution_request=create_managed_execution_request)

    moex_service.shutdown()



