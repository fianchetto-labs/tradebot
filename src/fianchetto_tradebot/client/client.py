import string
from random import choice
from typing import Optional, Type

import requests
from pydantic import BaseModel

from fianchetto_tradebot.common_models.account.account import Account
from fianchetto_tradebot.common_models.api.account.list_accounts_request import ListAccountsRequest
from fianchetto_tradebot.common_models.api.account.get_account_balance_request import GetAccountBalanceRequest
from fianchetto_tradebot.common_models.api.account.get_account_balance_response import GetAccountBalanceResponse
from fianchetto_tradebot.common_models.api.account.get_account_request import GetAccountRequest
from fianchetto_tradebot.common_models.api.account.get_account_response import GetAccountResponse
from fianchetto_tradebot.common_models.api.account.list_accounts_response import ListAccountsResponse
from fianchetto_tradebot.common_models.api.orders.cancel_order_request import CancelOrderRequest
from fianchetto_tradebot.common_models.api.orders.cancel_order_response import CancelOrderResponse
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.place_order_request import PlaceOrderRequest
from fianchetto_tradebot.common_models.api.orders.place_order_response import PlaceOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_modify_order_request import PreviewModifyOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.api.orders.preview_order_response import PreviewOrderResponse
from fianchetto_tradebot.common_models.api.orders.preview_place_order_request import PreviewPlaceOrderRequest
from fianchetto_tradebot.common_models.api.portfolio.get_portfolio_request import GetPortfolioRequest
from fianchetto_tradebot.common_models.api.portfolio.get_portfolio_response import GetPortfolioResponse
from fianchetto_tradebot.common_models.api.quotes.get_option_expire_dates_request import GetOptionExpireDatesRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_at_expiry_request import \
    GetOptionsChainAtExpiryRequest
from fianchetto_tradebot.common_models.api.quotes.get_options_chain_request import GetOptionsChainRequest
from fianchetto_tradebot.common_models.api.quotes.get_tradable_request import GetTradableRequest
from fianchetto_tradebot.common_models.api.request import Request
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType
from fianchetto_tradebot.common_models.portfolio.portfolio_builder import Portfolio

DEFAULT_TIMEOUT_SECS = 300
DEFAULT_OEX_URL = "http://localhost:8080"
DEFAULT_QUOTES_URL = "http://localhost:8081"

