# 25-MA Intraday — Same-Week Contract Variant

## Overview

Trades the **same-week expiry contract** (not the nearest upcoming weekly), using the
option's own 15-minute MA (not spot) as the trailing stop signal. Both CE and PE legs
are monitored independently from 09:30; whichever leg's option price dips below its
own 25-close SMA is sold first. Each leg trades at most once per day.

## Files

| File | Description |
|------|-------------|
| `short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_daywise.csv` | Day-level records |
| `short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_summary.md` | Full summary |
| `short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026.log` | Run log |

## Key Results (2020–2026)

| Metric | Value |
|--------|-------|
| Capital base | Rs 10,00,000 |
| Net P/L | Rs 1,39,007 |
| CAGR | 1.76% |
| Traded days | 1,315 |
| Skipped days | 536 |
| Win days | 711 |
| Loss days | 604 |
| Win rate | 54.1% |
| Max drawdown | Rs 6,38,220 |
| Best day | 2024-06-04 — Rs 1,01,950 |
| Worst day | 2025-05-27 — Rs −62,770 |

> **Note:** Despite a >54% win rate, the large max drawdown (Rs 6.4L on Rs 10L capital)
> and low CAGR (1.76%) indicate that the losing days are significantly larger than
> the winning days. This strategy deteriorated after 2022.

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 130 | 40.4% |
| 2 | 89 | 68.0% |
| 3 | 57 | 85.7% |
| 4 | 21 | 92.2% |
| 5 | 14 | 96.6% |
| 6 | 6 | 98.4% |
| 7-9 | 4 | 99.7% |
| 10+ | 1 | 100.0% |

_Longest streak: **10**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 176 | 54.8% |
| 2 | 67 | 75.7% |
| 3 | 42 | 88.8% |
| 4 | 22 | 95.6% |
| 5 | 9 | 98.4% |
| 6 | 2 | 99.1% |
| 7-9 | 3 | 100.0% |

_Longest streak: **8**_
