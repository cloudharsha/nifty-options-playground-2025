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

> **Corrected 2026-09-08.** These runs previously carried lookahead: the trailing
> stop filled at the open of the very 5-minute bar that triggered it, and the
> 09:20 entry read a 15-minute bar that does not close until 09:30. Every figure
> below is post-fix. See the [lookahead audit](../../../docs/lookahead-audit.md).

## Key Results (30% skip, averaged across 5 seeds)

| Gap threshold | Avg Net P/L | Avg CAGR | Max DD | Was (pre-fix) |
|--------------|-------------|----------|--------|---------------|
| 75 pts | −Rs 1,19,994 | −2.27% | Rs 6,31,263 | Rs 32,23,660 / 21.26% |
| 100 pts | −Rs 2,04,727 | −3.87% | Rs 7,80,258 | Rs 36,49,025 / 22.83% |
| 125 pts | −Rs 3,24,239 | −6.48% | Rs 8,58,006 | Rs 39,54,349 / 23.88% |
| 150 pts | −Rs 3,13,403 | −6.38% | Rs 9,23,108 | Rs 42,92,189 / 24.99% |

The ordering inverts after the fix: the *tightest* filter is now the least-bad,
because trading less of this signal costs less. None reach break-even.
See `*_magap_summary.md` for the full 40%/50% skip-rate breakdown.

## SL Exit Quality (pooled across all 60 runs)

| SL type | Count | % | Was (pre-fix) |
|---------|-------|---|---------------|
| Profitable SL (trailing stop locked in gain) | 24,453 | 29.8% | 30,497 / 39.0% |
| Loss-making SL | 57,739 | 70.2% | 47,789 / 61.0% |

## Streak Analysis

> Streaks computed at **trade (pooled across 60 runs) level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 13,626 | 57.0% |
| 2 | 5,698 | 80.8% |
| 3 | 2,463 | 91.1% |
| 4 | 1,157 | 96.0% |
| 5 | 571 | 98.3% |
| 6 | 182 | 99.1% |
| 7-9 | 204 | 100.0% |
| 10+ | 10 | 100.0% |

_Longest streak: **13**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 9,172 | 38.3% |
| 2 | 6,160 | 64.0% |
| 3 | 3,533 | 78.8% |
| 4 | 2,266 | 88.3% |
| 5 | 1,186 | 93.2% |
| 6 | 841 | 96.7% |
| 7-9 | 621 | 99.3% |
| 10+ | 160 | 100.0% |

_Longest streak: **20**_

### Consecutive Loss-Making SL Exits (trade-level)

> A trailing-stop SL exit can be *profitable* (the stop locked in gains) — this table counts only the SL exits that closed at a net loss.

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 9,542 | 39.7% |
| 2 | 6,111 | 65.2% |
| 3 | 3,471 | 79.6% |
| 4 | 2,208 | 88.8% |
| 5 | 1,144 | 93.6% |
| 6 | 794 | 96.9% |
| 7-9 | 597 | 99.4% |
| 10+ | 149 | 100.0% |

_Longest streak: **20**_
