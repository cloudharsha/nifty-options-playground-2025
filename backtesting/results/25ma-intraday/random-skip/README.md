# 25-MA Intraday — Random-Skip Variants

## Overview

Two sub-variants are stored here, both derived from the base strategy by adding
a random daily participation model (simulating a human trader who skips some days):

- **`trailing_random`** — default (09:30) entry time, no SL cap
- **`trailing_0920_random`** — entry pushed to 09:20 (falls back to 09:30 if no data), no SL cap

Each variant was run at skip rates of **30% / 40% / 50%** with **5 random seeds** each
= 30 trade-CSV files total (15 per sub-variant).

## Files

| Pattern | Count | Description |
|---------|-------|-------------|
| `*_random_skip(30, 40, 50)_run-4_trades.csv` | 15 | Old-entry-time random-skip trade records |
| `*_0920_random_skip(30, 40, 50)_run-4_trades.csv` | 15 | 09:20-entry random-skip trade records |
| `*_random_summary.md` | 1 | Aggregated summary for old-entry variant |
| `*_0920_random_summary.md` | 1 | Aggregated summary for 09:20 variant |
| `*.log` | 2 | Run logs |

> **Corrected 2026-09-08.** These runs previously carried lookahead: the trailing
> stop filled at the open of the very 5-minute bar that triggered it, and the
> 09:20 entry read a 15-minute bar that does not close until 09:30. Every figure
> below is post-fix. See the [lookahead audit](../../../docs/lookahead-audit.md).

## Key Results (averaged across all 30 runs)

Every skip rate is now a loss, in both entry variants. The 09:20 variant is far
worse than the 09:30 one because its entire signal was the ten-minute peek.

| Skip rate | 09:30 entry — Avg Net P/L | Avg CAGR | 09:20 entry — Avg Net P/L | Avg CAGR |
|-----------|--------------------------|----------|---------------------------|----------|
| 30% | −Rs 4,13,558 | −7.85% | −Rs 11,68,852 | −69.06% |
| 40% | −Rs 1,43,304 | −2.20% | −Rs 10,52,214 | −51.39% |
| 50% | −Rs 3,70,234 | −6.58% | −Rs 9,50,304 | −39.07% |

Pre-fix these read ~Rs 57–68L and ~28–32% at the 30% skip rate.

See the individual `*_summary.md` files for precise per-seed and per-skip-rate numbers.

## SL Exit Quality (pooled across all 30 runs)

| SL type | Count | % | Was (pre-fix) |
|---------|-------|---|---------------|
| Profitable SL (stop locked in gain) | 14,786 | 21.6% | 22,792 / 31.0% |
| Loss-making SL | 53,603 | 78.4% | 50,706 / 69.0% |

## Streak Analysis

> Streaks computed at **trade (pooled across 30 runs) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 11,814 | 59.6% |
| 2 | 4,398 | 81.7% |
| 3 | 2,022 | 91.9% |
| 4 | 936 | 96.7% |
| 5 | 363 | 98.5% |
| 6 | 159 | 99.3% |
| 7-9 | 132 | 100.0% |
| 10+ | 9 | 100.0% |

_Longest streak: **15**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 7,465 | 37.7% |
| 2 | 4,160 | 58.6% |
| 3 | 2,758 | 72.5% |
| 4 | 1,974 | 82.5% |
| 5 | 1,047 | 87.8% |
| 6 | 901 | 92.3% |
| 7-9 | 1,127 | 98.0% |
| 10+ | 395 | 100.0% |

_Longest streak: **23**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 7,802 | 39.2% |
| 2 | 4,265 | 60.6% |
| 3 | 2,829 | 74.8% |
| 4 | 1,880 | 84.2% |
| 5 | 992 | 89.2% |
| 6 | 846 | 93.4% |
| 7-9 | 1,013 | 98.5% |
| 10+ | 296 | 100.0% |

_Longest streak: **22**_
