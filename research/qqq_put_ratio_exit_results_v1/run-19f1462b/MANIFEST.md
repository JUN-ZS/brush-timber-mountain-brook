# QQQ put-ratio research output

- Study commit tested: 19f1462b19b5252adade68ae83c3b669838e14ba
- GitHub Actions run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38905755251
- Option-chain last observed date: 2025-12-15
- Replay, scale matrix, and dynamic NAV/BAR/MaxDD stress matrix: completed by this workflow before persistence.
- Dynamic results compound closed episodes into the next NAV; BAR rates are observed episode/mark frequency, not forward probability.
- External Yahoo/FRED and Yahoo ^VIX/^VXN proxies, when available, are price-path-only; they do not estimate option P&L after the option-chain boundary.
- Cost-sensitivity audit pairs zero/base/adverse model assumptions and screens friction BAR sample counts; it does not validate fills or promote any exit rule.
- Every output is research evidence only. Deployment and broker orders remain BLOCKED.
- Persisted because GitHub Actions artifact upload quota was exhausted; this directory is committed only on the isolated research branch.
