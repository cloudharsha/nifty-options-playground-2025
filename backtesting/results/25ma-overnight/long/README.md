# 25-MA Overnight — Long ATM Weekly

## Overview

Buys the ATM option overnight based on the NIFTY 25-SMA direction at 15:15. Entry at
15:29 (option open), exit the next trading day at 09:16 (option open). Direction: above
SMA buy CE, below SMA buy PE. A pure long-premium overnight directional play.

## Files

| File | Description |
|------|-------------|
| `long_atm_nifty_ma_weekly_overnight_2020_2026_daywise.csv` | Day-level trade records |
| `long_atm_nifty_ma_weekly_overnight_2020_2026_summary.md` | Full summary with monthly breakdown |
| `long_atm_nifty_ma_weekly_overnight_2020_2026.log` | Run log |

> **Corrected 2026-09-08.** These runs took their direction from the 15:15
> 15-minute bar but entered at 15:29 — that bar does not close until 15:30, so
> the entry preceded its own signal. The signal bar is now 15:00, which closes
> at 15:15. Every figure below is post-fix; see the
> [lookahead audit](../../../docs/lookahead-audit.md).

## Key Results (2020–2026)

| Metric | Value | Was (pre-fix) |
|--------|-------|---------------|
| Capital base | Rs 5,00,000 | Rs 5,00,000 |
| Net P/L | −Rs 1,82,442 | Rs 3,30,944 |
| CAGR | −5.90% | 7.04% |
| Traded days | 1,310 | 1,312 |
| Skipped days | 541 | 539 |
| Win days | 589 | 604 |
| Loss days | 721 | 708 |
| Win rate | 45.0% | 46.0% |
| Max drawdown | Rs 7,39,380 | Rs 5,68,615 |

> **Note:** This variant flipped from profit to loss once the entry stopped
> preceding its own signal bar. The long side has always had a sub-50% win rate
> and depended on a few large wins; a one-minute peek at the close was enough to
> pick out enough of those to look profitable. Max drawdown (Rs 7.4L) now exceeds
> the Rs 5L capital base by half again.

## Streak Analysis

> Streaks computed at **day (each day = one overnight trade) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 170 | 50.6% |
| 2 | 98 | 79.8% |
| 3 | 48 | 94.0% |
| 4 | 12 | 97.6% |
| 5 | 5 | 99.1% |
| 6 | 1 | 99.4% |
| 7-9 | 2 | 100.0% |

_Longest streak: **8**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 170 | 50.6% |
| 2 | 64 | 69.6% |
| 3 | 45 | 83.0% |
| 4 | 29 | 91.7% |
| 5 | 15 | 96.1% |
| 6 | 7 | 98.2% |
| 7-9 | 6 | 100.0% |

_Longest streak: **7**_
