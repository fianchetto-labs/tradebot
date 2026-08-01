# Docker POC

FIA-133 introduces one reusable image for local container startup checks. The
image can run each current REST service by selecting the Python module at
container start.

The Compose-backed integration slices start the E*Trade simulator plus the
quotes, orders, and MOEX services. TradeBot services reach the simulator and
each other through Docker service DNS, so this proves more than container
startup: it proves endpoint configuration, service networking, and
representative TradeBot HTTP routes.

## Build

Build from the repository root:

```bash
docker build -t tradebot:local .
```

The image defaults to Python 3.14. To test a different image tag temporarily:

```bash
docker build --build-arg PYTHON_VERSION=3.14 -t tradebot:local .
```

## Demo State

The REST services currently establish brokerage connectors during service
construction, before `/health-check` can respond. For credentials-free local
container startup, point the service at the checked-in demo state directory:

```bash
FIANCHETTO_TRADEBOT_STATE_DIR=/app/deploy/docker/demo-state
```

The demo state contains fake OAuth-shaped E*Trade values. They are intentionally
not live brokerage credentials. The simulator-backed Compose files override the
API endpoint with service DNS. The automated integration stack uses:

```bash
TRADEBOT_ETRADE_API_BASE_URL=http://etrade-simulator:8090
```

The local dogfooding stack uses:

```bash
TRADEBOT_ETRADE_API_BASE_URL=http://tradebot-etrade-simulator:8090
```

It also sets a long cache max age for that fake credential document:

```bash
TRADEBOT_ETRADE_CACHE_MAX_AGE_SECONDS=315360000
```

The default cache max age remains one hour for normal connector use. The longer
value is for checked-in simulator credentials only; the credential fields are
still validated before the service starts.

## Run One Service

Orders service:

```bash
docker run --rm \
  -e FIANCHETTO_TRADEBOT_STATE_DIR=/app/deploy/docker/demo-state \
  -e TRADEBOT_HEALTHCHECK_PORT=8080 \
  -p 8080:8080 \
  tradebot:local \
  python -m fianchetto_tradebot.server.orders.serving.orders_rest_service
```

Quotes service:

```bash
docker run --rm \
  -e FIANCHETTO_TRADEBOT_STATE_DIR=/app/deploy/docker/demo-state \
  -e TRADEBOT_HEALTHCHECK_PORT=8081 \
  -p 8081:8081 \
  tradebot:local \
  python -m fianchetto_tradebot.server.quotes.serving.quotes_rest_service
```

MOEX service:

```bash
docker run --rm \
  -e FIANCHETTO_TRADEBOT_STATE_DIR=/app/deploy/docker/demo-state \
  -e TRADEBOT_HEALTHCHECK_PORT=8082 \
  -p 8082:8082 \
  tradebot:local \
  python -m fianchetto_tradebot.server.moex.serving.moex_rest_service
```

The standalone MOEX command uses in-process orders and quotes adapters. The
Compose-backed integration stack sets `TRADEBOT_MOEX_SERVICE_ADAPTER_MODE=http`
plus `TRADEBOT_ORDERS_SERVICE_URL` and `TRADEBOT_QUOTES_SERVICE_URL` so MOEX
talks to the orders and quotes containers over Docker DNS.

Then verify health from the host:

```bash
curl http://127.0.0.1:8080/health-check
```

Change the port to match the service under test.

## Run The Local Simulator-Backed Stack

Use Nox for the local development stack:

```bash
python -m nox -s docker_up
```

That command builds `tradebot:local`, starts the Compose stack in
`deploy/docker/docker-compose.local.yml`, waits for service health, and leaves
the containers running until you stop them. This is the normal dogfooding loop
for local distributed-mode development.
For a short command-first runbook, see `docs/simulator-dogfooding.md`.

The local Compose stack uses stable service names that mirror the future
deployment topology:

| Service | Internal name | Host port |
| --- | --- | --- |
| E*Trade simulator | `tradebot-etrade-simulator` | `18090` |
| Orders | `tradebot-orders` | `18080` |
| Quotes | `tradebot-quotes` | `18081` |
| MOEX | `tradebot-moex` | `18082` |

MOEX talks to orders and quotes through Docker DNS:

```bash
TRADEBOT_ORDERS_SERVICE_URL=http://tradebot-orders:8080
TRADEBOT_QUOTES_SERVICE_URL=http://tradebot-quotes:8081
```

Run the local acceptance checks after the stack is up:

```bash
python -m nox -s docker_acceptance
```

To inspect the stack manually:

```bash
curl http://127.0.0.1:18090/health-check
curl http://127.0.0.1:18080/health-check
curl http://127.0.0.1:18081/api/v1/ETRADE/quotes/tradable/GE
curl http://127.0.0.1:18082/health-check
```

Inspect logs:

```bash
python -m nox -s docker_logs
python -m nox -s docker_logs -- tradebot-moex
```

Stop the stack:

```bash
python -m nox -s docker_down
```

Use the automated Docker integration session when you want a test-owned stack
with cleanup behavior:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_integration
```

That command uses `deploy/docker/docker-compose.integration.yml`, runs the
Docker integration tests, and cleans up according to
`TRADEBOT_INTEGRATION_STACK_TTL_SECONDS`.
