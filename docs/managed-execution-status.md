# Managed Execution Status

Managed executions have two related but separate status fields:

| Field | Meaning |
| --- | --- |
| `status` | The lifecycle state of TradeBot's managed execution worker. |
| `current_order_status` | The latest lifecycle state reported by the brokerage for the current underlying order. |

`OrderStatus` belongs to the brokerage order. `ManagedExecutionStatus` belongs to
TradeBot's orchestration layer. The two should not be treated as interchangeable
even when their values sound similar.

## Managed Execution States

| Status | Meaning |
| --- | --- |
| `PRE_SUBMISSION` | The managed execution exists, but the worker has not yet established and checked the current brokerage order. |
| `WORKING` | The worker is actively managing the execution, including checking the order, repricing, replacing, or waiting. |
| `CANCEL_REQUESTED` | A user or system action has asked the worker to stop managing the execution and cancel the current order. |
| `CANCELLED` | TradeBot intentionally stopped the managed execution. |
| `EXECUTED` | The managed execution completed successfully because the underlying order executed. |
| `FAILED` | The managed execution cannot safely continue because the worker errored or the brokerage reported a terminal adverse order status that the manager cannot continue from. |

## Managed Execution Transitions

The managed execution status should describe TradeBot's next orchestration
decision, not merely repeat the broker's status string.

The status-change rules live in
`fianchetto_tradebot.common_models.managed_executions.managed_execution_status`.
Worker and cancellation code should use the status-change helper there
instead of assigning managed execution status directly.

Normal managed execution flow:

1. `PRE_SUBMISSION`: the API has accepted the managed execution request.
2. `WORKING`: the worker has created or found the current brokerage order and
   is responsible for monitoring and repricing it.
3. `EXECUTED`: the worker checked the brokerage order and found it complete.

Intentional cancellation flow:

1. `WORKING`: the worker is actively managing the current brokerage order.
2. `CANCEL_REQUESTED`: TradeBot has asked the worker to stop managing the order.
3. `CANCELLED`: TradeBot has completed the managed cancellation path.

Failure flow:

1. `WORKING`: the worker is actively managing the current brokerage order.
2. `FAILED`: the worker errored, or the broker reported a terminal adverse
   status such as `EXPIRED` or an unreconciled `REJECTED` that the manager
   cannot continue from.

Terminal managed executions are immutable through the cancellation API. Once a
managed execution reaches `EXECUTED`, `CANCELLED`, or `FAILED`, a later cancel
request must return the existing managed execution state without cancelling the
underlying brokerage order or rewriting the managed execution status.

Invalid non-idempotent status changes raise `InvalidManagedExecutionStatusChange`.
Reapplying the same status is idempotent, which keeps repeated checks of
an already-recorded state safe.

## Brokerage Status Translation

When MOEX checks the current brokerage order, it records the raw brokerage
status in `current_order_status`. It then translates that order status into the
managed-execution lifecycle:

The default translation is table-driven. Context-specific overrides are only
used when the current managed execution status matters. Today, the important
override is cancellation: once a managed execution is `CANCEL_REQUESTED`, a
later active-looking brokerage order check must not move it back to `WORKING`.

| Brokerage `OrderStatus` | Managed `ManagedExecutionStatus` | Rationale |
| --- | --- | --- |
| `OPEN` | `WORKING` | The order is live and the worker can continue managing it. |
| `PARTIAL` | `WORKING` | The execution is still active; partial fill details remain brokerage order data. |
| `INDIVIDUAL_FILLS` | `WORKING` | Fill detail belongs to order state while the manager continues. |
| `CANCEL_REQUESTED` | `WORKING` | Broker-side cancellation is not the same as TradeBot deciding the managed execution is cancelled. |
| `PRE_SUBMISSION` | `WORKING` | The broker has not fully accepted the order yet, but the worker is still responsible for it. |
| `EXECUTED` | `EXECUTED` | The managed execution achieved its goal. |
| `CANCELLED` | `WORKING` | The manager may cancel one underlying order as part of replacement/re-entry; this is not the same as cancelling the managed execution. |
| `EXPIRED` | `FAILED` | The order reached a terminal state without execution. |
| `REJECTED` | `FAILED`, or `EXECUTED` after reconciliation | The broker rejected the order, so the manager cannot usually proceed normally. If the same order appears in the executed-order list, TradeBot treats the rejection as a broker race and records the order as executed. |
| `ANY` | Invalid | `ANY` is a query filter, not a real order lifecycle state. |

Intentional managed cancellation is handled by the cancellation path:

1. `cancel_managed_execution` confirms the managed execution is not already terminal.
2. It asks the worker to stop, moving the managed execution to `CANCEL_REQUESTED`.
3. The order service cancels the current brokerage order.
4. The managed execution moves to `CANCELLED`.

## Creation Readiness

`create_managed_execution` should not report that a managed execution is ready
only because it has a brokerage order ID. It should wait until the worker has
also fetched the first brokerage order status and populated `current_order_status`.
That keeps the returned managed execution state deterministic for callers and
tests.
