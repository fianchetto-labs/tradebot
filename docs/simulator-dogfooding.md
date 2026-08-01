# Simulator Dogfooding

Use this runbook from the repository root when you want to run the TradeBot
services as real local Docker processes without live E*Trade credentials.

The simulator-backed stack starts four containers:

| Service | Host URL | What it proves |
| --- | --- | --- |
| E*Trade simulator | `http://127.0.0.1:18090` | Fake brokerage HTTP boundary |
| Orders | `http://127.0.0.1:18080` | Order service process and connector wiring |
| Quotes | `http://127.0.0.1:18081` | Quote service process and connector wiring |
| MOEX | `http://127.0.0.1:18082` | Managed execution service-to-service wiring |

Inside the local Docker stack, services talk through Compose DNS. MOEX calls
`tradebot-orders:8080` and `tradebot-quotes:8081`; orders and quotes call
`tradebot-etrade-simulator:8090`.

## Start The Local Stack

Install the development package once:

```bash
python -m pip install -e ".[dev]"
```

Start the local simulator-backed stack:

```bash
python -m nox -s docker_up
```

This builds `tradebot:local`, starts
`deploy/docker/docker-compose.local.yml`, waits for health checks, and leaves
the containers running until you stop them.

Check the services:

```bash
curl http://127.0.0.1:18090/health-check
curl http://127.0.0.1:18080/health-check
curl http://127.0.0.1:18081/health-check
curl http://127.0.0.1:18082/health-check
```

Try a simulator-backed quote:

```bash
curl http://127.0.0.1:18081/api/v1/ETRADE/quotes/tradable/GE
```

Run the local acceptance checks against the already-running stack:

```bash
python -m nox -s docker_acceptance
```

`docker_acceptance` does not start or stop containers. It expects `docker_up`
to have already started the stack.

## Simulator Scenarios

Control routes live under `/_simulator` on the simulator service. Production
TradeBot services should not call them.

Reset simulator state:

```bash
curl -X POST http://127.0.0.1:18090/_simulator/reset
```

Select an order lifecycle scenario:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"scenario":"eventually-executed"}' \
  http://127.0.0.1:18090/_simulator/order-lifecycle-scenario
```

Supported scenarios:

| Scenario | Behavior |
| --- | --- |
| `open` | Order status reads remain `OPEN`. |
| `eventually-executed` | The first status read is `OPEN`; later reads are `EXECUTED`. |
| `broker-cancelled` | The first status read is `OPEN`; later reads are `CANCELLED`. |
| `rejected` | Status reads return `REJECTED`. |

For full MOEX request examples, use the executable Docker integration tests in
`tests/integration/docker/test_moex_service_stack.py`. Those tests create
managed executions through the MOEX HTTP service, select simulator scenarios,
and assert the resulting managed-execution lifecycle.

For a runnable managed-execution happy path without hand-writing the request
body, run:

```bash
python -m nox -s docker_acceptance
```

That command exercises the already-running local stack through the same HTTP
boundaries used by the Docker integration suite.

## Logs And Cleanup

Show all local stack logs:

```bash
python -m nox -s docker_logs
```

Show one service:

```bash
python -m nox -s docker_logs -- tradebot-moex
```

Stop and remove the local stack:

```bash
python -m nox -s docker_down
```

## Automated Docker Checks

Smoke checks prove container startup and health checks:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_smoke
```

Docker integration checks prove service-to-service behavior across real local
containers:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_integration
```

Local `docker_integration` runs leave the integration containers available for
30 minutes by default. That gives you time to inspect logs or see the stack in
Docker Desktop. CI cleans up immediately.

Clean up integration containers immediately:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 TRADEBOT_INTEGRATION_STACK_TTL_SECONDS=0 python -m nox -s docker_integration
```

Keep them for a different local TTL:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 TRADEBOT_INTEGRATION_STACK_TTL_SECONDS=3600 python -m nox -s docker_integration
```

Remove the integration stack manually:

```bash
docker compose -f deploy/docker/docker-compose.integration.yml down --volumes --remove-orphans
```

## Test Layer Boundaries

Use the safe service-free layers for fast feedback:

```bash
python -m nox -s unit
python -m nox -s functional
```

Use Docker-backed tests when the thing you need to prove involves process
startup, health checks, Docker DNS, port mapping, service-to-service HTTP,
runtime connector base URLs, or serialization over the wire.

Use live paper-account E*Trade tests only for brokerage behavior the simulator
cannot prove:

```bash
TRADEBOT_RUN_LIVE_E2E_TESTS=1 python -m nox -s live_e2e
```

Do not use simulator-backed success as evidence that live brokerage credentials,
E*Trade OAuth, market-hours behavior, or broker-side validation is correct.

## Related Docs

- `docs/testing.md` explains the full test pyramid and Nox sessions.
- `docs/docker-poc.md` explains the Docker image and Compose topology.
- `docs/etrade-simulator-contract.md` describes the simulator API contract and
  seed data.
