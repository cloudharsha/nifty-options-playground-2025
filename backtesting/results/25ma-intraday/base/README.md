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

| Metric | Value |
|--------|-------|
| Capital base | Rs 10,00,000 |
| Net P/L | Rs 67,11,939 |
| CAGR | 31.48% |
| Traded days | 1,578 |
| Skipped days | 273 |
| Total trades | 6,501 |
| Stop-loss exits | 5,257 |
| Day-close exits | 1,244 |
| Win days | 1,037 |
| Loss days | 541 |
| Win rate (day) | 65.7% |
| Max drawdown | Rs 1,36,705 |
| Best day | 2024-06-04 — Rs 1,01,950 |
| Worst day | 2020-03-27 — Rs −58,885 |

## SL Exit Quality

Of all stop-loss exits, **40%+ are profitable** — the trailing MA stop fires while the
trade is still in profit, locking in gains. Only the remaining ~60% are true losses.

| SL type | Count | % |
|---------|-------|---|
| Profitable SL (stop locked in gain) | 1,616 | 30.7% |
| Loss-making SL | 3,641 | 69.3% |

## Streak Analysis

> Streaks computed at **day / trade level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 111 | 30.8% |
| 2 | 95 | 57.2% |
| 3 | 66 | 75.6% |
| 4 | 28 | 83.3% |
| 5 | 19 | 88.6% |
| 6 | 13 | 92.2% |
| 7-9 | 18 | 97.2% |
| 10+ | 10 | 100.0% |

_Longest streak: **13**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 243 | 67.5% |
| 2 | 77 | 88.9% |
| 3 | 28 | 96.7% |
| 4 | 6 | 98.3% |
| 5 | 4 | 99.4% |
| 6 | 1 | 99.7% |
| 10+ | 1 | 100.0% |

_Longest streak: **10**_

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
