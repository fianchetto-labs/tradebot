# Testing

TradeBot uses a test pyramid with explicit commands and explicit safety gates.
Nox is the canonical interface for routine local validation and CI.

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

Reusable scenario harnesses belong under `tests/functional/`. A harness may own
setup for an in-process app, fake connector/session, seeded state, service
adapters, and realistic request fixtures. Test files should use those harnesses
to stay readable and focused on the Given/When/Then behavior being proved.
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

The Docker integration session is reserved for the Docker Compose and reusable
service lifecycle work in FIA-136, FIA-149, and FIA-152:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_integration
```

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
