# Random-Participation Backtest — Short ATM NIFTY MA Weekly Intraday Trailing

## Strategy (unchanged from baseline)

- Signal: NIFTY 25-SMA on 15-minute closes
- Entry window (when present): `09:30` through `15:00`
- Exit: `15:15` or trailing MA stop on 5-minute candles
- Direction: above SMA → short ATM PE; below SMA → short ATM CE
- Re-entry after stop: next 15-minute boundary

## Randomness Model

- **Day skip**: each trading day independently skipped with probability = skip_rate
- **Random start time**: on days the trader participates, the first entry attempt
  is at a uniformly random 15-minute boundary from 09:30 to 15:00
- Once a position is open, exit logic is **identical to baseline** (SL or EOD only)
- Seeds: [42, 137, 999, 2024, 31415]

## Baseline (full participation, always 09:30 start)

| Metric | Value |
|--------|-------|
| Net P/L | Rs 67,11,939 |
| CAGR | 31.48% |
| Max Drawdown | Rs 1,36,705 |
| Capital base | Rs 10,00,000 |

## Simulation Results

| Skip Rate | Run | Seed | Traded Days | Rnd Skipped | Strat Skipped | Net P/L | CAGR | vs Baseline | Max DD | Win% | Avg Start |
|-----------|-----|------|-------------|-------------|---------------|---------|------|-------------|--------|------|-----------|
| 30% | 1 | 42 | 1131 | 542 | 178 | Rs 2,817,144 | 19.66% | 62.4% | Rs 60,050 | 62.2% | 12:15 |
| 30% | 2 | 137 | 1108 | 553 | 190 | Rs 2,557,005 | 18.53% | 58.9% | Rs 102,220 | 62.1% | 12:15 |
| 30% | 3 | 999 | 1083 | 579 | 189 | Rs 2,540,560 | 18.46% | 58.6% | Rs 90,425 | 62.4% | 12:15 |
| 30% | 4 | 2024 | 1084 | 582 | 185 | Rs 2,824,737 | 19.69% | 62.6% | Rs 63,125 | 61.4% | 12:15 |
| 30% | 5 | 31415 | 1106 | 541 | 204 | Rs 2,773,722 | 19.48% | 61.9% | Rs 87,755 | 62.6% | 12:15 |
| 40% | 1 | 42 | 955 | 741 | 155 | Rs 2,408,472 | 17.86% | 56.7% | Rs 115,215 | 61.9% | 12:15 |
| 40% | 2 | 137 | 942 | 755 | 154 | Rs 2,734,790 | 19.31% | 61.3% | Rs 79,879 | 63.1% | 12:15 |
| 40% | 3 | 999 | 909 | 783 | 159 | Rs 2,281,194 | 17.26% | 54.8% | Rs 92,975 | 62.2% | 12:15 |
| 40% | 4 | 2024 | 952 | 740 | 159 | Rs 2,499,014 | 18.27% | 58.0% | Rs 82,448 | 62.0% | 12:15 |
| 40% | 5 | 31415 | 976 | 712 | 163 | Rs 2,350,892 | 17.59% | 55.9% | Rs 82,140 | 61.0% | 12:15 |
| 50% | 1 | 42 | 795 | 919 | 137 | Rs 2,124,493 | 16.49% | 52.4% | Rs 99,680 | 64.8% | 12:15 |
| 50% | 2 | 137 | 770 | 946 | 135 | Rs 1,732,101 | 14.42% | 45.8% | Rs 86,865 | 60.0% | 12:15 |
| 50% | 3 | 999 | 741 | 976 | 134 | Rs 1,611,922 | 13.73% | 43.6% | Rs 95,015 | 62.1% | 12:15 |
| 50% | 4 | 2024 | 786 | 935 | 130 | Rs 1,775,202 | 14.66% | 46.6% | Rs 73,635 | 63.1% | 12:15 |
| 50% | 5 | 31415 | 809 | 907 | 135 | Rs 1,566,390 | 13.46% | 42.8% | Rs 83,878 | 58.6% | 12:15 |

## Aggregated by Skip Rate (across 5 runs)

| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days |
|-----------|-------------|----------|----------|----------|------------|----------|-----------------|
| 30% | Rs 2,702,634 | 19.16% | 18.46% | 19.69% | Rs 80,715 | 62.2% | 1102 |
| 40% | Rs 2,454,872 | 18.06% | 17.26% | 19.31% | Rs 90,531 | 62.0% | 947 |
| 50% | Rs 1,762,022 | 14.55% | 13.46% | 16.49% | Rs 87,814 | 61.7% | 780 |

## Notes

- CAGR is computed on Rs 10,00,000 capital over the full data range (same as baseline).
- 'Rnd Skipped' = days the random model chose not to participate.
- 'Strat Skipped' = days participated but no trade completed (data gaps, no signal, etc.).
- 'Avg Start' ≈ average time of day the trader began looking for entries on active days.
- All trade mechanics (MA filter, trailing stop, re-entry, slippage, brokerage) are unchanged.
