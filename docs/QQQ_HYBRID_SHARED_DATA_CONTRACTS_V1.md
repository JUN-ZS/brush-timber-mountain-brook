# QQQ Hybrid Shared Data Contracts V1

**Purpose:** 定義各框架之間唯一允許的資料交接口。UI、即時操作台、研究回放及統計報告不能自行發明相同名字卻不同含義的欄位。這是規格草案；在實作前需先補 JSON Schema／validator／golden fixtures，並保留舊版原始輸出以對照。

**Related specs:** [Logic, Causality & Evidence Framework](./QQQ_HYBRID_LOGIC_CAUSALITY_FRAMEWORK_V1.md) · [Measurement UI Contract](./QQQ_HYBRID_MEASUREMENT_UI_CONTRACT_V1.md)

## 1. Type / unit / null rules

- Money: USD, decimal; price in USD per share/contract quote unit; option contract multiplier explicit (usually 100, never assumed silently).
- Percent units use explicit names: `*_pct` means 0–100 percentage points; `*_fraction` means 0–1. Never mix `5` and `0.05` without conversion.
- Time: RFC 3339 / ISO-8601 timestamp with timezone offset for instant; `YYYY-MM-DD` for date-only fields. Preserve original timezone/source string where provided.
- Integer trade units: integer contracts or shares. No fractional listed option contracts.
- Missing value: `null` plus a field-level reason/status. Missing is never 0, empty string, infinity, forward-filled value, or assumed unlimited capacity.
- Every derived/estimated output carries `evidence_class`, `formula_or_model_id`, and links to its inputs.
- Fields labeled optional may be null, but an operation must declare which fields are required for that calculation.
- IDs are stable opaque strings; identical scenario comparisons must not regenerate episode IDs merely because an exit rule changed.

## 2. Shared enums

```ts
type EvidenceClass = "OBSERVED" | "DERIVED" | "ESTIMATED" | "HYPOTHETICAL";
type DataState =
  | "FRESH" | "STALE" | "MIXED" | "PENDING" | "BLOCKED"
  | "ESTIMATED_ONLY" | "INCONCLUSIVE";
type OperatingMode =
  | "FROZEN_OPERATOR" | "MANUAL_CAPACITY_ONLY"
  | "RESEARCH_SCENARIO" | "HISTORICAL_REPLAY";
type ActionKind =
  | "BUY" | "ADD" | "HOLD" | "REDUCE" | "SELL"
  | "CLOSE" | "ROLL" | "PENDING" | "BLOCK";
type BudgetSemantics =
  | "PREMIUM_CASH" | "MAX_EXPIRY_LOSS"
  | "INTERIM_STRESS_LOSS" | "BROKER_MARGIN";
type MarkConvention =
  | "MIDPOINT_REFERENCE" | "CONSERVATIVE_QUOTE_SIDE"
  | "OBSERVED_BROKER_FILL" | "HYPOTHETICAL_STRESS";
type ExecutionEvidence =
  | "OBSERVED_BROKER_FILL" | "EOD_QUOTE_SIDE_REPLAY"
  | "MODELLED_FILL" | "NO_EXECUTION_EVIDENCE";
```

`READY` is deliberately not a global state. An individual calculation may be computable while the source data remains ESTIMATED_ONLY, the scenario is INCONCLUSIVE, or live execution is BLOCKED. Every result has separate calculation, evidence and operation states.

## 3. Field envelope: EvidenceValue<T>

All fields that directly influence decisions should be representable as:

```ts
type EvidenceValue<T> = {
  value: T | null;
  unit: string;
  evidence_class: EvidenceClass;
  data_state: DataState;
  source_id: string | null;
  source_version_or_hash: string | null;
  observed_at: string | null;
  as_of: string | null;
  received_at: string | null;
  transformation_id: string | null;
  parent_field_ids: string[];
  missing_reason: string | null;
  notes: string[];
};
```

