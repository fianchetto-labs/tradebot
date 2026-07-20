# Docker POC

FIA-133 introduces one reusable image for local container startup checks. The
image can run each current REST service by selecting the Python module at
container start.

This is not the full Docker Compose topology. Compose networking, service DNS,
and simulator-backed service-to-service checks belong to FIA-136, FIA-148, and
FIA-149.

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
not live brokerage credentials. A later simulator-backed Compose profile should
override the API endpoint with service DNS, for example:

```bash
TRADEBOT_ETRADE_API_BASE_URL=http://etrade-sim:8090
```

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
