# Deployment Modes

TradeBot currently supports three practical local execution modes and has a
planned Kubernetes direction. Pick the smallest mode that proves the behavior
you care about.

## Local In-Process Debugging

Use local Python and in-process adapters when you are changing domain behavior,
request models, parsers, tactics, or service logic and do not need separate
processes.

Typical commands:

```bash
python -m nox -s unit
python -m nox -s functional
python -m nox -s test -- tests/common/test_chain.py
```

This mode is fast and easy to debug. It does not prove container startup,
Docker DNS, port mapping, or service-to-service HTTP wiring.

## Local Docker/Compose Simulator Mode

Use the simulator-backed Compose stack when you want a demoable local runtime
without live brokerage credentials.

```bash
python -m nox -s docker_up
python -m nox -s docker_acceptance
python -m nox -s docker_down
```

This starts the E*Trade simulator plus orders, quotes, and MOEX as local
containers. Services talk through Compose DNS, and host traffic reaches them on
localhost ports. This is the best mode for manual dogfooding and local demos.

Health checks are exposed on localhost:

```bash
curl http://127.0.0.1:18090/health-check
curl http://127.0.0.1:18080/health-check
curl http://127.0.0.1:18081/health-check
curl http://127.0.0.1:18082/health-check
```

## Automated Docker Integration

Use the Docker integration session when you want tests to own stack startup,
verification, logs, and cleanup.

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_integration
```

This mode starts a test-owned Compose stack, runs Docker integration tests, and
uses TTL cleanup for local inspection. It proves service startup,
service-to-service HTTP, Docker DNS, connector base URLs, serialization over the
wire, and representative managed-execution behavior.

Use Docker smoke checks when you only need startup and health-check confidence:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 python -m nox -s docker_smoke
```

## Configuration And Secrets

The simulator-backed Docker modes use checked-in fake OAuth-shaped state under
`deploy/docker/demo-state`. Those values are intentionally not live brokerage
credentials, but they still exercise the normal credential-loading path.

Live brokerage credentials should stay out of Git. Do not commit OAuth tokens,
account identifiers, generated credential caches, private keys, or local state
directories containing real account data.

For the broader credential trust model across local development, simulator
demos, hosted services, and future third-party client access, see
`docs/credential-trust-model.md`.

Important runtime configuration:

| Variable | Purpose |
| --- | --- |
| `FIANCHETTO_TRADEBOT_STATE_DIR` | Points a service at its credential/state directory. |
| `TRADEBOT_ETRADE_API_BASE_URL` | Overrides the E*Trade-compatible API endpoint, commonly to the simulator service in Docker. |
| `TRADEBOT_ALLOW_LIVE_ETRADE_WRITES` | Must be `true` before live E*Trade place/cancel/modify calls are allowed against `https://api.etrade.com`. |
| `TRADEBOT_MOEX_SERVICE_ADAPTER_MODE` | Selects local vs HTTP-backed MOEX dependencies. |
| `TRADEBOT_ORDERS_SERVICE_URL` | Tells MOEX where the orders service lives in HTTP mode. |
| `TRADEBOT_QUOTES_SERVICE_URL` | Tells MOEX where the quotes service lives in HTTP mode. |

Hosted AWS deployments can use
`ETradeAwsSecretsManagerCredentialProvider` to load a validated E*Trade
credential document from an existing AWS Secrets Manager secret. The service
role should be limited to the intended secret and the required read/write
operations; KMS/IAM policy details are tracked separately from local Docker
configuration. Starter policy templates live in
`deploy/aws/credential-custody/`.

`TRADEBOT_MOEX_SERVICE_ADAPTER_MODE` defaults to `local` for simple developer
startup. When it is set to `http`, both `TRADEBOT_ORDERS_SERVICE_URL` and
`TRADEBOT_QUOTES_SERVICE_URL` must be set explicitly so containerized startup
does not silently point at localhost.

## Troubleshooting

- If a Nox Docker command skips, confirm `TRADEBOT_RUN_SERVICE_TESTS=1` is set
  for service, Docker, or integration sessions.
- If a service cannot reach another service from inside Docker, check the
  Compose service URL, not the host `127.0.0.1` URL.
- If health checks fail, inspect logs with `python -m nox -s docker_logs` or
  `python -m nox -s docker_logs -- tradebot-moex`.
- If ports are already in use, stop stale local containers with
  `python -m nox -s docker_down` and remove stale integration stacks with
  `docker compose -f deploy/docker/docker-compose.integration.yml down --volumes --remove-orphans`.
- If a service starts locally but fails in Docker, compare the state directory,
  base URL override, adapter mode, and service URL environment variables.

## Future Kubernetes Mode

Kubernetes is not implemented yet in this repository. The current Docker and
Compose work is intentionally shaping the service boundaries that Kubernetes
will need later: one process per service, explicit ports, health checks,
container-friendly configuration, and service-to-service URLs.

When Kubernetes support lands, it should reuse those same boundaries rather
than introduce a separate service model.

## Related Docs

- `docs/testing.md` lists the test pyramid and Nox commands.
- `docs/docker-poc.md` explains the Docker image and Compose topology.
- `docs/simulator-dogfooding.md` is the command-first local demo runbook.
- `docs/credential-trust-model.md` defines credential trust modes and live
  brokerage safety expectations.
