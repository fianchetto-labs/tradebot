# Security Readiness Checkpoint

This checklist defines the current natural stopping point for credential and
live-trading safety. It is intentionally modest: enough structure for local
development, simulator demos, and careful single-operator experiments without
turning TradeBot into a general-purpose permissions platform.

## Current Safe Envelope

TradeBot is ready to claim the following modes when the checklist below passes:

- Local development with developer-owned credentials stored outside Git.
- Docker simulator demos using checked-in fake OAuth-shaped state.
- Hosted single-operator read-only or preview-only runs using managed secrets.
- Carefully controlled single-operator live writes only when an explicit
  live-write gate is enabled for that run.

TradeBot is not yet ready to claim:

- Third-party credential custody.
- Write-only client credential intake.
- Client-scoped authorization grants.
- Credential rotation and revocation workflows.
- Compliance-grade audit evidence or tenant isolation.

Those are real production trust features and should stay in the follow-up
custody tickets rather than being approximated with broad framework code.

## Required Controls

Before a hosted or live-account demo, confirm:

- Real brokerage credentials are not committed, baked into Docker images, or
  printed in CI, logs, test output, screenshots, PRs, or tickets.
- Simulator mode uses fake credential material and points E*Trade traffic at
  the simulator endpoint, not the live broker.
- Hosted credential material lives in a managed secret store such as AWS Secrets
  Manager.
- Runtime IAM can read only the intended secret and KMS key.
- Secret access logs show safe metadata only: provider, operation, outcome, and
  non-reversible fingerprints.
- Live E*Trade place, cancel, and modify calls fail closed unless explicitly
  enabled for the run.
- Any live-write run has a small quantity or notional limit and a human stop
  plan.

## Verification Commands

For ordinary local safety:

```bash
.venv/bin/python -m nox -s unit
.venv/bin/python -m nox -s functional
```

For simulator-backed service wiring:

```bash
TRADEBOT_RUN_SERVICE_TESTS=1 .venv/bin/python -m nox -s docker_integration
```

For manual Docker dogfooding:

```bash
.venv/bin/python -m nox -s docker_up
.venv/bin/python -m nox -s docker_acceptance
.venv/bin/python -m nox -s docker_down
```

Do not use simulator success as evidence that live OAuth, live broker behavior,
or market-hours behavior is correct.

## Live Demo Notes

Pick the smallest live mode that proves the demo:

- Use read-only calls when account discovery, balances, positions, or status
  are enough.
- Use preview-only when brokerage validation is the point.
- Use live placement only when the demo explicitly requires money-moving
  behavior.

For live placement, cancellation, or modification:

- Keep the operation quantity and notional deliberately tiny.
- Confirm the target account manually before enabling writes.
- Keep logs, screenshots, and PR/ticket notes scrubbed of full account ids,
  credential values, and raw order payloads.
- Turn the live-write gate back off after the demo.

## Follow-Up Boundary

The next security tickets should remain focused:

- Write-only credential intake should solve how credentials enter managed
  storage without becoming visible to operators.
- Client authorization should solve who can use which account and operation
  class.
- Rotation and revocation should solve how a credential or client grant stops
  being valid.

Avoid introducing role frameworks, policy engines, tenant models, or generic
permissions abstractions until those tickets have concrete callers.