This is a semantic model, not a requirement that every table cell render all metadata. UI may compact it, but expanding a value must reveal its envelope. For raw source records, `transformation_id` can be null; for DERIVED outputs it must identify the transformation.

## 4. MarketSnapshot

```ts
type VXContractMark = {
  symbol: string;
  expiry: string;                   // YYYY-MM-DD
  price: EvidenceValue<number>;
  quote_or_snapshot_time: string | null;
  contract_family: "STANDARD_MONTHLY" | "WEEKLY" | "VXM" | "VXMT" | "TAS" | "OTHER";
};

type MarketSnapshot = {
  snapshot_id: string;
  requested_as_of: string;
  captured_at: string;
  data_state: DataState;
  mode: OperatingMode;
  spots: {
    QQQ: EvidenceValue<number>;
    VXX: EvidenceValue<number>;
    VIX: EvidenceValue<number>;
    VXN: EvidenceValue<number>;
  };
  vx_term: {
    source_id: string | null;
    source_mode: "CBOE_DELAYED" | "OPEND" | "MANUAL_TEST" | "OTHER" | null;
    m1: VXContractMark | null;
    m2: VXContractMark | null;
    slope_pct: EvidenceValue<number>;
    selection_audit_id: string | null;
  };
  provenance_by_field: Record<string, EvidenceValue<unknown>>;
  blockers: string[];
  warnings: string[];
};
```

**Invariants**
1. M1 and M2 are verified eligible contracts, strictly ordered by actual expiry and with expiry later than the as-of date; they cannot be inferred from VIX spot.
2. `slope_pct = 100 * (M2.price - M1.price) / M1.price`, only when both prices are finite and M1 is nonzero.
3. If either expiry identity, price provenance, or the relevant as-of is unknown, `slope_pct.value=null` and data state is PENDING/BLOCKED; do not classify carry using an absent slope.
4. If any source is MIXED in time, preserve each field's as-of. A newer field does not overwrite another field's timestamp.

## 5. OptionLeg and OptionStructure

```ts
type OptionLeg = {
  leg_id: string;
  underlying: "QQQ" | "VXX" | string;
  contract_id: string;              // exact listed contract identity
  option_type: "CALL" | "PUT";
  side: "BUY" | "SELL";
  quantity: number;                 // non-negative integer
  multiplier: number | null;
  expiry: string;
  strike: number;
  bid: EvidenceValue<number>;
  ask: EvidenceValue<number>;
  bid_size: EvidenceValue<number>;
  ask_size: EvidenceValue<number>;
  delta: EvidenceValue<number>;
  implied_volatility: EvidenceValue<number>;
  quote_state: DataState;
};

type OptionStructure = {
  structure_id: string;
  scenario_id: string;
  legs: OptionLeg[];
  net_entry_cash_usd: EvidenceValue<number>;
  net_liquidation_value_usd: EvidenceValue<number>;
  max_terminal_profit_usd: EvidenceValue<number>;
  max_terminal_loss_usd: EvidenceValue<number>;
  payoff_model_id: string;
  budget_semantics: BudgetSemantics | null;
  data_state: DataState;
  blockers: string[];
};
```

**Invariants**
- Every required leg must have compatible underlying, contract type, multiplier and intended expiry relationship; any exception must be explicit in the strategy contract.
- `bid_size` and `ask_size` refer to the quote-side count in the provider's declared units; they are not interchangeable and cannot be ignored during capacity calculations.
- Provider Delta and model-estimated Delta share the numeric range but not evidence class. The label must survive normalization and rendering.
- Credit flow, terminal payoff loss, interim liquidation stress and broker margin are separate values. A value for one cannot fill another.
- Max terminal loss is computed over the full payoff structure and its necessary payoff knots; the QQQ=0 payoff alone is not automatically the global worst case.
- An incomplete leg set yields missing risk outputs plus PENDING/BLOCKED, not a zero-risk structure.

## 6. PositionLedger and FillLedger

