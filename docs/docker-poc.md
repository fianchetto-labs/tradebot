# Docker POC

FIA-133 introduces one reusable image for local container startup checks. The
image can run each current REST service by selecting the Python module at
container start.

The first Compose-backed integration slice starts the E*Trade simulator and the
quotes service together. The quotes service reaches the simulator through Docker
service DNS, so this proves more than container startup: it proves endpoint
configuration, service networking, and a representative TradeBot HTTP route.

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
not live brokerage credentials. The simulator-backed Compose profile overrides
the API endpoint with service DNS:

```bash
TRADEBOT_ETRADE_API_BASE_URL=http://etrade-simulator:8090
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

Then verify health from the host:

```bash
curl http://127.0.0.1:8080/health-check
```

Change the port to match the service under test.

## Run The Simulator-Backed Stack

Use Nox for the automated Docker integration run:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_integration
```

That command builds `tradebot:local`, starts the Compose stack in
`deploy/docker/docker-compose.integration.yml`, waits for service health, runs
the Docker integration tests, and tears the stack down.

To inspect the stack manually:

```bash
docker build --build-arg PYTHON_VERSION=3.14 -t tradebot:local .
docker compose -f deploy/docker/docker-compose.integration.yml up --detach --wait
curl http://127.0.0.1:18090/health-check
curl http://127.0.0.1:18081/api/v1/ETRADE/quotes/tradable/GE
docker compose -f deploy/docker/docker-compose.integration.yml down --volumes
```
