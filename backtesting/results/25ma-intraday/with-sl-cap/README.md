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

> **Corrected 2026-09-08.** These runs previously carried lookahead: the trailing
> stop filled at the open of the very 5-minute bar that triggered it, and the
> 09:20 entry read a 15-minute bar that does not close until 09:30. Every figure
> below is post-fix. See the [lookahead audit](../../../docs/lookahead-audit.md).

## Key Results

| Skip rate | Avg Net P/L | Avg CAGR | Avg Win% | Avg 2SL-Cap Days |
|-----------|-------------|----------|----------|-----------------|
| 30% | −Rs 2,05,723 | −3.63% | 47.9% | 684 |
| 40% | −Rs 2,16,528 | −3.77% | 47.5% | 589 |
| 50% | −Rs 2,69,926 | −4.40% | 47.4% | 493 |

Pre-fix: Rs 51,08,988 / 27.43%, Rs 43,62,600 / 25.21%, Rs 35,70,092 / 22.55%.
The 2-SL/day cap is the least-bad variant in the family — it stops trading early
on the worst days — but it still does not reach break-even.

- **2SL-Cap Days** = days where trading was halted after 2 stop-losses (protects capital).
- vs baseline (no cap, no skip): −Rs 14,15,087 / −100% CAGR (wiped out).

## SL Exit Quality (pooled across all 15 runs)

The summary showed "Max SL Overall = 38" — that counts ALL consecutive SL exits including
profitable ones. Filtering to only loss-making SL exits gives the true drawdown picture below.

| SL type | Count | % | Was (pre-fix) |
|---------|-------|---|---------------|
| Profitable SL (trailing stop locked in gain) | 6,147 | 29.8% | 7,894 / 40.3% |
| Loss-making SL | 14,497 | 70.2% | 11,700 / 59.7% |

## Streak Analysis

> Streaks computed at **trade (pooled across 15 runs) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 3,496 | 57.1% |
| 2 | 1,479 | 81.3% |
| 3 | 606 | 91.2% |
| 4 | 298 | 96.0% |
| 5 | 142 | 98.4% |
| 6 | 42 | 99.1% |
| 7-9 | 57 | 100.0% |
| 10+ | 1 | 100.0% |

_Longest streak: **11**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 2,413 | 39.4% |
| 2 | 1,619 | 65.8% |
| 3 | 846 | 79.6% |
| 4 | 561 | 88.8% |
| 5 | 310 | 93.8% |
| 6 | 193 | 97.0% |
| 7-9 | 154 | 99.5% |
| 10+ | 32 | 100.0% |

_Longest streak: **20**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 2,504 | 40.7% |
| 2 | 1,588 | 66.6% |
| 3 | 834 | 80.2% |
| 4 | 552 | 89.1% |
| 5 | 303 | 94.1% |
| 6 | 184 | 97.1% |
| 7-9 | 150 | 99.5% |
| 10+ | 30 | 100.0% |

_Longest streak: **20**_
