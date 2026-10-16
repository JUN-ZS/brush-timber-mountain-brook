# QQQ put-ratio research output

- Study commit tested: 3f7e2d98ff229d5d9e0a22edef36f383fca77cc2
- GitHub Actions run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38911332183
- Option-chain last observed date: 2025-12-15
- Replay, scale matrix, and dynamic NAV/BAR/MaxDD stress matrix: completed by this workflow before persistence.
- Dynamic results compound closed episodes into the next NAV; BAR rates are observed episode/mark frequency, not forward probability.
- Policy-MAE sensitivity uses only clean prior resolved episode marks; strict sign-reversal uses the same original contract IDs and strikes. Full-terminal exposure remains separate and outputs are retained in policy_mae_reversal/.
- External Yahoo/FRED and Yahoo ^VIX/^VXN proxies, when available, are price-path-only; they do not estimate option P&L after the option-chain boundary.
- Cost-sensitivity audit pairs zero/base/adverse model assumptions and screens friction BAR sample counts; it does not validate fills or promote any exit rule.
- Every output is research evidence only. Deployment and broker orders remain BLOCKED.
- Persisted because GitHub Actions artifact upload quota was exhausted; this directory is committed only on the isolated research branch.
