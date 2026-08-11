# Brokerage Credential Trust Model

TradeBot needs different credential rules for local development, simulator
demos, hosted services, and future third-party client access. The point of this
document is to make those trust boundaries explicit before the implementation
starts mixing them together.

This is a policy and design document. It does not by itself implement AWS
Secrets Manager, client authorization grants, or live-trading permission gates.
Those belong to the follow-up credential-custody tickets.

## Protected Assets

Treat all of these as sensitive:

- Brokerage API keys and API secrets.
- OAuth request tokens, access tokens, token secrets, and serialized sessions.
- Account identifiers, account id keys, portfolio data, balances, positions,
  and order history.
- Live order authority, including preview, place, cancel, and modify access.
- Client authorization grants that say which account and operation classes
  TradeBot may use.
- Local credential files, generated caches, private keys, environment variables,
  and state directories that contain real brokerage material.

Simulator seed accounts and fake OAuth-shaped values are not live credentials,
but they should still look structurally valid so credential-loading paths are
tested realistically.

## Trust Modes

| Mode | Intended Use | Credential Storage | Allowed Brokerage Actions | Operator Access |
| --- | --- | --- | --- | --- |
| Local developer | One developer working on their own machine and account | Ignored local files or local state directory | Whatever the developer explicitly runs | The local developer owns the risk |
| Simulator demo | Docker/local demo with no brokerage access | Checked-in fake OAuth-shaped state plus simulator base URL | Simulator-only read, preview, place, cancel, and lifecycle scenarios | No live credential access |
| Hosted single-operator | Cloud runtime using one operator-owned brokerage account | Managed cloud secret store, not repo or image | Read-only first, preview-only second, live placement only with explicit gates | Operators should not routinely view raw secret values |
| Third-party client | Client grants TradeBot limited access to client brokerage accounts | Per-client managed secrets plus explicit authorization grants | Only operations permitted by the client grant and runtime gates | Raw credentials should be write-only to humans after intake |

Use the smallest mode that proves the thing you need. Simulator success is not
evidence that live OAuth, broker-side validation, or market-hours behavior is
correct.

## Local Developer Mode

Local development can use developer-owned credentials because the trust boundary
is the developer's own laptop and brokerage account. That convenience must not
leak into production assumptions.

Rules:

- Keep real local credentials out of Git.
- Keep generated OAuth/session artifacts out of Git.
- Prefer local paths already covered by `.gitignore`.
- Do not paste real credentials, account ids, tokens, or balances into docs,
  tests, logs, screenshots, PR bodies, or issue comments.
- Local credential files are acceptable only for local development or
  explicitly credentialed manual validation.

Local mode does not prove multi-user credential custody, operator separation,
or production access control.

## Simulator Demo Mode

Simulator mode exists so TradeBot can be demoed as real local services without
live brokerage credentials. It should use fake OAuth-shaped state and point the
E*Trade connector at the simulator endpoint.

Rules:

- Fake simulator credentials may be checked in only when they are clearly not
  live brokerage credentials.
- Fake credentials should still be structurally validated.
- Simulator control routes under `/_simulator` must remain test/demo-only and
  must not be called by production TradeBot services.
- Simulator-backed tests may prove service wiring, serialization, Docker DNS,
  process startup, and representative order lifecycles.
- Simulator-backed tests must not be described as proof that live brokerage
  credentials or live broker behavior are correct.

See `docs/simulator-dogfooding.md` and `docs/etrade-simulator-contract.md` for
the executable simulator workflow.

## Hosted Single-Operator Mode

Hosted single-operator mode is the first cloud step: the service runs in AWS or
another managed environment, but the brokerage account is still owned by the
operator of the system.

Rules:

- Do not bake credentials into Docker images.
- Do not store live credentials in the repository, application database, CI
  logs, or container environment dumps.
- Store credential material in a managed secret store.
- Give the runtime service role only the permissions required to read/decrypt
  the intended secret.
- Keep read-only, preview-only, and live placement authority separated.
- Make live placement/cancel/modify fail closed unless explicitly enabled.
- Log operation names and safe identifiers, not raw credentials or full account
  identifiers.

This mode can support a careful live demo, but it is still weaker than
third-party custody because the system operator owns both the infrastructure and
the brokerage account.

### AWS Secrets Manager Provider

The E*Trade AWS Secrets Manager provider reads and writes the same validated
credential document as local development, but stores it as one JSON
`SecretString` in an existing AWS Secrets Manager secret. The provider does not
create secrets; secret creation, KMS key choice, IAM policy, and rotation policy
belong to the infrastructure custody tickets.

The starter AWS policies live under `deploy/aws/credential-custody/`. They are
templates for one runtime role, one existing secret, and one customer-managed
KMS key. The runtime role policy grants only `DescribeSecret`, `GetSecretValue`,
`PutSecretValue`, and KMS key use through Secrets Manager for that secret.

Expected secret document shape:

