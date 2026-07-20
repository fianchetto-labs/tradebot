# E*Trade Simulator Contract

The E*Trade simulator is a non-production service for deployment demos and smoke
tests. It should let TradeBot services run as real HTTP processes without live
brokerage credentials.

The simulator is not a broker-accuracy certification suite. It should return
deterministic, plausible responses for the subset of E*Trade behavior that
TradeBot needs in local Docker and future Kubernetes demos.

## Goals

- Prove service startup, HTTP routing, serialization, and container networking.
- Exercise the real TradeBot E*Trade service/parsing paths where practical.
- Provide stable seed accounts, quotes, option chains, portfolio positions, and
  order lifecycle data.
- Keep live brokerage validation separate from simulator-backed deployment
  validation.

## Initial Seed Data

- Account id key: `acct-key-1`
- Display account id: `acct-1`
- Equity: `GE`
- Option: `GE 2026-01-16 PUT 25.00`
- Preview id: `preview-1`
- Placed order id: `order-1`
- Response timestamp: `2026-01-02T13:30:00Z`

## Initial Endpoint Surface

The first simulator should support these E*Trade-like routes:

| Method | Path | Scenario |
| --- | --- | --- |
| `GET` | `/v1/accounts/list.json` | List the deterministic demo account. |
| `GET` | `/v1/accounts/{account_id}/balance.json` | Return a plausible margin balance. |
| `GET` | `/v1/accounts/{account_id}/portfolio.json` | Return one GE equity position and one GE option position. |
| `GET` | `/v1/market/quote/{symbols}.json` | Return equity and option quotes. |
| `GET` | `/v1/market/optionexpiredate.json` | Return deterministic option expiries for GE. |
| `GET` | `/v1/market/optionchains.json` | Return a small call/put option chain for a requested expiry. |
| `POST` | `/v1/accounts/{account_id}/orders/preview.json` | Return preview id `preview-1`. |
| `POST` | `/v1/accounts/{account_id}/orders/place.json` | Return placed order id `order-1`. |
| `GET` | `/v1/accounts/{account_id}/orders/{order_id}.json` | Return an open placed order. |
| `PUT` | `/v1/accounts/{account_id}/orders/cancel.json` | Return a successful cancellation. |

## Failure Path

The initial representative failure should be an order preview response with an
`Error` body. The first seed failure should use the existing E*Trade parser
behavior for a retry-suggested response, such as an insufficient-shares message.

The FastAPI simulator exposes that failure with:

```bash
curl -X POST \
  "http://127.0.0.1:8090/v1/accounts/acct-key-1/orders/preview.json?scenario=retryable-preview-error"
```

## State

The first implementation can keep order state in memory and reset it on process
restart. That is enough for deployment demos and smoke tests. Persistent
simulator state is out of scope until a test needs it.

## Running The Simulator

Start the simulator locally with:

```bash
python -m fianchetto_tradebot.server.simulator.etrade
```

By default it binds to `0.0.0.0:8090`. Override that with:

```bash
TRADEBOT_ETRADE_SIMULATOR_HOST=127.0.0.1 \
TRADEBOT_ETRADE_SIMULATOR_PORT=8090 \
python -m fianchetto_tradebot.server.simulator.etrade
```

This is a real FastAPI/uvicorn process, but it is still not part of the default
unit test suite. Docker Compose wiring and real-process smoke tests are tracked
separately.

## TradeBot Connector Configuration

TradeBot E*Trade services should keep production behavior unchanged by default:
they load OAuth credentials and use the E*Trade base URL stored with those
credentials.

Simulator-backed deployments should supply fake E*Trade credentials and point
the connector at the simulator endpoint. For example, the credential cache can
contain non-secret placeholder values:

```json
{
  "consumer_key": "simulator-consumer-key",
  "consumer_secret": "simulator-consumer-secret",
  "access_token": "simulator-access-token",
  "access_token_secret": "simulator-access-token-secret",
  "request_token": "simulator-request-token",
  "request_token_secret": "simulator-request-token-secret",
  "base_url": "http://etrade-sim:8090"
}
```

This preserves the normal OAuth-shaped connector/session path while avoiding
live brokerage credentials. The simulator ignores the fake signature material,
but the credential document is still validated: required OAuth fields must be
present and non-empty, request-token fields must be present and either non-empty
or `null`, and `base_url` must be an `http` or `https` URL.

`TRADEBOT_ETRADE_API_BASE_URL` can override the cached E*Trade-compatible HTTP
endpoint at runtime:

```bash
TRADEBOT_ETRADE_API_BASE_URL=http://etrade-sim:8090
```

Use a Docker/Kubernetes service name such as `http://etrade-sim:8090` inside a
service network, or `http://127.0.0.1:8090` for local process testing.

Base URL precedence is explicit:

1. `TRADEBOT_ETRADE_API_BASE_URL`
2. `base_url` in the credential cache
3. legacy standalone `base_url.json`
4. interactive OAuth establishment

## Validation Layers

- Unit/parser tests prove the simulator-shaped payloads still parse into domain
  models.
- Adapter contract tests prove local and HTTP TradeBot adapters preserve the
  same behavior.
- Simulator-backed smoke tests prove real processes, Docker networking, service
  DNS, and startup ordering.
- Live brokerage tests remain separate and credential-gated.

Run the executable seed contract with:

```bash
python -m pytest tests/common/api/etrade_simulator/test_etrade_simulator_contract.py
```

## Service Test Safety

Simulator contract tests that use in-memory fake sessions can run in the
standard unit test suite. Tests that require a live simulator, TradeBot service
process, Docker container, or Docker Compose stack must opt into the service-test
guard.

Mark those tests explicitly:

```python
import pytest


@pytest.mark.service
@pytest.mark.docker
def test_simulator_backed_stack_smoke():
    ...
```

The default test command remains safe:

```bash
python -m pytest
```

Tests marked `service` or `docker` are skipped unless the caller deliberately
sets:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1
```

Run Docker-backed service tests intentionally with:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 docker compose up -d
TRADEBOT_RUN_SERVICE_TESTS=1 python -m pytest -m docker tests
```

This keeps simple unit-test invocations credentials-free and service-free while
still making the real-process deployment checks easy to run on purpose.