```ts
type PositionLine = {
  position_id: string;
  sleeve: "QQQ_CORE" | "QQQ_FAR_CALL"
    | "VXX_UNDERLYING_SHORT" | "VXX_CALL_CREDIT_SPREAD"
    | "RESEARCH_PUT_RATIO" | "OTHER";
  instrument_id: string;
  signed_quantity: number;           // shares/contracts, with a documented sign convention
  avg_entry_price_usd: number | null;
  mark_price: EvidenceValue<number>;
  market_value_usd: EvidenceValue<number>;
  unrealized_pnl_usd: EvidenceValue<number>;
  source_ledger_id: string;
  as_of: string;
};

type PositionLedger = {
  ledger_id: string;
  as_of: string;
  nav_usd: EvidenceValue<number>;
  cash_usd: EvidenceValue<number>;
  buying_power_usd: EvidenceValue<number>;
  reserve_cash_usd: EvidenceValue<number>;
  occupied_margin_usd: EvidenceValue<number>;
  lines: PositionLine[];
  reconciliation_state: DataState;
  reconciliation_differences_usd: number | null;
};

type FillLedgerEntry = {
  fill_id: string;
  order_id: string;
  instrument_id: string;
  signed_filled_quantity: number;
  fill_price_usd: number;
  commission_usd: number | null;
  other_fees_usd: number | null;
  broker_timestamp: string;
  broker_reference: string | null;
  evidence_class: "OBSERVED";
};
```

**Invariants**
- PositionLedger is current confirmed state, not a target, not an open order and not a simulated fill.
- Actual fill entries are append-only; corrections should be compensating entries or explicit adjustments with a trail, not silent rewrite of history.
- NAV must reconcile according to an explicit accounting definition; if cash, mark or positions needed for reconciliation are missing, NAV-derived sizing is PENDING.
- The accounting sign convention must be uniform across stock shorts and option short legs. User-visible labels must retain the sleeve distinctions above.

## 7. ScenarioConfig (all adjustable controls live here first)

```ts
type ScenarioConfig = {
  scenario_id: string;
  scenario_hash: string;
  created_at: string;
  parent_scenario_id: string | null;
  mode: OperatingMode;
  policy_version: string;
  engine_version: string;
  market_snapshot_id: string;
  position_ledger_id: string | null;
  sample_start: string | null;
  sample_end: string | null;
  sample_class: "DEVELOPMENT" | "VALIDATION" | "UNSEEN_HOLDOUT" | "LIVE_SNAPSHOT";
  nav_usd: number | null;
  budget_semantics: BudgetSemantics;
  risk_budget_fraction: number | null;  // 0..1, not percentage points
  ratio_direction: "SHORT_HEAVY_1_LONG_N_SHORT" | "LONG_HEAVY_N_LONG_1_SHORT" | null;
  ratio_n: number | null;
  hold_sessions: number | null;
  exit_policy_id: string | null;
  profit_target_nav_fraction: number | null;
  loss_stop_nav_fraction: number | null;
  action_delay_sessions: number;
  mark_convention: MarkConvention;
  slippage_per_leg_per_side_usd: number;
  commission_per_contract_per_side_usd: number;
  borrow_annual_rate_fraction: number | null;
  quote_depth_fraction: number;
  stress_config_id: string | null;
};
```

**Invariants**
- Scenario parameters are immutable after results are generated. Editing creates a new scenario ID/hash.
- Hash canonicalization must define property ordering, numeric precision, null representation and timezone normalization.
- When only NAV changes, source market facts, contract identity and historical episode IDs remain unchanged.
- When costs change, raw source quotes and signals remain unchanged.
- When exit policy changes, paired-event entry contract identity stays fixed unless the scenario explicitly changes entry policy too.
- Budget semantics are required. No generic `budget_pct` may mean premium in one engine and max loss in another.

## 8. RiskCapacity

