# Testing

TradeBot uses a test pyramid with explicit commands and explicit safety gates.
Nox is the canonical interface for routine local validation and CI.

Raw `python -m pytest` is still useful for tight local debugging, but shared
project workflows should use Nox so local and CI behavior stay aligned.

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

## Commands

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the safe default suite:

```bash
python -m nox -s unit
```

Run the current in-process functional suite:

```bash
python -m nox -s functional
```

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
