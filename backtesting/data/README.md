# Reference data

Small reference series that a strategy needs and that cannot be derived from the
options or spot files. Unlike the ~11 GB of market data — which stays local, see
the [root README](../../README.md#data-layout) — these are a few tens of KB and
**are** versioned, so a run that depends on them stays reproducible.

## `india_vix_daily.csv`

Daily India VIX (NSE symbol `INDIAVIX`), OHLC, 2020-01-02 to 2026-09-08.

```csv
date,open,high,low,close
2020-01-02,11.6,11.7,10.73,11.49
```

- `date` is the trading date, `YYYY-MM-DD`, no timezone (it is a daily bar).
- Sessions with no print are absent rather than zero-filled; 1,638 rows.
- Sourced from the Yahoo Finance chart API for `^INDIAVIX` and reduced to daily
  OHLC. Spot-checked against the known extremes: 83.61 on 2020-03-24 (the COVID
  peak) and 9.15 on 2025-12-26.

Used by the Sleeve A adjusted straddle, whose entry rule skips a cycle when the
**previous** session's VIX close is below 12. Any strategy reading this file
should use the last session strictly before the entry date, never the entry
date's own close, which is not known at 09:20.