class Client:

    def __init__(self, brokerage: Brokerage):
        # TODO: Adjust to automatically get the base_url for the type of request
        self.base_url = "http://localhost:8081"
        self.timeout = DEFAULT_TIMEOUT_SECS
        self.brokerage = brokerage
        self.populate_type_to_path_mapper()

    def get_accounts(self) -> list[Account]:
        request = ListAccountsRequest()
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value)}

        response: ListAccountsResponse = self.get(path=path, base_uri=base_uri, response_model=ListAccountsResponse,
                                                  path_params=path_params, query_params=None)
        return response.account_list

    def get_account(self, account_id: str) -> Account:
        # Generate a #GetAccountRequest object
        # So this is the canonical question - should GetAccountRequest have everything (hermetically-sealed request),
        # or should it be brokerage-agnostic? Brokerage-agnostic b/c we know that every request is done wrt a brokerage,
        # and that's set in the client. Factor it out then.
        request = GetAccountRequest(account_id=account_id)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id}

        response: GetAccountResponse = self.get(path=path, base_uri=base_uri, response_model=GetAccountResponse, path_params=path_params, query_params=None)

        return response.account

    def get_portfolio(self, account_id: str)->Portfolio:
        request = GetPortfolioRequest(account_id=account_id)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id}

        response: GetPortfolioResponse = self.get(path=path, base_uri=base_uri, response_model=GetPortfolioResponse, path_params=path_params, query_params=None)
        return response.portfolio

    def get_account_balance(self, account_id: str):
        request = GetAccountBalanceRequest(account_id=account_id)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id}

        response: GetAccountBalanceResponse = self.get(path=path, base_uri=base_uri, response_model=GetAccountBalanceResponse,
                                                  path_params=path_params, query_params=None)
        return response.account_balance

    def preview_order(self, account_id: str, order: Order, client_order_id: str=None)->PreviewOrderResponse:
        if not client_order_id:
            client_order_id = Client.generate_random_alphanumeric()
        order_metadata: OrderMetadata = OrderMetadata(order_type=order.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PreviewOrderRequest(order_metadata=order_metadata, order=order)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id}

        response: PreviewOrderResponse = self.post(path=path, base_uri=base_uri, request_body=request, response_model=PreviewOrderResponse,
                                                  path_params=path_params)
        return response

    def preview_and_place_order(self, account_id: str, order: Order, client_order_id: str=None)->PlaceOrderResponse:
        if not client_order_id:
            client_order_id = Client.generate_random_alphanumeric()
        order_metadata: OrderMetadata = OrderMetadata(order_type=order.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PreviewPlaceOrderRequest(order_metadata=order_metadata, order=order)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id}

        response: PlaceOrderResponse = self.post(path=path, response_model=PlaceOrderResponse,
                                                 path_params=path_params, query_params=None)
        return response

    def place_order(self, account_id: str, order: Order, preview_id: str, client_order_id: str)->PlaceOrderResponse:
        order_metadata: OrderMetadata = OrderMetadata(order_type=order.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PlaceOrderRequest(order_metadata=order_metadata, order=order, preview_id=preview_id)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id, "preview_id": preview_id}

        response: PlaceOrderResponse = self.post(path=path, base_uri=base_uri, request_body=request, response_model=PlaceOrderResponse,
                                                 path_params=path_params)
        return response

    def modify_order(self, account_id: str, order: Order, order_id_to_modify: str, client_order_id: str=None)->PlaceOrderResponse:
        if not client_order_id:
            client_order_id = Client.generate_random_alphanumeric()

        order_metadata: OrderMetadata = OrderMetadata(order_type=order.get_order_type(),
                                                      account_id=account_id, client_order_id=client_order_id)
        request = PreviewModifyOrderRequest(order_metadata=order_metadata, order=order, order_id_to_modify=order_id_to_modify)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id, "order_id": order_id}

        response: PlaceOrderResponse = self.put(path=path, base_uri=base_uri, request_body=request, response_model=PlaceOrderResponse,
                                                 path_params=path_params)
        return response

    def cancel_order(self, account_id: str, order_id: str):
        request: CancelOrderRequest = CancelOrderRequest(account_id=account_id, order_id=order_id)
        path, base_uri = self.get_path(request)
        path_params = {"brokerage": str(self.brokerage.value), "account_id": account_id, "order_id": order_id}
        response: CancelOrderResponse = self.delete(path=path, base_uri=base_uri, response_model=CancelOrderResponse, path_params=path_params, query_params=None)
        return response

    def get_path(self, request: Request)->(str, str):
        request_type: Type[Request] = type(request)
        if request_type in self.request_type_to_path:
            return self.request_type_to_path[request_type]
        raise Exception(f"Could not identify path for type {request_type}")

    def get(
        self,
        path: str,
        base_uri: str,
        response_model: Type[BaseModel],
        path_params: Optional[dict] = None,
        query_params: Optional[dict] = None,
    ) -> BaseModel:
        url = self._format_path(path, base_uri, path_params)
        if hasattr(self, 'session'):
            response = self.session.get(url, params=query_params, timeout=self.timeout)
        else:
            response = requests.get(url, params=query_params, timeout=self.timeout)
        response.raise_for_status()
        return response_model.model_validate(response.json())

    def delete(
        self,
        path: str,
        base_uri: str,
        response_model: Type[BaseModel],
        path_params: Optional[dict] = None,
        query_params: Optional[dict] = None,
    ) -> BaseModel:
        url = self._format_path(path, base_uri, path_params)
        if hasattr(self, 'session'):
            response = self.session.delete(url, params=query_params, timeout=self.timeout)
        else:
            response = requests.delete(url, params=query_params, timeout=self.timeout)
        response.raise_for_status()
        return response_model.model_validate(response.json())

    def post(
        self,
        path: str,
        base_uri: str,
        request_body: BaseModel,
        response_model: Type[BaseModel],
        path_params: Optional[dict] = None,
    ) -> BaseModel:
        url = self._format_path(path, base_uri, path_params)
        if hasattr(self, 'session'):
            response = self.session.post(
                url, json=request_body.model_dump(), timeout=self.timeout
            )
        else:
            response = requests.post(
                url, json=request_body.model_dump(), timeout=self.timeout
            )
        response.raise_for_status()
        return response_model.model_validate(response.json())

    def put(
        self,
        path: str,
        base_uri: str,
        request_body: BaseModel,
        response_model: Type[BaseModel],
        path_params: Optional[dict] = None,
    ) -> BaseModel:
        url = self._format_path(path, base_uri, path_params)
        if hasattr(self, 'session'):
            response = self.session.put(
                url, json=request_body.model_dump(), timeout=self.timeout
            )
        else:
            response = requests.put(
                url, json=request_body.model_dump(), timeout=self.timeout
            )
        response.raise_for_status()
        return response_model.model_validate(response.json())

    def _format_path(self, path: str, base_uri:str, path_params: Optional[dict]) -> str:
        if path_params:
            path = path.format(**path_params)
        return f"{base_uri}{path}"

    def populate_type_to_path_mapper(self):
        # Ideally we'd do a callout to some service to get the latest & greatest
        # For now it'll just be static.. it might be possible to pull the trace to get the API call
        self.request_type_to_path: dict[Type[Request], (str, str)] = {
            # TODO: Replace each hand-coded URI with a reference. Should be coded in common to be imported into both
            ListAccountsRequest: ("/api/v1/{brokerage}/accounts/", DEFAULT_QUOTES_URL),
            GetAccountRequest: ("/api/v1/{brokerage}/accounts/{account_id}", DEFAULT_QUOTES_URL),
            GetPortfolioRequest : ("/api/v1/{brokerage}/accounts/{account_id}/portfolio", DEFAULT_QUOTES_URL),
            GetAccountBalanceRequest: ("/api/v1/{brokerage}/accounts/{account_id}/balance", DEFAULT_QUOTES_URL),
            # This will change after FIA-93
            GetTradableRequest: ("/api/v1/{brokerage}/quotes/equity/{equity}", DEFAULT_QUOTES_URL),
            GetOptionsChainRequest: ("/api/v1/{brokerage}/quotes/equity/{equity}/options_chain", DEFAULT_QUOTES_URL),
            GetOptionsChainAtExpiryRequest: ("/api/v1/{brokerage}/quotes/equity/{equity}/options_chain/{expiry}", DEFAULT_QUOTES_URL),
            GetOptionExpireDatesRequest: ("/api/v1/{brokerage}/quotes/equity/{equity}/options_chain/expiry", DEFAULT_QUOTES_URL),
            CancelOrderRequest: ("/api/v1/{brokerage}/accounts/{account_id}/orders/{order_id}", DEFAULT_OEX_URL),
            PlaceOrderRequest: ("/api/v1/{brokerage}/accounts/{account_id}/orders/preview/{preview_id}", DEFAULT_OEX_URL),
            PreviewOrderRequest: ("/api/v1/{brokerage}/accounts/{account_id}/orders/preview", DEFAULT_OEX_URL),
            PreviewPlaceOrderRequest: ("/api/v1/{brokerage}/accounts/{account_id}/orders/preview_and_place", DEFAULT_OEX_URL),
            # TODO: Add PlaceModifyOrderRequest once FIA-57 is complete
            PreviewModifyOrderRequest: ("/api/v1/{brokerage}/accounts/{account_id}/orders/{order_id}", DEFAULT_OEX_URL)
        }

    @staticmethod
    def generate_random_alphanumeric(length=15):
        characters = string.ascii_letters + string.digits
        return ''.join(choice(characters) for _ in range(length))

