# Strategy Instance / Campaign Instance v1

This is a separate personal campaign ledger.

**System Evidence:** \`research/evidence_v1/\` records what the desk observes over time.

**Personal Instance:** \`research/strategy_instance_v1/instances/<INSTANCE_ID>/\` records one actual campaign from the user's economic T0.

## T0 rule

\`start_at_utc\` is the user's economic T0.

\`created_at_utc\` is when the instance record was created.

Initial positions/cost basis are immutable USER_INITIAL input. Broker deals are applied only when their timestamp is **after created_at_utc**, so the original entry is not double-counted.

Changing initial state materially means creating a new instance, not rewriting the old one.

## Direct path

\`Futu OpenD -> local Python tracker -> instance ledger/state -> report\`

Grok is **not** the raw recorder. It may inspect the resulting report and explain what happened, but broker timestamps, fills and P&L originate from the local reader.

## Windows CMD

Create:

\`\`\`cmd
python -m research.strategy_instance_v1.run_instance init --instance-id MY_001 --start-at-utc 2026-10-01T01:30:00+00:00 --position "US.QQQ.EXAMPLE,LONG,1,12.34" --position "US.QQQ.EXAMPLE2,SHORT,10,1.23" --note "actual T0"
\`\`\`

Record once:

\`\`\`cmd
python -m research.strategy_instance_v1.run_instance cycle --instance-id MY_001 --observe-strategy-plan
\`\`\`

Run every 5 minutes:

\`\`\`cmd
python -m research.strategy_instance_v1.run_instance watch --instance-id MY_001 --interval 300 --observe-strategy-plan
\`\`\`

Manual note:

\`\`\`cmd
python -m research.strategy_instance_v1.run_instance note --instance-id MY_001 --text "manual roll because spread widened"
\`\`\`

Adjustable manual strategy book:

\`\`\`cmd
python -m research.strategy_instance_v1.run_instance manual --instance-id MY_001 --action ADD --code US.QQQ260116C00600000 --qty 2 --price 8.50 --note "manual add"
python -m research.strategy_instance_v1.run_instance manual --instance-id MY_001 --action REDUCE --code US.QQQ260116C00600000 --qty 1 --price 10.25 --note "manual harvest"
python -m research.strategy_instance_v1.run_instance manual --instance-id MY_001 --action SELL_FAR --code US.QQQ260116C00600000 --qty 10 --price 2.10 --note "manual far short"
python -m research.strategy_instance_v1.run_instance manual --instance-id MY_001 --action BUY_BACK_FAR --code US.QQQ260116C00600000 --qty 2 --price 3.40 --note "manual far cover"
\`\`\`

The \`manual\` commands create a separate adjustable operator book. They do not alter the broker-observed \`lots\`, broker realized P&L, or broker reconciliation. This keeps USER_MANUAL input separate from Futu observations. The report shows broker-observed P&L and manual-book P&L side by side.


Report / verify:

\`\`\`cmd
python -m research.strategy_instance_v1.run_instance report --instance-id MY_001
python -m research.strategy_instance_v1.run_instance verify --instance-id MY_001
\`\`\`

The launcher \`run_strategy_instance.cmd\` lets you omit the module prefix when desired.

Operator Console:

```cmd
run_strategy_operator.cmd
```

Open:

`http://127.0.0.1:8766/research/strategy_instance_v1/operator_dashboard.html`

The console provides:
- instance selector
- locked strategy ticket / risk snapshot
- manual ADD / REDUCE / SELL_FAR / BUY_BACK_FAR controls
- +1 / +5 / -1 / -5 quantity shortcuts
- realized-P&L preview before commit
- one-click manual ledger recording
- broker refresh (read-only Futu/OpenD cycle)
- manual positions, marks, recent manual trades, and ledger hash

The console binds to `127.0.0.1` by default. Browser actions write only the `USER_MANUAL` instance ledger; they never submit broker orders.

### Recommended operating flow

1. Start Futu OpenD.
2. Start the normal live desk watcher if you want the locked strategy to continue observing market state:

```cmd
python -m research.live_hedge_v1.watch_live_desk --interval 15
```

3. Start the local Operator Console:

```cmd
run_strategy_operator.cmd
```

4. Open the Operator Console and select your instance.
5. When the locked strategy has a ticket, use **USE TICKET AS MANUAL TEMPLATE**. Change the quantity and/or price before recording when your actual execution differs.
6. Press **Refresh Broker** after execution to update broker observations and the manual-book mark.

The semantic split is:

```
LOCKED STRATEGY -> candidate/ticket -> BROKER OBSERVED P&L

YOUR ADJUSTMENT -> USER_MANUAL trade -> MANUAL BOOK P&L
```

A manual trade also stores the strategy ticket visible at that moment, so later analysis can distinguish following the strategy from changing size or acting independently.


## Automatically recorded

Broker positions/orders/deals, exact local snapshot plus SHA-256, newly observed executions, FIFO gross realized P&L, marked unrealized P&L, total gross P&L, broker-vs-instance reconciliation, read-only strategy-plan observations, the separate manual-book mark/P&L, manual trade events, manual notes, and DATA_GAPs.

No order is submitted or modified.

## Scheduling

With Futu OpenD on the same Windows PC, Windows Task Scheduler or the long-running \`watch\` mode is the direct primary recorder. GitHub Actions is not the raw recorder when OpenD is only reachable locally.

## Offline / PC-off recovery

The broker-side transaction record is recoverable after an outage. When the next cycle sees no prior cycle, or a gap of at least `--backfill-after-minutes` (default 10), the recorder asks Futu for historical live executions from the recovery date through today. Futu documents both historical orders and historical executed trades for live accounts. `deal_id` is used for deduplication, so a fill seen before and after the outage is not counted twice.

What cannot be reconstructed exactly is the missed *market-state path*: the precise option bid/ask/Greek/risk state that would have existed at every 5-minute point while the recorder was offline. Those missing periods remain a DATA_GAP rather than invented snapshots.

Therefore the evidence hierarchy is:

```
Broker deal/fill     -> recoverable
Broker order history -> recoverable
Current positions    -> recoverable
Exact missed quote path -> NOT recoverable
Strategy observation during outage -> NOT recoverable
```

A later backfill restores transaction truth; it does not manufacture missing historical market observations.

## Cloud operation

For 24/7 recording, put OpenD and this recorder on a VPS. The Windows PC then becomes a trading/monitoring terminal rather than the evidence recorder. A VPS scheduler such as Windows Task Scheduler, cron, or systemd timer is preferable to using a Grok/Cursor bot as the scheduler. Grok/Cursor can be used to inspect reports or maintain the deployment, but should not be the source of record.