```ts
type CapacityLimit = {
  limit_id: "RISK" | "CASH" | "MARGIN" | "QUOTE_DEPTH" | "BORROW" | "INTEGER_UNIT" | "DATA_GATE";
  max_units: number | null;
  data_state: DataState;
  evidence_class: EvidenceClass;
  source_or_model_id: string;
  explanation: string;
};

type RiskCapacity = {
  scenario_id: string;
  current_units: number | null;
  target_units: number | null;        // theoretical desired holding
  max_buy_units: number | null;       // executable only when all gates support it
  max_sell_units: number | null;
  limits: CapacityLimit[];
  binding_constraint: CapacityLimit["limit_id"] | null;
  tail_loss_per_unit_usd: EvidenceValue<number>;
  cash_per_unit_usd: EvidenceValue<number>;
  margin_per_unit_usd: EvidenceValue<number>;
  depth_units: EvidenceValue<number>;
  status: DataState;
  blockers: string[];
};
```

**Invariants**
- For known, finite caps, `max_buy_units = max(0, min(all applicable caps))`; any unknown required cap is not infinity.
- A `target_units` value may exist while `max_buy_units=0`; both must be shown and explained separately.
- `max_sell_units` cannot exceed confirmed current units. Multi-leg closing capacity must use the correct quote side and size for every required leg and show residual unhedged risk.
- If no executable quote/size or margin confirmation exists, do not label a theoretical number as live-ready. Show theoretical capacity separately with ESTIMATED_ONLY/PENDING/BLOCKED.

## 9. DecisionOutput

```ts
type DecisionOutput = {
  decision_id: string;
  snapshot_id: string;
  scenario_id: string | null;
  mode: OperatingMode;
  policy_version: string;
  engine_version: string;
  data_state: DataState;
  regime: string | null;
  current_positions_ref: string | null;
  target_positions: Record<string, number> | null;
  deltas: Record<string, number> | null;
  capacity_ref: string | null;
  action: ActionKind;
  reason_codes: string[];
  reason_text: string[];
  evidence_refs: string[];
  human_review_required: boolean;
  execution_enabled: false;
};
```

**Required distinction**
- DecisionOutput is a recommendation/explanation object; it cannot represent an order or fill.
- `execution_enabled` stays false in this system contract. Actual order permissions must be controlled elsewhere and cannot be toggled by ScenarioConfig.
- For hard data blocks per current V3 contract: current positions are preserved, no new deployment and no automatic reduce. The display must separately say risk may remain unresolved.
- If a relevant option candidate is absent, do not infer `target quantity=0` unless a valid policy independently and explicitly requires that target independent of the missing candidate. Preserve the unresolved field and reason.

## 10. ReplayEpisode and ReplayAction

```ts
type ReplayAction = {
  signal_as_of: string;
  action_type: "OPEN" | "CLOSE" | "TRIM" | "ROLL" | "DEFER" | "NO_ACTION";
  execution_observed_at: string | null;
  quote_snapshot_id: string | null;
  execution_evidence: ExecutionEvidence;
  quote_side_reference: MarkConvention | null;
  requested_quantity: number;
  executable_quantity: number | null;
  deferred_reason: string | null;
};

type ReplayEpisode = {
  episode_id: string;
  source_dataset_hash: string;
  source_end: string;
  entry_contract_ids: string[];
  entry_as_of: string;
  entry_action: ReplayAction;
  actions: ReplayAction[];
  exit_policy_id: string;
  cost_model_id: string;
  gross_pnl_usd: number | null;
  costs_usd: number | null;
  net_pnl_usd: number | null;
  terminal_stress_loss_usd: number | null;
  realized_status: "RESOLVED" | "UNRESOLVED_SOURCE_END" | "MISSING_MARK" | "BLOCKED_ENTRY" | "SKIPPED_SIZE";
  sample_class: "DEVELOPMENT" | "VALIDATION" | "UNSEEN_HOLDOUT";
  limitations: string[];
};
```