if __name__ == "__main__":
    account_id = '1XRq48Mv_HUiP8xmEZRPnA'
    etrade_client: Client = Client(Brokerage.ETRADE)
    a: Account = etrade_client.get_account(account_id)
    print(a)
    p: Portfolio = etrade_client.get_portfolio(account_id)
    print(p)

    # This can be hidden behind some factory methods, as this is a little overly detailed.
    ol: OrderLine = OrderLine(tradable=Equity(ticker="GE"), action=Action.BUY, quantity=2)
    order_price: OrderPrice = OrderPrice(order_price_type=OrderPriceType.LIMIT, price=Amount(whole=100, part=1))
    o: Order = Order(expiry=GoodUntilCancelled(), order_lines = [ol], order_price=order_price)

    pr_or: PreviewOrderResponse = etrade_client.preview_order(account_id, o)
    print(pr_or)
    preview_id = pr_or.preview_id
    client_id = pr_or.order_metadata.client_order_id

    pl_or: PlaceOrderResponse = etrade_client.place_order(account_id, o, preview_id, client_id)
    print(pl_or)
    order_id = pl_or.order_id
    print(f"Order id: {order_id} placed.")

    o.order_price.price += Amount(whole=0, part=1)
    print(f"About to modify order {order_id}")
    m_or: PlaceOrderResponse = etrade_client.modify_order(account_id, o, order_id)
    new_order_id = m_or.order_id
    print(f"New order: {new_order_id}")

    c: CancelOrderResponse = etrade_client.cancel_order(account_id, new_order_id)
    print(c)
