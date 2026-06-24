# 25-MA Overnight — Short Offset Variants

## Overview

Sells OTM or ITM options overnight using the NIFTY 25-SMA direction signal at 15:15.
Entry at 15:29, exit next trading day 09:16. The strike is offset from ATM:
- **OTM** variants sell deeper out-of-the-money (lower premium, lower risk)
- **ITM** variants sell in-the-money (higher premium, higher delta exposure)

Eight offset distances are stored in a single daywise CSV, distinguished by `range_label`.

## Files

| File | Description |
|------|-------------|
| `short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_daywise.csv` | All 8 variants in one file (filter by `range_label`) |
| `short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md` | Full per-variant summary |
| `short_atm_nifty_ma_weekly_overnight_offsets_2020_2026.log` | Run log |

## Range Comparison (2020–2026, Rs 10L capital)

| Range | Traded | Win% | Net P/L | CAGR | Max DD |
|-------|--------|------|---------|------|--------|
| ITM_300 | 1,180 | 53.2% | Rs 26,53,098 | 18.96% | Rs 2,96,200 |
| ITM_200 | 1,274 | 53.5% | Rs 27,36,233 | 19.32% | Rs 2,70,220 |
| ITM_100 | 1,307 | 53.9% | Rs 23,08,668 | 17.39% | Rs 2,28,640 |
| OTM_100 | 1,313 | 57.9% | Rs 11,72,399 | 10.95% | Rs 2,98,630 |
| OTM_200 | 1,311 | 55.7% | Rs 7,36,394 | 7.67% | Rs 2,70,775 |
| OTM_300 | 1,312 | 49.8% | Rs 4,45,963 | 5.07% | Rs 2,05,310 |
| OTM_400 | 1,311 | 42.8% | Rs 1,85,151 | 2.30% | Rs 2,06,510 |
| OTM_500 | 1,303 | 33.5% | Rs −86,223 | −1.20% | Rs 3,49,702 |

ITM variants outperform OTM on raw CAGR. OTM_100 has the best win rate but lower P/L.

## Streak Summary by Range

| Range | Max Win Streak | Max Loss Streak |
|-------|---------------|-----------------|
| ITM_100 | 8 | 7 |
| ITM_200 | 8 | 7 |
| ITM_300 | 8 | 7 |
| OTM_100 | 8 | 7 |
| OTM_200 | 12 | 7 |
| OTM_300 | 10 | 12 |
| OTM_400 | 10 | 15 |
| OTM_500 | 10 | 30 |

## Per-Range Streak Detail

### ITM_100

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 143 | 43.1% |
| 2 | 88 | 69.6% |
| 3 | 54 | 85.8% |
| 4 | 26 | 93.7% |
| 5 | 14 | 97.9% |
| 6 | 2 | 98.5% |
| 7-9 | 5 | 100.0% |

_Longest streak: **8**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 191 | 57.5% |
| 2 | 67 | 77.7% |
| 3 | 41 | 90.1% |
| 4 | 19 | 95.8% |
| 5 | 7 | 97.9% |
| 6 | 6 | 99.7% |
| 7-9 | 1 | 100.0% |

_Longest streak: **7**_

### ITM_200

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 134 | 42.0% |
| 2 | 86 | 69.0% |
| 3 | 56 | 86.5% |
| 4 | 22 | 93.4% |
| 5 | 14 | 97.8% |
| 6 | 2 | 98.4% |
| 7-9 | 5 | 100.0% |

_Longest streak: **8**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 176 | 55.2% |
| 2 | 73 | 78.1% |
| 3 | 35 | 89.0% |
| 4 | 17 | 94.4% |
| 5 | 11 | 97.8% |
| 6 | 6 | 99.7% |
| 7-9 | 1 | 100.0% |

_Longest streak: **7**_

### ITM_300

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 132 | 43.9% |
| 2 | 84 | 71.8% |
| 3 | 44 | 86.4% |
| 4 | 22 | 93.7% |
| 5 | 12 | 97.7% |
| 6 | 4 | 99.0% |
| 7-9 | 3 | 100.0% |