**Invariants**
- EOD quote replay action time may not precede a later observed valid quote; if delayed, keep both signal and action times.
- EOD mark must not be given `OBSERVED_BROKER_FILL` evidence.
- Missing marks are not forward-filled and unresolved episodes do not enter resolved-P&L denominator.
- Paired policies for the same episode preserve entry IDs unless entry policy is explicitly part of the experiment.
- Source boundary is a first-class field; price-only supplements after the option-chain boundary do not create option P&L episodes.

## 11. ProbabilityEstimate

```ts
type ProbabilityEstimate = {
  estimate_id: string;
  scenario_id: string;
  event_definition: string;
  metric_kind: "PRICE_PATH_FREQUENCY" | "DAILY_POSITIVE_RATIO" | "EPISODE_WIN_RATE" | "CONDITIONAL_FREQUENCY";
  numerator: number;
  denominator: number;
  unresolved_count: number;
  overlapping_windows: boolean | null;
  state_condition_definition: Record<string, unknown>;
  point_estimate_fraction: number | null; // 0..1
  interval_method: string | null;
  interval_low_fraction: number | null;
  interval_high_fraction: number | null;
  dependence_adjustment: string | null;
  sample_class: string;
  data_state: DataState;
  evidence_refs: string[];
  limitations: string[];
};
```

**Invariants**
- Fraction uses 0..1 internally; UI converts to percentage points for display.
- `denominator=0` means point estimate and interval are null, status INCONCLUSIVE; never output 0% as though observed.
- Metric kind determines eligible unit of analysis; daily returns, price windows and option episodes cannot share denominators.
- Number of rows in a parameter matrix is not the effective sample count. A grid with many policies can all reuse the same episodes.
- Conditional filters must use only information observable at the start of the forecast window.

## 12. EvidenceManifest / RunResult

```ts
type EvidenceManifest = {
  run_id: string;
  tested_commit_sha: string;
  workflow_path: string;
  runner_label: string;
  started_at: string;
  completed_at: string | null;
  source_files: Array<{ path: string; sha256_or_git_blob_sha: string; source_end: string | null }>;
  scenario_hashes: string[];
  output_files: Array<{ path: string; sha256_or_git_blob_sha: string; row_count: number | null }>;
  tests: Array<{ name: string; status: "PASS" | "FAIL" | "SKIPPED"; details: string }>;
  artifact_upload_status: "SUCCESS" | "QUOTA_BLOCKED" | "FAILED" | "NOT_USED";
  persistence_commit_sha: string | null;
  limitations: string[];
};
```

Calculation completion, report generation, artifact upload, and durable persistence are independent outcomes. If artifact upload hits quota but outputs are committed to a branch, report both outcomes truthfully; do not report the entire run as failed solely because the secondary artifact step failed, and do not report artifacts as retained if persistence also failed.

## 13. Reason-code registry (initial contract)

Codes should be stable machine-readable values; UI text is presentation and may be translated. This initial registry is deliberately conservative:

| Code | Meaning | Expected state / consequence |
|---|---|---|
| `DATA_REQUIRED_FIELD_MISSING` | Required data value absent | PENDING/BLOCKED; no inferred default |
| `DATA_TIMESTAMP_MISSING` | Required as-of missing | PENDING/BLOCKED; not FRESH |
| `DATA_STALE` | Required source too old | STALE; block action as contract requires |
| `DATA_ASOF_MIXED` | Cross-source as-of gap too large | MIXED; no new deployment |
| `SOURCE_HASH_MISMATCH` | Pinned source integrity failed | BLOCKED |
| `VX_CONTRACT_NOT_ELIGIBLE` | Wrong contract family/expiry/order | BLOCKED term calculation |
| `OPTION_LEG_INCOMPLETE` | Required option leg missing | PENDING/BLOCKED structure |
| `OPTION_QUOTE_INVALID` | Invalid / crossed / non-finite quote | PENDING/BLOCKED affected action |
| `OPTION_SIZE_INSUFFICIENT` | Any required leg cannot support quantity | Reduce capacity or BLOCK |
| `BUDGET_SEMANTICS_UNSET` | Premium and risk budget not distinguished | PENDING sizing |
| `RISK_BUDGET_EXCEEDED` | Scenario risk cap exceeded | MAX BUY=0 or reduced |
| `CASH_LIMIT` | Cash/buying-power cap binding | MAX BUY reduced |
| `MARGIN_UNKNOWN` | Required broker margin not confirmed | Theoretical-only / BLOCK live capacity |
| `CLOSE_QUOTE_UNAVAILABLE` | Cannot quote-side price a required close leg | PENDING / unresolved risk |
| `REPLAY_ACTION_DEFERRED` | Valid execution quote unavailable at signal | Record deferred action; no fill claim |
| `SAMPLE_INSUFFICIENT` | Denominator/precision inadequate | INCONCLUSIVE |
| `SOURCE_END_CENSORING` | Dataset ends before outcome resolves | unresolved; excluded from resolved denominator |
| `RESEARCH_MODE_ONLY` | Candidate belongs to research, not frozen ops | no live target/order mutation |