```json
{
  "consumer_key": "example-consumer-key",
  "consumer_secret": "example-consumer-secret",
  "access_token": "example-access-token",
  "access_token_secret": "example-access-token-secret",
  "request_token": "example-request-token",
  "request_token_secret": "example-request-token-secret",
  "base_url": "https://api.etrade.com"
}
```

The credential provider treats `ResourceNotFoundException` as absent credential
state. Other AWS, JSON, and validation failures are surfaced without printing
secret values.

## Third-Party Client Mode

Third-party client mode is the long-term trust target. A client grants TradeBot
limited brokerage access, and TradeBot uses that access only through audited
and authorized runtime paths.

Target rules:

- Credential intake should be write-only after submission: operators can create,
  validate, rotate, or revoke credentials, but cannot display raw values.
- Credentials should be stored per client, brokerage, environment, and account
  scope.
- The application database should store metadata and secret references, not raw
  secret values.
- Runtime services should decrypt credentials only when an authorized operation
  requires them.
- Client grants should define allowed brokerage, account scope, operation
  classes, limits, expiration, and revocation state.
- Revoked or expired grants must fail closed.
- Audit records should tie each brokerage action to the client grant and safe
  credential reference that allowed it.

Do not claim full third-party custody until the credential provider, secret
store, IAM/KMS policies, authorization model, rotation/revocation flow, and
audit evidence exist.

## Operation Classes

Credential access is not the same thing as trading authority. Keep these
classes separate in code, configuration, tests, and documentation:

| Class | Examples | Risk |
| --- | --- | --- |
| Read-only | Account list, balances, portfolio, quotes, order status | Can expose sensitive financial data |
| Preview-only | Broker-side order preview/validation without placement | Can expose intent and account constraints |
| Live placement | Place an order with a live broker | Can move money |
| Live cancellation/modification | Cancel or modify an existing live order | Can change trading outcome |
| Simulator action | Simulator reset, lifecycle scenario, fake order flow | Safe only outside production |

Live placement, cancellation, and modification should require explicit runtime
gates and account/operation authorization. They should never be enabled merely
because credentials are present.

The current E*Trade live-write gate is intentionally small and fail-closed:
`ETradeOrderService` blocks placement, cancellation, and modification against
`https://api.etrade.com` unless `TRADEBOT_ALLOW_LIVE_ETRADE_WRITES=true` is set
in the runtime environment. Preview, read-only, and simulator-backed endpoints
do not require this flag.

## Logging And Display Rules

Safe logs should answer what happened without becoming a credential leak.

Allowed:

- Operation name.
- Brokerage name.
- Environment/mode.
- Request or correlation id.
- Secret reference or version id when it is not itself sensitive.
- Stable non-reversible secret fingerprints when the raw secret id could expose
  account, client, environment, or naming details.
- Redacted account reference, such as a stable alias or last-four style hint.
- Result status, failure category, retry count, and upstream service name.

Forbidden:

- API keys, API secrets, OAuth tokens, token secrets, cookies, or signatures.
- Raw credential files or serialized session bodies.
- Full account identifiers or account id keys.
- Raw brokerage request/response bodies unless they have been explicitly
  scrubbed.
- Order payloads that expose live trading intent in ordinary logs.

Error messages should explain the missing or invalid configuration field without
printing the value.

The E*Trade AWS Secrets Manager provider emits standard Python audit log lines
to `fianchetto_tradebot.audit.credentials` for `GetSecretValue` and
`PutSecretValue` calls. Those log lines include provider, operation, outcome,
and a short SHA-256-based secret fingerprint. They do not include raw secret ids
or credential payloads. Unexpected AWS read/write failures are raised as
scrubbed operation-level errors for the same reason.

## Documentation And Demo Checklist

Before any live-account demo, document which trust mode is being used and which
operation classes are enabled.

Minimum checklist:

1. Confirm whether the demo uses simulator, live read-only, live preview-only,
   or live placement.
2. Confirm no live credentials are checked in or baked into the image.
3. Confirm logs and test output do not print secret values or full account
   identifiers.
4. Confirm live placement/cancel/modify paths are disabled unless the demo
   explicitly needs them.
5. Confirm any live placement demo has small quantity/notional limits and a
   documented stop/rollback path.

`FIA-180` owns the fuller production credential security readiness checklist.

## Related Work

- `FIA-171`: introduce the brokerage credential provider interface.
- `FIA-172`: move local E*Trade credentials behind an explicit local provider.
- `FIA-173`: add an AWS Secrets Manager credential provider.
- `FIA-174`: define AWS KMS and IAM policies for credential custody.
- `FIA-175`: add safe audit logging for secret and brokerage access.
- `FIA-176`: add explicit live trading permission gates.
- `FIA-177`: design write-only client credential intake.
- `FIA-178`: define client brokerage authorization and account scope.
- `FIA-179`: add credential rotation and revocation workflow.
- `FIA-180`: add the production credential security readiness checklist.
