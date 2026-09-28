# V1.1 checkpoint status

The first V1.1 replay checkpoint is SUPERSEDED.

Reason: that checkpoint used simplified replay assumptions that did not fully match the original workspace source, including VXX short sizing and radar-weight / feature details.

Do not use the earlier V1.1 numbers as evidence.

Source-aligned checkpoint was subsequently recomputed directly from the original workspace source logic (policy.ts, radar.ts, book.ts, bs.ts, splits.ts, use-desk.ts):

- Source-policy replay, desk boot 2018-03-01: CAGR 12.7049%, daily MTM MaxDD -23.1837%, final NAV 276,508.11.
- Dynamic deployment overlay: CAGR 12.6828%, daily MTM MaxDD -23.6965%, final NAV 276,047.48.

Both remain DERIVED_BS_VIX replays, not OPRA historical fills.

Conclusion: the dynamic QQQ call deployment governor did not demonstrate incremental improvement under source-aligned reconstruction.
