# Testing

TradeBot uses a test pyramid with explicit commands and explicit safety gates.
Nox is the canonical interface for routine local validation and CI.

For how these test layers map to local in-process, local Docker, automated
Docker integration, and future Kubernetes deployment modes, see
`docs/deployment.md`.

Raw `python -m pytest` can still be useful as a tight local debugging escape
hatch, but shared project workflows should use Nox so local and CI behavior
stay aligned.

## Test Layers

| Layer | Purpose | Default |
| --- | --- | --- |
| Unit | Tiny, isolated tests for one class, function, or module boundary | Safe |
| Functional | In-process tests that exercise multiple classes or components | Safe |
| Contract | Shared behavior tests for alternate implementations of the same port | Safe when service-free |
| Docker smoke | Real container startup and health checks | Opt-in |
| Docker integration | Service-to-service checks across real local processes or containers | Opt-in |
| Live E2E | Paper-account E*Trade checks using real credentials | Opt-in, never default |

Push tests as low in the pyramid as they can honestly go. Use Docker-backed
tests for process, networking, readiness, or serialization boundaries. Use live
paper-account tests only for risks that cannot be proven with fakes, simulators,
or local containers.

## Unit vs Functional

Unit tests verify one class, function, value object, parser branch, or module
boundary at a time. They should be fast, deterministic, and narrow. Unit tests
should not need Docker, a running service, live credentials, real network I/O,
or a broad application workflow to explain why they exist.

Functional tests verify an in-process slice of product behavior across multiple
project components. They may use realistic fixtures, fakes, in-process FastAPI
clients, service adapters, parsers, tactics, and domain objects together. They
can prove wiring, request/response translation, parser-to-domain behavior,
adapter equivalence, or a representative trading workflow that would be too
thinly tested by isolated unit tests.

Functional tests should be scenario-oriented. A good functional test starts
from a recognizable product behavior, arranges the relevant in-process
collaborators, runs the behavior through the public boundary for that slice,
and asserts the domain result. It should not exist merely because a unit test
grew large.

Reusable fixtures, fakes, contract sessions, and scenario harnesses belong under
`tests/fixtures/` or another established test-infrastructure package. A harness
may own setup for an in-process app, fake connector/session, seeded state,
service adapters, and realistic request fixtures. Test files should use those
harnesses to stay readable and focused on the Given/When/Then behavior being
proved.
When the scenario crosses an adapter boundary, prefer an explicit in-process
connector or adapter over anonymous mocks so the boundary remains visible.

Functional tests are not Docker tests, live brokerage tests, browser tests, or
generic slow unit tests. If a test needs a real process, container network,
external service, or paper-account credential, mark it with the appropriate
`service`, `docker`, `integration`, or `live_e2e` marker instead.

## Commands

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the safe default suite:

```bash
python -m nox -s unit
```

Run the in-process functional suite:

```bash
python -m nox -s functional
```

This selects only tests explicitly marked `functional`. It does not also run the
unit suite.

Run focused pytest commands through Nox:

```bash
python -m nox -s test -- tests/common/test_chain.py
```

Build the local Docker image after the Docker POC is present:

```bash
python -m nox -s docker_build
```

Start the local simulator-backed Docker stack for manual dogfooding:

```bash
python -m nox -s docker_up
```

This builds `tradebot:local`, starts the E*Trade simulator, orders, quotes, and
MOEX services through `deploy/docker/docker-compose.local.yml`, waits for
health checks, and leaves the containers running. The local stack uses stable
Compose service names:

| Service | Internal name | Host URL |
| --- | --- | --- |
| E*Trade simulator | `tradebot-etrade-simulator` | `http://127.0.0.1:18090` |
| Orders | `tradebot-orders` | `http://127.0.0.1:18080` |
| Quotes | `tradebot-quotes` | `http://127.0.0.1:18081` |
| MOEX | `tradebot-moex` | `http://127.0.0.1:18082` |

Run acceptance checks against the already-running local stack:

```bash
python -m nox -s docker_acceptance
```

This reuses the Docker integration tests as an explicit local acceptance pass.
It does not start or stop containers; run `docker_up` first.
For a step-by-step local runbook, see `docs/simulator-dogfooding.md`.

Inspect logs:

```bash
python -m nox -s docker_logs
python -m nox -s docker_logs -- tradebot-moex
```

Stop the local stack:

```bash
python -m nox -s docker_down
```

Run Docker-backed service smoke checks intentionally:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_smoke
```

This starts the orders, quotes, and MOEX smoke containers after building the
local image. After their health checks pass, the containers remain available
for 30 minutes so you can inspect them in Docker Desktop, curl their health
checks, or review logs. The smoke harness schedules automatic cleanup at the
end of that window and also removes any previous smoke containers before
starting a fresh run.

The smoke containers bind only to localhost:

```bash
curl http://127.0.0.1:18080/health-check
curl http://127.0.0.1:18081/health-check
curl http://127.0.0.1:18082/health-check
```

To clean them up early:

```bash
docker rm -f tradebot-nox-smoke-orders tradebot-nox-smoke-quotes tradebot-nox-smoke-moex
```

Smoke tests are startup probes. They prove a service process can boot from the
Docker image and answer its health check, but they do not prove service-to-service
behavior or a user workflow.

Run the simulator-backed Docker integration slice intentionally:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_integration
```

This builds the local image, starts the Compose stack, waits for health checks,
runs Docker integration tests, and leaves the stack available for 30 minutes on
local machines. The current slices verify host pytest -> TradeBot service
container -> E*Trade simulator container -> TradeBot service container -> host
assertion for quotes and orders. They also verify MOEX -> orders/quotes over
Docker DNS for a representative managed-execution lifecycle. That catches
broken Docker DNS, port mapping, service startup ordering, connector base URL
configuration, request/response serialization, and order lifecycle behavior
across a real HTTP/process boundary.

Integration cleanup is intentionally automatic. Local runs schedule cleanup by
run-specific Docker labels so an old cleanup task does not remove a newer run.
Each integration run removes any previous integration stack before starting a
fresh one. CI always tears the stack down immediately. To make a local run clean
up immediately, set:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 TRADEBOT_INTEGRATION_STACK_TTL_SECONDS=0 python -m nox -s docker_integration
```

To clean the integration stack up early:

```bash
docker compose -f deploy/docker/docker-compose.integration.yml down --volumes --remove-orphans
```

Use `docker_integration` for an automated test-owned stack with TTL cleanup.
Use `docker_up` / `docker_down` when you want a stable local runtime to inspect
manually.
The manual simulator-backed workflow is documented in
`docs/simulator-dogfooding.md`.

The live paper-account E*Trade session is reserved for FIA-153 and must remain
separately gated:

```bash
TRADEBOT_RUN_LIVE_E2E_TESTS=1 python -m nox -s live_e2e
```

## Safety Gates

Tests marked `service`, `docker`, or `integration` must not run as part of the
ordinary unit workflow. Service/container tests require:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1
```

Live E*Trade paper-account tests require a separate gate:

```bash
TRADEBOT_RUN_LIVE_E2E_TESTS=1
```

Do not commit brokerage credentials, access tokens, private keys, account
identifiers, or generated credential files. Test failures should report which
configuration is missing without printing secret values.

For the credential trust modes behind these gates, see
`docs/credential-trust-model.md`.
