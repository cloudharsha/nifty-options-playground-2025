# 25-MA Intraday — With MA Gap Filter

## Overview

Extends the 2-SL-cap strategy with an **MA gap filter**: skip the day's entry if the
absolute distance between NIFTY spot close and its 25-SMA exceeds a threshold.
The idea is to avoid entering when price is already far from the MA (mean-reversion risk).

Tested across **4 gap thresholds** (75 / 100 / 125 / 150 pts) × **3 skip rates**
(30% / 40% / 50%) × **5 seeds** = **60 files**.

## Files

| Pattern | Count | Description |
|---------|-------|-------------|
| `*_magap_gap(75, 100, 125, 150)_skip(30, 40, 50)_run-4_trades.csv` | 60 | Trade records |
| `*_magap_gap(75, 100, 125, 150)_skip(30, 40, 50)_run-4_daywise.csv` | 60 | Day aggregates |
| `*_magap_summary.md` | 1 | Full summary across all gap/skip combinations |
| `*_magap.log` | 1 | Run log |

## Key Results (30% skip, averaged across 5 seeds)

| Gap threshold | Avg Net P/L | Avg CAGR | Max DD |
|--------------|-------------|----------|--------|
| 75 pts | Rs 32,23,660 | 21.26% | Rs 1,00,874 |
| 100 pts | Rs 36,49,025 | 22.83% | Rs 1,21,120 |
| 125 pts | Rs 39,54,349 | 23.88% | Rs 1,40,008 |
| 150 pts | Rs 42,92,189 | 24.99% | Rs 1,42,824 |

Tighter MA gap filter = fewer trades, lower CAGR, but also meaningfully lower drawdown.
See `*_magap_summary.md` for the full 40%/50% skip-rate breakdown.

## SL Exit Quality (pooled across all 60 runs)

| SL type | Count | % |
|---------|-------|---|
| Profitable SL (trailing stop locked in gain) | 30,497 | 39.0% |
| Loss-making SL | 47,789 | 61.0% |

## Streak Analysis

> Streaks computed at **trade (pooled across 60 runs) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 11,382 | 47.4% |
| 2 | 6,270 | 73.6% |
| 3 | 3,360 | 87.6% |
| 4 | 1,654 | 94.5% |
| 5 | 624 | 97.1% |
| 6 | 362 | 98.6% |
| 7-9 | 294 | 99.8% |
| 10+ | 50 | 100.0% |

_Longest streak: **17**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 11,762 | 49.0% |
| 2 | 5,861 | 73.4% |
| 3 | 3,098 | 86.3% |
| 4 | 1,768 | 93.6% |
| 5 | 759 | 96.8% |
| 6 | 479 | 98.8% |
| 7-9 | 242 | 99.8% |
| 10+ | 51 | 100.0% |

_Longest streak: **19**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 11,687 | 49.3% |
| 2 | 5,942 | 74.3% |
| 3 | 2,973 | 86.9% |
| 4 | 1,726 | 94.1% |
| 5 | 691 | 97.0% |
| 6 | 430 | 98.9% |
| 7-9 | 221 | 99.8% |
| 10+ | 51 | 100.0% |

_Longest streak: **19**_
