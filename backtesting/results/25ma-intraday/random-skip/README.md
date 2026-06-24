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

## Key Results (averaged across all 30 runs)

| Skip rate | Avg Net P/L | Avg CAGR |
|-----------|-------------|----------|
| 30% | ~Rs 57–68L | ~28–32% |
| 40% | ~Rs 48–58L | ~26–29% |
| 50% | ~Rs 40–48L | ~24–26% |

See the individual `*_summary.md` files for precise per-seed and per-skip-rate numbers.

## SL Exit Quality (pooled across all 30 runs)

| SL type | Count | % |
|---------|-------|---|
| Profitable SL (stop locked in gain) | 22,792 | 31.0% |
| Loss-making SL | 50,706 | 69.0% |

## Streak Analysis

> Streaks computed at **trade (pooled across 30 runs) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 11,503 | 52.1% |
| 2 | 5,225 | 75.7% |
| 3 | 2,816 | 88.5% |
| 4 | 1,364 | 94.7% |
| 5 | 591 | 97.3% |
| 6 | 314 | 98.8% |
| 7-9 | 239 | 99.8% |
| 10+ | 37 | 100.0% |

_Longest streak: **15**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 9,430 | 42.7% |
| 2 | 5,256 | 66.5% |
| 3 | 3,092 | 80.5% |
| 4 | 1,730 | 88.3% |
| 5 | 1,036 | 93.0% |
| 6 | 576 | 95.6% |
| 7-9 | 808 | 99.3% |
| 10+ | 154 | 100.0% |

_Longest streak: **19**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 9,680 | 44.2% |
| 2 | 5,179 | 67.9% |
| 3 | 3,097 | 82.0% |
| 4 | 1,603 | 89.3% |
| 5 | 1,010 | 94.0% |
| 6 | 540 | 96.4% |
| 7-9 | 671 | 99.5% |
| 10+ | 113 | 100.0% |

_Longest streak: **16**_
