# 25-MA Intraday — With 2-SL/Day Cap

## Overview

Adds a **daily stop-loss cap** on top of the 09:20-entry random-skip strategy:
once 2 stop-loss exits occur in a single day, no further entries are taken that day.
This hard-caps intraday drawdown at the cost of missing potential afternoon recoveries.

Run at skip rates **30% / 40% / 50%** × **5 seeds** = **15 files**.

## Files

| Pattern | Count | Description |
|---------|-------|-------------|
| `*_2slcap_skip(30, 40, 50)_run-4_trades.csv` | 15 | Trade-level records |
| `*_2slcap_skip(30, 40, 50)_run-4_daywise.csv` | 15 | Day-level aggregates |
| `*_2slcap_summary.md` | 1 | Full aggregated summary with all skip rates |
| `*_2slcap.log` | 1 | Run log |

## Key Results

| Skip rate | Avg Net P/L | Avg CAGR | Avg Win% | Avg 2SL-Cap Days |
|-----------|-------------|----------|----------|-----------------|
| 30% | Rs 51,08,988 | 27.43% | 60.8% | 672 |
| 40% | Rs 43,62,600 | 25.21% | 60.7% | 578 |
| 50% | Rs 35,70,092 | 22.55% | 60.8% | 482 |

- **2SL-Cap Days** = days where trading was halted after 2 stop-losses (protects capital).
- vs baseline (no cap, no skip): Rs 67,11,939 / 31.48% CAGR.

## SL Exit Quality (pooled across all 15 runs)

The summary showed "Max SL Overall = 38" — that counts ALL consecutive SL exits including
profitable ones. Filtering to only loss-making SL exits gives the true drawdown picture below.

| SL type | Count | % |
|---------|-------|---|
| Profitable SL (trailing stop locked in gain) | 7,894 | 40.3% |
| Loss-making SL | 11,700 | 59.7% |

## Streak Analysis

> Streaks computed at **trade (pooled across 15 runs) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 2,652 | 44.4% |
| 2 | 1,593 | 71.0% |
| 3 | 845 | 85.2% |
| 4 | 448 | 92.7% |
| 5 | 198 | 96.0% |
| 6 | 125 | 98.1% |
| 7-9 | 93 | 99.6% |
| 10+ | 21 | 100.0% |

_Longest streak: **17**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 2,991 | 50.0% |
| 2 | 1,490 | 74.9% |
| 3 | 757 | 87.6% |
| 4 | 391 | 94.1% |
| 5 | 195 | 97.4% |
| 6 | 82 | 98.7% |
| 7-9 | 67 | 99.9% |
| 10+ | 8 | 100.0% |

_Longest streak: **15**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 2,961 | 49.9% |
| 2 | 1,515 | 75.4% |
| 3 | 746 | 88.0% |
| 4 | 389 | 94.5% |
| 5 | 180 | 97.6% |
| 6 | 80 | 98.9% |
| 7-9 | 57 | 99.9% |
| 10+ | 8 | 100.0% |

_Longest streak: **15**_
