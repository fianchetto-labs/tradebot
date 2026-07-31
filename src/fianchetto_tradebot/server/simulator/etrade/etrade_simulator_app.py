from dataclasses import dataclass, field
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fianchetto_tradebot.common_models.order.order_status import OrderStatus
from fianchetto_tradebot.server.common.api.http_status_code import HttpStatusCode
from fianchetto_tradebot.server.simulator.etrade import seed_data

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8090
TERMINAL_ORDER_STATUSES = {
    OrderStatus.CANCELLED.value,
    OrderStatus.EXECUTED.value,
    OrderStatus.EXPIRED.value,
    OrderStatus.REJECTED.value,
}


class OrderLifecycleScenario(str, Enum):
    OPEN = "open"
    EVENTUALLY_EXECUTED = "eventually-executed"
    BROKER_CANCELLED = "broker-cancelled"
    REJECTED = "rejected"


class SimulatorScenarioRequest(BaseModel):
    scenario: str


class SimulatorScenarioResponse(BaseModel):
    scenario: str


@dataclass
class ETradeSimulatorState:
    order_status_by_id: dict[str, str] = field(default_factory=dict)
    order_read_count_by_id: dict[str, int] = field(default_factory=dict)
    order_lifecycle_scenario: OrderLifecycleScenario = OrderLifecycleScenario.OPEN

    def place_order(self) -> str:
        self.order_status_by_id[seed_data.ORDER_ID] = OrderStatus.OPEN.value
        self.order_read_count_by_id[seed_data.ORDER_ID] = 0
        return seed_data.ORDER_ID

    def get_order_status(self, order_id: str) -> str:
        current_status = self.order_status_by_id.get(order_id, OrderStatus.OPEN.value)
        if current_status in TERMINAL_ORDER_STATUSES:
            return current_status

        read_count = self.order_read_count_by_id.get(order_id, 0) + 1
        self.order_read_count_by_id[order_id] = read_count
        next_status = self._scenario_status_for_read(read_count)
        self.order_status_by_id[order_id] = next_status
        return next_status

    def cancel_order(self, order_id: str) -> None:
        if self.order_status_by_id.get(order_id) in TERMINAL_ORDER_STATUSES:
            return
        self.order_status_by_id[order_id] = OrderStatus.CANCELLED.value

    def reset(self) -> None:
        self.order_status_by_id.clear()
        self.order_read_count_by_id.clear()
        self.order_lifecycle_scenario = OrderLifecycleScenario.OPEN

    def set_order_lifecycle_scenario(self, scenario: OrderLifecycleScenario) -> None:
        self.order_lifecycle_scenario = scenario
        self.order_read_count_by_id.clear()

    def _scenario_status_for_read(self, read_count: int) -> str:
        if self.order_lifecycle_scenario == OrderLifecycleScenario.EVENTUALLY_EXECUTED and read_count >= 2:
            return OrderStatus.EXECUTED.value
        if self.order_lifecycle_scenario == OrderLifecycleScenario.BROKER_CANCELLED and read_count >= 2:
            return OrderStatus.CANCELLED.value
        if self.order_lifecycle_scenario == OrderLifecycleScenario.REJECTED:
            return OrderStatus.REJECTED.value
        return OrderStatus.OPEN.value


def create_app(state: ETradeSimulatorState | None = None) -> FastAPI:
    state = state or ETradeSimulatorState()
    app = FastAPI(title="TradeBot E*Trade Simulator")

    @app.get("/")
    def root():
        return "E*Trade Simulator"

    @app.get("/health-check")
    def health_check():
        return "E*Trade Simulator Up"

    @app.post("/_simulator/reset")
    def reset_simulator():
        state.reset()
        return SimulatorScenarioResponse(scenario=state.order_lifecycle_scenario.value)

    @app.post("/_simulator/order-lifecycle-scenario")
    def set_order_lifecycle_scenario(request: SimulatorScenarioRequest):
        scenario = _order_lifecycle_scenario(request.scenario)
        state.set_order_lifecycle_scenario(scenario)
        return SimulatorScenarioResponse(scenario=scenario.value)

    @app.get("/v1/accounts/list.json")
    def list_accounts():
        return seed_data.account_list_response()

    @app.get("/v1/accounts/{account_id}/balance.json")
    def get_account_balance(account_id: str):
        _ensure_demo_account(account_id)
        return seed_data.balance_response(account_id)

    @app.get("/v1/accounts/{account_id}/portfolio.json")
    def get_portfolio(account_id: str):
        _ensure_demo_account(account_id)
        return seed_data.portfolio_response(account_id)

    @app.get("/v1/market/quote/{symbols}.json")
    def get_quote(symbols: str):
        _ensure_supported_symbol(symbols)
        return seed_data.quote_response(symbols, include_greeks=":" in symbols)

    @app.get("/v1/market/optionexpiredate.json")
    def get_option_expire_dates(symbol: str):
        _ensure_supported_symbol(symbol)
        return seed_data.option_expire_date_response()

    @app.get("/v1/market/optionchains.json")
    def get_option_chain(symbol: str, expiryYear: int, expiryMonth: int, expiryDay: int):
        _ensure_supported_symbol(symbol)
        return seed_data.option_chain_response(expiryYear, expiryMonth, expiryDay)

    @app.post("/v1/accounts/{account_id}/orders/preview.json")
    def preview_order(account_id: str, scenario: str | None = None):
        _ensure_demo_account(account_id)
        if scenario == "retryable-preview-error":
            return seed_data.retryable_preview_error_response()
        if scenario is not None:
            raise HTTPException(status_code=HttpStatusCode.BAD_REQUEST, detail=f"Unknown simulator scenario {scenario}")
        return seed_data.preview_order_response()

    @app.post("/v1/accounts/{account_id}/orders/place.json")
    def place_order(account_id: str):
        _ensure_demo_account(account_id)
        order_id = state.place_order()
        return seed_data.place_order_response(order_id)

    @app.get("/v1/accounts/{account_id}/orders/{order_id}.json")
    def get_order(account_id: str, order_id: str):
        _ensure_demo_account(account_id)
        return seed_data.get_order_response(order_id, status=state.get_order_status(order_id))

    @app.put("/v1/accounts/{account_id}/orders/cancel.json")
    def cancel_order(account_id: str):
        _ensure_demo_account(account_id)
        state.cancel_order(seed_data.ORDER_ID)
        return seed_data.cancel_order_response(seed_data.ORDER_ID)

    return app


def _ensure_demo_account(account_id: str) -> None:
    if account_id != seed_data.ACCOUNT_ID:
        raise HTTPException(status_code=HttpStatusCode.NOT_FOUND, detail=f"Unknown simulator account {account_id}")


def _ensure_supported_symbol(symbol: str) -> None:
    if symbol != seed_data.EQUITY_SYMBOL and not symbol.startswith(f"{seed_data.EQUITY_SYMBOL}:"):
        raise HTTPException(status_code=HttpStatusCode.NOT_FOUND, detail=f"Unknown simulator symbol {symbol}")


def _order_lifecycle_scenario(scenario: str) -> OrderLifecycleScenario:
    try:
        return OrderLifecycleScenario(scenario)
    except ValueError as exc:
        supported_scenarios = ", ".join(item.value for item in OrderLifecycleScenario)
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST,
            detail=f"Unknown order lifecycle scenario {scenario}. Supported scenarios: {supported_scenarios}",
        ) from exc


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)
