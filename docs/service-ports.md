# TradeBot Service Ports

This project uses "port" in two related but separate ways:

- A service port is an internal dependency contract, following Ports and Adapters / Hexagonal Architecture.
- A TCP port is the network port used when a service is deployed as a process.

## Service dependency ports

Managed order execution should depend on small service contracts instead of concrete in-process services. The current ports are:

- `OrderServicePort`: the order operations required by managed execution.
- `QuoteServicePort`: the quote lookup operation required by price-adjustment tactics.

Concrete services such as ETrade order and quote services can satisfy these ports directly. Future local adapters and HTTP adapters should implement the same ports so managed execution can run in either mode:

- Local mode: dependencies are ordinary in-process objects.
- HTTP mode: dependencies are clients that call deployed service processes.

The composition root should choose local or HTTP adapters at startup. Domain and orchestration logic should not branch on deployment mode.

Local mode uses explicit adapter wrappers:

- `LocalOrderServiceAdapter`
- `LocalQuoteServiceAdapter`
- `build_local_service_adapters`

These adapters preserve ordinary in-process debugging while giving deployed HTTP clients a clear interface to implement later.

HTTP mode uses adapter wrappers that receive generic base URLs:

- `HttpOrderServiceAdapter`
- `HttpQuoteServiceAdapter`
- `build_http_service_adapters`
- `orders_base_url`
- `quotes_base_url`

The environment variable names are deployment-neutral:

- `TRADEBOT_ORDERS_SERVICE_URL`
- `TRADEBOT_QUOTES_SERVICE_URL`

Code defaults point at local development ports. Docker Compose and Kubernetes should override those values with the right service DNS names for that environment.

HTTP adapters should construct URLs using the route path values required by the target service. FastAPI handlers do not need to accept every path value when the handler only needs the parsed Pydantic request body.

Run the adapter contract simulation with:

```bash
python -m pytest tests/common/service/test_service_adapter_contracts.py
```

This starts fake in-process FastAPI order and quote services and drives them through the same port methods as local adapters. It is the fastest demo that local and network mode still agree without requiring brokerage credentials.

## TCP port convention

Use the `80xx` range for public FastAPI service processes:

- `8000`: reserved for a future gateway/API facade.
- `8080`: orders service.
- `8081`: quotes/accounts/portfolio service.
- `8082`: managed order execution service.
- `8083`: reserved for a future Trident service.

Prefer stable port assignments over environment-specific reshuffling. Deployment environments can still remap external ports through Docker, Kubernetes Services, or ingress.
