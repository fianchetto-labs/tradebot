from datetime import date
from enum import Enum

from pydantic import BaseModel

from fianchetto_tradebot.client.client import Client
from fianchetto_tradebot.common_models.api.orders.order_metadata import OrderMetadata
from fianchetto_tradebot.common_models.api.orders.preview_order_request import PreviewOrderRequest
from fianchetto_tradebot.common_models.brokerage.brokerage import Brokerage
from fianchetto_tradebot.common_models.finance.amount import Amount
from fianchetto_tradebot.common_models.finance.currency import Currency
from fianchetto_tradebot.common_models.finance.equity import Equity
from fianchetto_tradebot.common_models.finance.exercise_style import ExerciseStyle
from fianchetto_tradebot.common_models.finance.option import Option
from fianchetto_tradebot.common_models.finance.option_type import OptionType
from fianchetto_tradebot.common_models.managed_executions.list_managed_executions_request import (
    ListManagedExecutionsRequest,
)
from fianchetto_tradebot.common_models.order.action import Action
from fianchetto_tradebot.common_models.order.expiry.good_until_cancelled import GoodUntilCancelled
from fianchetto_tradebot.common_models.order.order import Order
from fianchetto_tradebot.common_models.order.order_line import OrderLine
from fianchetto_tradebot.common_models.order.order_price import OrderPrice
from fianchetto_tradebot.common_models.order.order_price_type import OrderPriceType


class _OkResponse(BaseModel):
    ok: bool


class _Response:
    def raise_for_status(self):
        pass

    def json(self):
        return {"ok": True}


class _RecordingSession:
    def __init__(self):
        self.last_json = None

    def post(self, _url, json, timeout):
        self.last_json = json
        return _Response()

    def put(self, _url, json, timeout):
        self.last_json = json
        return _Response()


def _assert_json_compatible(value):
    if isinstance(value, dict):
        for key, nested_value in value.items():
            assert isinstance(key, str), f"Expected JSON object key to be str, got {type(key)}: {key!r}"
            _assert_json_compatible(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _assert_json_compatible(nested_value)
    else:
        assert value is None or isinstance(value, (str, int, float, bool))
        assert not isinstance(value, (date, Enum, BaseModel))


def _preview_option_order_request() -> PreviewOrderRequest:
    option = Option(
        equity=Equity(ticker="GE"),
        type=OptionType.PUT,
        strike=Amount(whole=10, part=0, currency=Currency.US_DOLLARS),
        expiry=date(2026, 1, 16),
        style=ExerciseStyle.AMERICAN,
    )
    order_line = OrderLine(tradable=option, action=Action.BUY, quantity=1)
    order_price = OrderPrice(
        order_price_type=OrderPriceType.LIMIT,
        price=Amount(whole=1, part=25, currency=Currency.US_DOLLARS),
    )
    order = Order(expiry=GoodUntilCancelled(), order_lines=[order_line], order_price=order_price)
    return PreviewOrderRequest(
        order_metadata=OrderMetadata(
            order_type=order.get_order_type(),
            account_id="abc123",
            client_order_id="client-1",
        ),
        order=order,
    )


def test_list_managed_executions_request_serializes_brokerage_keys_as_strings():
    request = ListManagedExecutionsRequest(accounts={Brokerage.ETRADE: "acct-1"})

    as_dict = request.model_dump()

    assert as_dict == {"accounts": {"etrade": "acct-1"}}
    _assert_json_compatible(as_dict)
    assert ListManagedExecutionsRequest.model_validate(as_dict).accounts == {
        Brokerage.ETRADE: "acct-1"
    }
    assert ListManagedExecutionsRequest.model_validate_json(request.model_dump_json()).accounts == {
        Brokerage.ETRADE: "acct-1"
    }


def test_client_post_serializes_request_body_in_json_mode():
    client = Client(Brokerage.ETRADE)
    client.session = _RecordingSession()

    client.post("", "", _preview_option_order_request(), _OkResponse)

    payload = client.session.last_json
    _assert_json_compatible(payload)
    assert payload["order_metadata"]["order_type"] == "OPTN"
    assert payload["order"]["order_lines"][0]["tradable"]["expiry"] == "2026-01-16"
    assert payload["order"]["order_lines"][0]["tradable"]["type"] == "PUT"
    assert payload["order"]["order_price"]["price"]["currency"] == "USD"


def test_client_put_serializes_request_body_in_json_mode():
    client = Client(Brokerage.ETRADE)
    client.session = _RecordingSession()

    client.put("", "", _preview_option_order_request(), _OkResponse)

    payload = client.session.last_json
    _assert_json_compatible(payload)
    assert payload["order_metadata"]["order_type"] == "OPTN"
    assert payload["order"]["order_lines"][0]["tradable"]["expiry"] == "2026-01-16"
