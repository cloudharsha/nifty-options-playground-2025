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
| Net P/L | -Rs 14,15,087 |
| CAGR | -100.00% |
| Max Drawdown | Rs 19,86,026 |
| Capital base | Rs 10,00,000 |

## Simulation Results

| Skip Rate | Run | Seed | Traded Days | Rnd Skipped | Strat Skipped | Net P/L | CAGR | vs Baseline | Max DD | Win% | Avg Start |
|-----------|-----|------|-------------|-------------|---------------|---------|------|-------------|--------|------|-----------|
| 30% | 1 | 42 | 1131 | 542 | 178 | -Rs 308,602 | -4.82% | +95.2pp | Rs 823,918 | 53.5% | 12:15 |
| 30% | 2 | 137 | 1108 | 553 | 190 | -Rs 727,468 | -15.99% | +84.0pp | Rs 1,017,978 | 51.4% | 12:15 |
| 30% | 3 | 999 | 1083 | 579 | 189 | -Rs 622,370 | -12.23% | +87.8pp | Rs 945,097 | 51.5% | 12:15 |
| 30% | 4 | 2024 | 1084 | 582 | 185 | -Rs 112,419 | -1.59% | +98.4pp | Rs 475,676 | 54.6% | 12:15 |
| 30% | 5 | 31415 | 1106 | 541 | 204 | -Rs 296,931 | -4.61% | +95.4pp | Rs 668,955 | 53.9% | 12:15 |
| 40% | 1 | 42 | 955 | 741 | 155 | -Rs 91,866 | -1.28% | +98.7pp | Rs 567,990 | 54.8% | 12:15 |
| 40% | 2 | 137 | 942 | 755 | 154 | -Rs 71,061 | -0.98% | +99.0pp | Rs 376,780 | 52.9% | 12:15 |
| 40% | 3 | 999 | 909 | 783 | 159 | -Rs 92,011 | -1.28% | +98.7pp | Rs 681,625 | 53.6% | 12:15 |
| 40% | 4 | 2024 | 951 | 740 | 160 | -Rs 60,743 | -0.84% | +99.2pp | Rs 609,046 | 54.9% | 12:15 |
| 40% | 5 | 31415 | 976 | 712 | 163 | -Rs 400,841 | -6.63% | +93.4pp | Rs 701,400 | 51.1% | 12:15 |
| 50% | 1 | 42 | 795 | 919 | 137 | -Rs 33,660 | -0.46% | +99.5pp | Rs 364,902 | 54.7% | 12:15 |
| 50% | 2 | 137 | 770 | 946 | 135 | -Rs 608,876 | -11.82% | +88.2pp | Rs 1,010,466 | 50.9% | 12:15 |
| 50% | 3 | 999 | 741 | 976 | 134 | -Rs 301,730 | -4.70% | +95.3pp | Rs 525,860 | 53.8% | 12:15 |
| 50% | 4 | 2024 | 786 | 935 | 130 | -Rs 351,821 | -5.64% | +94.4pp | Rs 625,336 | 54.1% | 12:15 |
| 50% | 5 | 31415 | 809 | 907 | 135 | -Rs 555,085 | -10.28% | +89.7pp | Rs 791,096 | 49.8% | 12:15 |

## Aggregated by Skip Rate (across 5 runs)

| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days |
|-----------|-------------|----------|----------|----------|------------|----------|-----------------|
| 30% | -Rs 413,558 | -7.85% | -15.99% | -1.59% | Rs 786,325 | 53.0% | 1102 |
| 40% | -Rs 143,304 | -2.20% | -6.63% | -0.84% | Rs 587,368 | 53.4% | 947 |
| 50% | -Rs 370,234 | -6.58% | -11.82% | -0.46% | Rs 663,532 | 52.7% | 780 |

## Notes

- CAGR is computed on Rs 10,00,000 capital over the full data range (same as baseline).
- 'Rnd Skipped' = days the random model chose not to participate.
- 'Strat Skipped' = days participated but no trade completed (data gaps, no signal, etc.).
- 'Avg Start' ≈ average time of day the trader began looking for entries on active days.
- All trade mechanics (MA filter, trailing stop, re-entry, slippage, brokerage) are unchanged.
