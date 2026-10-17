# QQQ Forward Shadow Intake V1

This is an **intake kit, not a dataset**. No current market prices or forward observations are populated. The pinned historical QQQ option archive ends on 2025-12-15, so the next evidence should be collected prospectively from a permitted manual capture, broker export or licensed source.

Read CAPTURE_PROTOCOL_V1.md before creating snapshots. Blank structure templates live under templates/; they are deliberately invalid until actual fields and source evidence are supplied. Do not put templates in snapshots/ or count them as observations.

The validator:
- checks SHA-256 against the unchanged evidence file;
- validates standard QQQ OCC identity, expiry/right/strike, quote date, Bid/Ask, displayed size and Delta;
- requires timezone-aware ISO-8601 timestamps and verifies the market date after converting to source.observation_timezone;
- checks frozen signal fields, exact contract consistency across episodes, side-correct entry/exit depth, missing marks and execution-disabled flags;
- never scrapes webpages, places orders, interpolates prices or proves a fill/strategy edge.

## Commands

From repository root, validate one completed snapshot:

    python research/qqq_option_forward_shadow_v1/validate_shadow_snapshot.py --snapshot research/qqq_option_forward_shadow_v1/snapshots/SNAPSHOT_ID.json --root research/qqq_option_forward_shadow_v1

Validate the append-only ledger:

    python research/qqq_option_forward_shadow_v1/validate_shadow_snapshot.py --snapshot-dir research/qqq_option_forward_shadow_v1/snapshots --root research/qqq_option_forward_shadow_v1

Windows evidence hash:

    certutil -hashfile "C:\path\to\evidence.png" SHA256

Linux evidence hash:

    sha256sum evidence.png

No broker order path or live HUB policy is enabled by this intake.
