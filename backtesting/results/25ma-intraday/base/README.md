# 25-MA Intraday — Base Strategy

## Overview

The baseline NIFTY 25-SMA weekly intraday trailing short-option strategy, 2020–2026.
Every trading day the 15-minute NIFTY spot is compared to its 25-period SMA; if spot
is above SMA sell ATM PE, if below sell ATM CE. A 5-minute trailing MA stop exits the
trade, with re-entry after the next 15-minute boundary. Closes any open position at 15:15.

## Files

| File | Description |
|------|-------------|
| `short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_trades.csv` | Trade-level records (one row per individual trade leg) |
| `short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_daywise.csv` | Day-level aggregate P&L |
| `short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_summary.md` | Full summary with yearly breakdown |
| `short_atm_nifty_ma_weekly_intraday_trailing_2020_2026.log` | Run log |

## Key Results (2020–2026)

> **Corrected 2026-09-08.** The trailing stop used to fill at the option open of
> the same 5-minute bar whose high/low triggered it — a price from before the
> stop existed. That single bug was the entire edge. See the
> [lookahead audit](../../../docs/lookahead-audit.md).

| Metric | Value | Was (pre-fix) |
|--------|-------|---------------|
| Capital base | Rs 10,00,000 | Rs 10,00,000 |
| Net P/L | −Rs 14,15,087 | Rs 67,11,939 |
| CAGR | −100% (wiped out) | 31.48% |
| Traded days | 1,578 | 1,578 |
| Skipped days | 273 | 273 |
| Total trades | 5,888 | 6,501 |
| Stop-loss exits | 4,673 | 5,257 |
| Day-close exits | 1,215 | 1,244 |
| Win days | 839 | 1,037 |
| Loss days | 739 | 541 |
| Win rate (day) | 53.2% | 65.7% |
| Max drawdown | Rs 19,86,026 | Rs 1,36,705 |
| Best day | 2024-06-04 — Rs 1,01,950 | 2024-06-04 — Rs 1,01,950 |
| Worst day | 2026-01-27 — Rs −77,166 | 2020-03-27 — Rs −58,885 |

Losses exceed the Rs 10L capital base, so CAGR floors at −100% rather than
returning the complex number the old formula produced.

## SL Exit Quality

Only **21.5%** of stop-loss exits are profitable. The pre-fix figure of 30.7% was
the bug's clearest fingerprint: filling at the triggering bar's open booked a
gain on stops that had actually moved against the position by the time they
could be acted on.

| SL type | Count | % | Was (pre-fix) |
|---------|-------|---|---------------|
| Profitable SL (stop locked in gain) | 1,004 | 21.5% | 1,616 / 30.7% |
| Loss-making SL | 3,669 | 78.5% | 3,641 / 69.3% |

## Streak Analysis

> Streaks computed at **day / trade level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 185 | 45.9% |
| 2 | 102 | 71.2% |
| 3 | 66 | 87.6% |
| 4 | 23 | 93.3% |
| 5 | 14 | 96.8% |
| 6 | 7 | 98.5% |
| 7-9 | 5 | 99.8% |
| 10+ | 1 | 100.0% |

_Longest streak: **10**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 221 | 54.7% |
| 2 | 109 | 81.7% |
| 3 | 39 | 91.3% |
| 4 | 14 | 94.8% |
| 5 | 12 | 97.8% |
| 6 | 5 | 99.0% |
| 7-9 | 3 | 99.8% |
| 10+ | 1 | 100.0% |

_Longest streak: **14**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 675 | 44.5% |
| 2 | 330 | 66.2% |
| 3 | 198 | 79.2% |
| 4 | 125 | 87.5% |
| 5 | 87 | 93.2% |
| 6 | 39 | 95.8% |
| 7-9 | 55 | 99.4% |
| 10+ | 9 | 100.0% |

_Longest streak: **16**_