## 14. Canonical computation rules

1. **Term slope:** `S_pct = 100 * (M2 - M1) / M1` when eligible and M1 ≠ 0.
2. **NAV fraction:** `exposure_fraction = market_value_usd / nav_usd` only with reconciled positive NAV and valid mark.
3. **NAV risk amount:** `risk_budget_usd = nav_usd * risk_budget_fraction`; the fraction semantics are explicit 0..1.
4. **Vertical spread maximum expiry loss:** derive from payoff using correct signed quantities, multiplier and net entry cash; do not use gross credit as loss cap.
5. **Quote-side marks:** opening long at Ask / opening short at Bid; closing short at Ask / closing long at Bid, per available side and quantity. Apply additional modeled slippage/fees separately.
6. **Capacity:** `max_buy_units = min(applicable verified integer limits)`; any unknown required live limit prevents a live-ready result.
7. **Episode win rate:** `count(resolved eligible episodes with net_pnl_usd > 0) / count(resolved eligible episodes)`; display flat and unresolved separately.
8. **Daily positive ratio:** separate calculation over valid daily returns; never call this episode win rate.
9. **Price-path frequency:** count valid starts whose forward outcome meets the stated threshold divided by valid eligible starts. Declare overlapping window policy.
10. **Cost drag:** midpoint-to-quote-side valuation difference is a mark reconciliation and assumption sensitivity, not confirmed slippage or fill.
11. **Reproducibility:** same source hash + scenario hash + engine version must yield matching canonical outputs within a declared numeric tolerance.
12. **Unknown outputs:** if a required term is null or invalid, output null plus reason; do not make up a point estimate.

## 15. Compatibility and migration contract

- Keep current V3 fields as an adapter surface while new structures are built; document mapping per field rather than doing a wholesale rewrite.
- Never silently reinterpret the existing 1.2% / 2% option sleeve constants. Before any UI sizing uses them, declare whether each is premium/cash budget, max-loss budget, or another explicitly named concept. If historical versions disagree, expose the difference and keep calculations side-by-side until resolved.
- Schema migration is versioned. Existing journal rows remain interpretable by their original `engine_version` and `policy_version`; do not retroactively apply new semantics to historical records.
- Put Ratio output keeps `RESEARCH_PUT_RATIO` sleeve and research mode even if it appears beside other research charts.
- No data contract can authorize broker order placement. Execution remains an independent permission boundary.

## 16. Definition of done

A data contract is ready for implementation only when:
1. Type/schema validation exists.
2. Required vs optional fields are operation-specific and documented.
3. Missing / stale / mixed / estimate-only behavior is tested.
4. At least one golden fixture covers each state and ratio direction.
5. Same episode + same scenario inputs is reproducible.
6. Every output links to source evidence and limitations.
7. The adapter to existing V3 fields has a reviewed mapping.
8. No change to frozen policy or order permissions is implied.
