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

## Key Results (2020–2026)

| Metric | Value |
|--------|-------|
| Capital base | Rs 5,00,000 |
| Net P/L | Rs 3,30,944 |
| CAGR | 7.04% |
| Traded days | 1,312 |
| Skipped days | 539 |
| Win days | 604 |
| Loss days | 708 |
| Win rate | 46.0% |
| Max drawdown | Rs 5,68,615 |
| Best day | 2026-02-02 — Rs 1,72,606 |
| Worst day | 2020-03-20 — Rs −91,325 |

> **Note:** Despite positive CAGR, the win rate is below 50% — a few large wins
> offset many small losses. The max drawdown (Rs 5.7L) exceeds the capital base (Rs 5L),
> making this high-risk for standalone deployment. 2020 was deeply negative.

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
