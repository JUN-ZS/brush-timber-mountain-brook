# QQQ Forward Shadow Intake V1

Manual or authorized-source intake for new option observations. The pinned historical QQQ option archive ends on 2025-12-15; no 2026 option P&L is inferred.

Validation commands (run from the repository root):

    python research/qqq_option_forward_shadow_v1/validate_shadow_snapshot.py --snapshot research/qqq_option_forward_shadow_v1/snapshots/SNAP_ID.json --root research/qqq_option_forward_shadow_v1

    python research/qqq_option_forward_shadow_v1/validate_shadow_snapshot.py --snapshot-dir research/qqq_option_forward_shadow_v1/snapshots --root research/qqq_option_forward_shadow_v1

Each snapshot evidence file must exist under the root and its SHA-256 must match. Snapshot files are immutable; filename stem must equal snapshot_id. The validator checks source evidence, contract identity, date alignment, quote side/size, the frozen signal definition and exact contracts across episode records. It never scrapes external webpages, places orders or fills missing quotes.

No current forward sample is fabricated or pre-populated. The first record must be sourced from an actual permitted manual capture, broker export or licensed source.
