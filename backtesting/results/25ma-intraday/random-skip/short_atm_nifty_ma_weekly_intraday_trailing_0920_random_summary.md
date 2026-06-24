# 09:20-Start Random-Skip Backtest — Short ATM NIFTY MA Weekly Intraday Trailing

## Strategy changes vs baseline

- **Entry start**: 09:20 (vs 09:30 in baseline); if no option data at 09:20,
  falls through to the standard 09:30 slot automatically
- **Signal at 09:20**: uses the 09:15 15m bar (same bar the 09:30 entry uses)
- **Day skipping**: random at 30% / 40% / 50% (5 runs each, 15 total)
- **Exit logic**: unchanged — trailing 25-SMA stop on 5m candles, or EOD 15:15
- **Re-entry after stop**: next 15m boundary (unchanged)
- **Seeds**: [42, 137, 999, 2024, 31415]

## Baseline (full participation, 09:30 start)

| Metric | Value |
|--------|-------|
| Net P/L | Rs 67,11,939 |
| CAGR | 31.48% |
| Max Drawdown | Rs 1,36,705 |
| Capital base | Rs 10,00,000 |

## Simulation Results

| Skip | Run | Seed | Traded Days | Rnd Skip | Strat Skip | Net P/L | CAGR | vs Base | Max DD | Win% | Max SL/Day | Max SL Overall |
|------|-----|------|-------------|----------|------------|---------|------|---------|--------|------|------------|----------------|
| 30% | 1 | 42 | 1137 | 533 | 181 | Rs 7,068,908 | 32.28% | 102.5% | Rs 157,845 | 69.0% | 16 | 29 |
| 30% | 2 | 137 | 1099 | 560 | 192 | Rs 7,041,940 | 32.22% | 102.4% | Rs 110,325 | 69.9% | 16 | 29 |
| 30% | 3 | 999 | 1056 | 611 | 184 | Rs 6,388,348 | 30.73% | 97.6% | Rs 98,245 | 68.6% | 16 | 25 |
| 30% | 4 | 2024 | 1123 | 536 | 192 | Rs 6,760,458 | 31.59% | 100.4% | Rs 111,560 | 68.8% | 16 | 25 |
| 30% | 5 | 31415 | 1099 | 560 | 192 | Rs 6,841,987 | 31.78% | 100.9% | Rs 93,520 | 69.6% | 16 | 27 |
| 40% | 1 | 42 | 980 | 709 | 162 | Rs 6,278,184 | 30.47% | 96.8% | Rs 155,315 | 69.9% | 16 | 27 |
| 40% | 2 | 137 | 921 | 766 | 164 | Rs 5,644,954 | 28.89% | 91.8% | Rs 98,565 | 69.3% | 16 | 29 |
| 40% | 3 | 999 | 917 | 778 | 156 | Rs 5,396,900 | 28.23% | 89.7% | Rs 112,210 | 68.0% | 16 | 23 |
| 40% | 4 | 2024 | 963 | 731 | 157 | Rs 5,667,820 | 28.94% | 91.9% | Rs 114,410 | 68.8% | 16 | 25 |
| 40% | 5 | 31415 | 941 | 751 | 159 | Rs 5,946,932 | 29.66% | 94.2% | Rs 70,945 | 69.8% | 16 | 25 |
| 50% | 1 | 42 | 819 | 896 | 136 | Rs 5,181,488 | 27.64% | 87.8% | Rs 154,090 | 68.9% | 16 | 27 |
| 50% | 2 | 137 | 770 | 937 | 144 | Rs 4,478,144 | 25.59% | 81.3% | Rs 98,565 | 69.2% | 16 | 32 |
| 50% | 3 | 999 | 747 | 973 | 131 | Rs 4,580,999 | 25.91% | 82.3% | Rs 89,025 | 68.9% | 15 | 30 |
| 50% | 4 | 2024 | 807 | 918 | 126 | Rs 4,733,825 | 26.36% | 83.7% | Rs 95,215 | 69.0% | 15 | 24 |
| 50% | 5 | 31415 | 780 | 941 | 130 | Rs 4,895,559 | 26.84% | 85.2% | Rs 88,970 | 70.0% | 16 | 25 |

## Aggregated by Skip Rate (5 runs each)

| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days | Avg Max SL/Day | Avg Max SL Overall |
|-----------|-------------|----------|----------|----------|------------|----------|-----------------|----------------|---------------------|
| 30% | Rs 6,820,328 | 31.72% | 30.73% | 32.28% | Rs 114,299 | 69.2% | 1103 | 16.0 | 27.0 |
| 40% | Rs 5,786,958 | 29.24% | 28.23% | 30.47% | Rs 110,289 | 69.2% | 944 | 16.0 | 25.8 |
| 50% | Rs 4,774,003 | 26.47% | 25.59% | 27.64% | Rs 105,173 | 69.2% | 785 | 15.6 | 27.6 |

## SL Streak Detail

| Skip | Run | Max SL in a Single Day | Max SL Streak (All Trades) | Total Stop Exits | Total Trades |
|------|-----|------------------------|----------------------------|------------------|--------------|
| 30% | 1 | 16 | 29 | 3727 | 4633 |
| 30% | 2 | 16 | 29 | 3602 | 4471 |
| 30% | 3 | 16 | 25 | 3569 | 4401 |
| 30% | 4 | 16 | 25 | 3825 | 4711 |
| 30% | 5 | 16 | 27 | 3595 | 4469 |
| 40% | 1 | 16 | 27 | 3164 | 3952 |
| 40% | 2 | 16 | 29 | 3088 | 3825 |
| 40% | 3 | 16 | 23 | 3148 | 3876 |
| 40% | 4 | 16 | 25 | 3258 | 4022 |
| 40% | 5 | 16 | 25 | 3075 | 3820 |
| 50% | 1 | 16 | 27 | 2708 | 3359 |
| 50% | 2 | 16 | 32 | 2595 | 3218 |
| 50% | 3 | 15 | 30 | 2486 | 3084 |
| 50% | 4 | 15 | 24 | 2767 | 3406 |
| 50% | 5 | 16 | 25 | 2567 | 3183 |

## Notes

- **Max SL/Day**: worst single-day streak of consecutive stop-loss exits (within one day).
- **Max SL Overall**: longest consecutive SL streak across all trades in the backtest, ignoring day boundaries.
- CAGR computed on Rs 10,00,000 capital over the full data range (same as baseline).
- 'Rnd Skip' = days the random model chose not to participate.
- 'Strat Skip' = days participated but no trade completed (data gaps, no signal, etc.).
- At 09:20 the option data is sparse; most days the effective first entry falls at 09:30.