_Longest streak: **8**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 170 | 56.5% |
| 2 | 65 | 78.1% |
| 3 | 37 | 90.4% |
| 4 | 15 | 95.3% |
| 5 | 4 | 96.7% |
| 6 | 9 | 99.7% |
| 7-9 | 1 | 100.0% |

_Longest streak: **7**_

### OTM_100

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 131 | 39.3% |
| 2 | 91 | 66.7% |
| 3 | 57 | 83.8% |
| 4 | 23 | 90.7% |
| 5 | 16 | 95.5% |
| 6 | 5 | 97.0% |
| 7-9 | 10 | 100.0% |

_Longest streak: **8**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 201 | 60.5% |
| 2 | 73 | 82.5% |
| 3 | 37 | 93.7% |
| 4 | 14 | 97.9% |
| 5 | 4 | 99.1% |
| 6 | 2 | 99.7% |
| 7-9 | 1 | 100.0% |

_Longest streak: **7**_

### OTM_200

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 144 | 44.2% |
| 2 | 81 | 69.0% |
| 3 | 47 | 83.4% |
| 4 | 22 | 90.2% |
| 5 | 12 | 93.9% |
| 6 | 13 | 97.9% |
| 7-9 | 6 | 99.7% |
| 10+ | 1 | 100.0% |

_Longest streak: **12**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 179 | 54.9% |
| 2 | 81 | 79.8% |
| 3 | 41 | 92.3% |
| 4 | 13 | 96.3% |
| 5 | 9 | 99.1% |
| 6 | 1 | 99.4% |
| 7-9 | 2 | 100.0% |

_Longest streak: **7**_

### OTM_300

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 151 | 49.2% |
| 2 | 68 | 71.3% |
| 3 | 37 | 83.4% |
| 4 | 25 | 91.5% |
| 5 | 12 | 95.4% |
| 6 | 9 | 98.4% |
| 7-9 | 3 | 99.3% |
| 10+ | 2 | 100.0% |

_Longest streak: **10**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 156 | 50.8% |
| 2 | 69 | 73.3% |
| 3 | 42 | 87.0% |
| 4 | 13 | 91.2% |
| 5 | 11 | 94.8% |
| 6 | 5 | 96.4% |
| 7-9 | 6 | 98.4% |
| 10+ | 5 | 100.0% |

_Longest streak: **12**_

### OTM_400

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 150 | 52.8% |
| 2 | 63 | 75.0% |
| 3 | 36 | 87.7% |
| 4 | 15 | 93.0% |
| 5 | 10 | 96.5% |
| 6 | 7 | 98.9% |
| 7-9 | 2 | 99.6% |
| 10+ | 1 | 100.0% |

_Longest streak: **10**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 131 | 46.1% |
| 2 | 66 | 69.4% |
| 3 | 32 | 80.6% |
| 4 | 19 | 87.3% |
| 5 | 9 | 90.5% |
| 6 | 3 | 91.5% |
| 7-9 | 8 | 94.4% |
| 10+ | 16 | 100.0% |

_Longest streak: **15**_

### OTM_500

## Streak Analysis

> Streaks computed at **day level** across all traded records.
> A streak ends as soon as the sequence is broken by an opposite result or a skip day (for day-level).

### Consecutive Profitable Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 151 | 59.7% |
| 2 | 58 | 82.6% |
| 3 | 25 | 92.5% |
| 4 | 11 | 96.8% |
| 5 | 5 | 98.8% |
| 6 | 1 | 99.2% |
| 10+ | 2 | 100.0% |

_Longest streak: **10**_

### Consecutive Losing Days / Trades

| Streak | Count | Cumul % |
|--------|-------|---------|
| 1 | 94 | 37.2% |
| 2 | 54 | 58.5% |
| 3 | 36 | 72.7% |
| 4 | 24 | 82.2% |
| 5 | 12 | 87.0% |
| 6 | 4 | 88.5% |
| 7-9 | 10 | 92.5% |
| 10+ | 19 | 100.0% |

_Longest streak: **30**_
