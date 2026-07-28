# TradeBot Brokerage Setup

Most contributors do not need this guide on day one. Use it only when your
ticket explicitly needs real or sandbox brokerage credentials.

For ordinary documentation, model, serialization, service-adapter, simulator,
and unit-test work, stay credentials-free and use the normal local setup:

- [New Contributor Quickstart](../docs/new-contributor-quickstart.md)
- [Local development setup](set_up_local_env.MD)
- [Testing guide](../docs/testing.md)
- [E*Trade simulator contract](../docs/etrade-simulator-contract.md)

## Supported Brokerages

Brokerage support is evolving and is not uniform across integrations.

| Brokerage | Status | Credentialed validation |
| --- | --- | --- |
| E*Trade | Primary current integration | Sandbox/live OAuth credentials |
| Schwab | In development | Do not assume full workflow support |
| Interactive Brokers (IBKR) | Planned | Paper trading support is roadmap work |

Use simulator-backed tests for process, networking, and serialization checks
whenever possible. Use sandbox or live brokerage validation only for risks that
cannot be proven with unit tests, fakes, or the simulator.

## Safety Rules

- Never commit `config.ini`, credential caches, tokens, private keys, account
  identifiers, screenshots containing account data, or generated credential
  files.
- Prefer sandbox or paper accounts for validation.
- Keep live order-placement work out of ordinary local test runs.
- Use the explicit test gates documented in [Testing](../docs/testing.md).
- If a command would place, cancel, or modify a real order, stop and confirm the
  intended account, environment, and ticket scope first.

## E*Trade Config

The E*Trade connector reads configuration from:

```text
src/fianchetto_tradebot/server/common/brokerage/etrade/config.ini
```

Create it from the example:

```bash
cd src/fianchetto_tradebot/server/common/brokerage/etrade
cp config.example.ini config.ini
```

Then fill in the sandbox and/or production values provided by E*Trade:

```ini
[DEFAULT]
SANDBOX_BASE_URL=https://apisb.etrade.com
PROD_BASE_URL=https://api.etrade.com

[SANDBOX]
SANDBOX_API_KEY=<SANDBOX_API_KEY>
SANDBOX_API_SECRET=<SANDBOX_API_SECRET_KEY>

[PROD]
PROD_API_KEY=<PROD_API_KEY>
PROD_API_SECRET=<PROD_API_SECRET>
```

`config.ini` files are ignored by Git. Keep them local.

## Credential Cache

After OAuth succeeds, E*Trade connection state is cached under:

```text
~/.fianchetto_tradebot/etrade/
```

The current credential cache stores OAuth-shaped values plus a `base_url`.
Simulator-backed deployments can use fake but well-formed credential values;
live brokerage validation must use real credentials.

The E*Trade base URL precedence is:

1. `TRADEBOT_ETRADE_API_BASE_URL`
2. `base_url` in the credential cache
3. legacy standalone `base_url.json`
4. interactive OAuth establishment

See [E*Trade simulator contract](../docs/etrade-simulator-contract.md) for the
simulator-backed credential shape and fake-value conventions.

## Manual E*Trade OAuth

When the E*Trade connector cannot load a valid cached connection, it starts an
interactive OAuth flow. At the prompt, choose sandbox unless your ticket
explicitly requires live validation:

```text
1) Sandbox Consumer Key
2) Live Consumer Key
3) Exit
Please select Consumer Key Type: 1
```

The connector opens a browser, asks you to authorize the app, and prompts for
the verification code.

## First Validation

For a new contributor, the first validation should still be credentials-free:

```bash
python -m nox -s unit
```

If your ticket needs a credentialed E*Trade check, define the smallest safe
manual validation with Aleks before running it. Prefer read-only account or
quote calls before any order workflow.
