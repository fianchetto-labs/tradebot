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

## TCP port convention

Use the `80xx` range for public FastAPI service processes:

- `8000`: reserved for a future gateway/API facade.
- `8080`: orders service.
- `8081`: quotes/accounts/portfolio service.
- `8082`: managed order execution service.
- `8083`: reserved for a future Trident service.

Prefer stable port assignments over environment-specific reshuffling. Deployment environments can still remap external ports through Docker, Kubernetes Services, or ingress.
