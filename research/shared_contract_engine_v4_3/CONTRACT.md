# SharedContractEngine V4.3 — isolated strict contract module

**Status:** additive ES module research implementation; not wired into the user's Canvas HTML and not a live trading engine. Import it as an ES module (or use Node 24+ `require(ESM)`); it also exposes `globalThis.SharedContractEngineV43` after module evaluation. It contains no broker API or order path.

## Implemented

- Strict numeric parsing: EMPTY is distinct from explicit zero; coercive strings, booleans, arrays, objects, NaN and infinities are rejected.
- Raw-file CSV/JSON import for option quotes, user-defined episode manifests and underlying EOD history. Each imported file receives a SHA-256 digest; each row remains explicitly unauthenticated until its source is independently verified.
- Quote requirements include contract ID, underlying, expiry, right, strike, ISO timestamp with timezone, bid, ask, side-specific bid/ask size and explicit contract multiplier. Crossed markets, missing fields, OCC term mismatches and inadequate sizes fail closed.
- Coverage report keeps option-chain coverage and QQQ spot-history coverage separate. No 62 episode or 240 window records are generated in code.
- Put-ratio replay requires exact timestamps for both legs at entry and exit and computes long entry at ask, long exit at bid, short entry at bid, and short exit at ask. It reports EOD quote-side replay, never a confirmed fill.
- Ledger requires position-specific basis/marks when quantities are positive. The independent statement value is statementNav; navOverride remains a separate manual field. If statement NAV is absent, status is UNRECONCILED_NO_STATEMENT.
- Accounting convention: cashBalance is the account cash balance and is assumed to already include posted short-sale proceeds and option credits; those flows are not added again. The broker statement must confirm this convention before production use.
- Zero slippage and zero commission are valid and remain zero. Missing or negative costs block.
- Joint stress has no fixed $420 fallback. Active option holdings require a valid candidate and explicit maximum-expiry loss.
- State bundle includes the full source store, inputs and all three parameter groups. Import verifies full sourceHash, scenarioHash, embedded engineOutputHash, then independently recomputes the engine output before exposing staged state. UI state is committed only after verification.
- Thirty-five Golden Tests use clearly labeled TEST_ONLY arithmetic fixtures. They are not historical market data and are not performance evidence.

## Provenance and integrity boundaries

SHA-256 detects a change relative to a previously trusted hash; it is not a digital signature and cannot establish that an uploaded file genuinely came from an exchange/vendor. Current import status is UNAUTHENTICATED_UPLOAD. To promote a source to an authenticated research dataset, add an independently verified source URL/export identity, retrieval evidence and a separately pinned source hash, then audit rows and coverage.

The historical price-drop function measures underlying-price-path drop frequency by imported observation count. It is not option-strategy win rate, a forecast probability, or a substitute for option-chain replay. Missing trading sessions can distort a row-count horizon.

## Integration still required

The source conversation referenced a Canvas/V4.2 HTML file, but that full HTML source was not present in the current repository tree available to this change. This module is intentionally isolated; no guessed DOM IDs, Canvas state, app screens, or live settings have been overwritten. To wire it into that HTML, connect the real UI adapter to buildFullStateBundle, verifyAndStageFullStateBundle and restoreFullStateBundle, then run browser-level tests against the actual HTML asset.
