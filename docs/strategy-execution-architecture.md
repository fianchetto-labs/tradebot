# Strategy and Execution Architecture

## Purpose

TradeBot will support proprietary trading logic without turning strategy code
into an unbounded broker client. This document defines the first, deliberately
small architecture for that work. It is a design and package-boundary document;
it does not change live-trading behavior by itself.

The initial supported shape is one active strategy instance per brokerage
account. That is a conscious constraint while TradeBot develops durable intent,
safe revocation, and risk controls. Multi-strategy coordination within one
account is deferred rather than hidden behind incomplete locking behavior.

## Terms

| Term | Responsibility |
| --- | --- |
| Strategy | Long-running portfolio intent: why to trade, what outcome is wanted, and when to create, revise, or withdraw an objective. |
| Trade objective | A durable, higher-order request such as "roll this covered call" with economic constraints and execution guidance. It does not name a tactic or call a broker. |
| Execution plan | The current, broker-actionable plan derived from an objective and fresh brokerage, portfolio, and market state. |
| Managed execution | A time-bounded, broker-facing job that completes one atomic order objective within the plan's limits. |
| Execution policy | The platform-owned choice of how to execute a valid plan, including selection of a tactic. |
| Tactic | An order-scoped method, such as incremental repricing or cautious legging, that proposes the next action within an already-authorized plan. |
| Risk-control policy | A platform-owned guard that can reject a plan, reserve risk capacity, or authorize a narrowly defined break-glass action. |

## Ownership Boundaries

| Component | May do | Must not do |
| --- | --- | --- |
| Strategy | Emit, revise, supersede, or withdraw trade objectives; provide economic constraints and execution guidance; explain its decision. | Call brokerage connectors, choose raw repricing mechanics, or mutate a live order. |
| Objective controller | Reconcile the newest objective with fresh observed state; construct a plan; coordinate supersession. | Invent portfolio intent or bypass risk policy. |
| Managed execution | Preview, submit, poll, cancel, replace, and record one broker order objective. | Change strike, expiry, quantity, account, objective deadline, or economic constraints. |
| Execution policy and tactic | Choose and apply safe mechanics within the plan, such as price progression and poll timing. | Change the requested trade or call the brokerage outside managed execution. |
| Risk-control policy | Enforce account and strategy limits; authorize exceptional behavior under named rules. | Infer a strategy's investment thesis. |

## Covered-Call Roll Example

A strategy can express this objective:

> Roll the current covered call for at least the specified net credit, using a
> selected expiry and delta range. Prefer price improvement, do not use a market
> order when quotes are degenerate, and keep the objective valid for its stated
> window.

The objective controller turns that into a current multi-leg order plan. The
execution policy selects the default price-adjustment tactic. Managed execution
then owns the broker-facing work: it submits the order, observes it, and may
replace it at a new permitted price. A cancellation of a replaced brokerage
order does not by itself cancel the managed execution.

## Objective Lifecycle

Objectives are desired state; broker and portfolio observations are observed
state. TradeBot journals the intent and decisions that connect them, while the
broker remains the source of truth for holdings, fills, and live orders.

Every objective has a stable business key, a strategy instance identity, a
strategy version, and a revision. A newer revision must name the active
revision it supersedes. The controller must then:

1. Fence the prior revision from making further brokerage writes.
2. Stop and reconcile its active managed execution.
3. Re-read brokerage state.
4. Validate the successor plan and activate it only when the predecessor is no
   longer live.

If the predecessor fills during cancellation, the successor is stale. TradeBot
must re-evaluate rather than placing a compensating order from the old plan.
This is deliberate optimistic-concurrency behavior: a stale proposal must not
become a dirty broker write.

`PROPOSE` exercises the same strategy, planning, risk, and explainability path
but stops before brokerage writes. Approval always causes a fresh evaluation and
plan comparison before activation.

## Initial Safety Defaults

- One strategy instance per account, with one active objective at a time.
- Atomic multi-leg execution is the default for a covered-call roll.
- Each strategy has a configured risk cap. The default is 10% of current broker
  net-liquidation value; broker-previewed buying-power or margin is reserved
  against that cap before a write and released after terminal reconciliation.
- A named, versioned risk-control policy may automatically authorize
  break-glass legging when its explicit conditions hold. The corresponding
  tactic must reduce risk first, confirm the completed leg, and re-check
  coverage, price limits, and capacity before opening a replacement leg.
- Hard plan incompatibilities always require a new approval: account,
  underlying, direction, quantity, loss of coverage, or loss of the atomic
  structure. Covered-call-specific normalized heuristics may evaluate softer
  changes such as credit, strike, and DTE distance.

## Deployment Semantics

Kubernetes should run and restart TradeBot processes, but it must not be the
system of record for trade intent or brokerage correctness. The domain model
borrows useful controller terms such as desired state, observed state,
generation, reconciliation, and conditions. A Kubernetes Job or CronJob cannot
atomically cancel and reconcile a broker order before activating its successor.

## Package Layout

```text
src/fianchetto_tradebot/
  common_models/
    strategies/                 # Future serializable strategy identity and objective contracts
    managed_executions/         # Existing managed-execution request, response, and lifecycle contracts
  server/
    strategies/                 # Future strategy runner and objective controller
    trident/
      research/                 # Existing market research and candidate construction, not active strategies
    orders/
      managed_executions/       # Future runtime managed-execution coordinator and policy code
      tactics/                  # Existing and future order-scoped execution tactics
```

This change creates the package boundaries only. Current runtime code remains
in its established modules until a child ticket moves it with import, behavior,
and lifecycle coverage. In particular, `managed_order_execution.py` is legacy
placement for the current runtime model; new managed-execution runtime code
belongs under `server/orders/managed_executions/`.

## Deliberate Non-Goals

- Multiple independent strategies within one brokerage account.
- A generic plugin registry, dynamic code upload, or user-supplied broker
  client.
- Kubernetes Jobs or custom resources as the source of truth for objectives.
- Generic strategy-family diplomacy, allocation, or lock management.
- Full lifecycle P&L accounting beyond the initial roll's net credit or debit.
- A universal plan-distance algorithm before multiple objective types justify
  one.
