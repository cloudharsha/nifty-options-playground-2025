# 09:20-Start Random-Skip + 2-SL/Day Cap Backtest — Short ATM NIFTY MA Weekly Intraday Trailing

## Strategy changes vs baseline

- **Entry start**: 09:20 (vs 09:30 in baseline); falls through to 09:30 if no option data at 09:20
- **Signal at 09:20**: uses the 09:15 15m bar (same bar the 09:30 entry uses)
- **Day skipping**: random at 30% / 40% / 50% (5 runs each, 15 total)
- **Seeds**: [42, 137, 999, 2024, 31415]
- **Exit logic**: trailing 25-SMA stop on 5m candles, or EOD 15:15
- **Re-entry after stop**: next 15m boundary
- **NEW — Daily SL cap**: if stop-loss fires 2 times in a day, no further entries that day

## Baseline (full participation, 09:30 start, no SL cap)

| Metric | Value |
|--------|-------|
| Net P/L | Rs 6,711,939 |
| CAGR | 31.48% |
| Max Drawdown | Rs 136,705 |
| Capital base | Rs 10,00,000 |

## Simulation Results

| Skip | Run | Seed | Traded Days | Rnd Skip | Strat Skip | 2SL-Cap Days | Net P/L | CAGR | vs Base | Max DD | Win% | Max SL/Day | Max SL Overall |
|------|-----|------|-------------|----------|------------|-------------|---------|------|---------|--------|------|------------|----------------|
| 30% | 1 | 42 | 1137 | 533 | 181 | 696 | Rs 5,339,831 | 28.08% | 89.2% | Rs 161,115 | 61.1% | 2 | 32 |
| 30% | 2 | 137 | 1099 | 560 | 192 | 664 | Rs 5,270,888 | 27.89% | 88.6% | Rs 96,535 | 61.3% | 2 | 21 |
| 30% | 3 | 999 | 1056 | 611 | 184 | 648 | Rs 4,719,991 | 26.32% | 83.6% | Rs 101,360 | 59.1% | 2 | 31 |
| 30% | 4 | 2024 | 1123 | 536 | 192 | 699 | Rs 5,040,391 | 27.25% | 86.6% | Rs 103,355 | 60.2% | 2 | 38 |
| 30% | 5 | 31415 | 1099 | 560 | 192 | 653 | Rs 5,173,839 | 27.62% | 87.7% | Rs 120,100 | 62.2% | 2 | 27 |
| 40% | 1 | 42 | 980 | 709 | 162 | 594 | Rs 4,837,675 | 26.67% | 84.7% | Rs 146,740 | 61.9% | 2 | 37 |
| 40% | 2 | 137 | 921 | 766 | 164 | 562 | Rs 4,247,031 | 24.87% | 79.0% | Rs 70,580 | 61.0% | 2 | 21 |
| 40% | 3 | 999 | 917 | 778 | 156 | 567 | Rs 3,961,932 | 23.94% | 76.0% | Rs 112,320 | 58.3% | 2 | 27 |
| 40% | 4 | 2024 | 963 | 731 | 157 | 603 | Rs 4,242,378 | 24.86% | 79.0% | Rs 89,545 | 59.2% | 2 | 38 |
| 40% | 5 | 31415 | 941 | 751 | 159 | 564 | Rs 4,523,983 | 25.73% | 81.7% | Rs 111,915 | 62.9% | 2 | 22 |
| 50% | 1 | 42 | 819 | 896 | 136 | 505 | Rs 3,984,648 | 24.02% | 76.3% | Rs 149,140 | 62.0% | 2 | 33 |
| 50% | 2 | 137 | 770 | 937 | 144 | 478 | Rs 3,290,435 | 21.55% | 68.4% | Rs 70,831 | 60.5% | 2 | 27 |
| 50% | 3 | 999 | 747 | 973 | 131 | 457 | Rs 3,274,688 | 21.49% | 68.3% | Rs 80,940 | 58.9% | 2 | 33 |
| 50% | 4 | 2024 | 807 | 918 | 126 | 506 | Rs 3,511,774 | 22.37% | 71.1% | Rs 89,045 | 59.6% | 2 | 28 |
| 50% | 5 | 31415 | 780 | 941 | 130 | 466 | Rs 3,788,916 | 23.35% | 74.2% | Rs 137,470 | 62.9% | 2 | 23 |

## Aggregated by Skip Rate (5 runs each)

| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days | Avg 2SL-Cap Days | Avg Max SL/Day | Avg Max SL Overall |
|-----------|-------------|----------|----------|----------|------------|----------|-----------------|------------------|----------------|---------------------|
| 30% | Rs 5,108,988 | 27.43% | 26.32% | 28.08% | Rs 116,493 | 60.8% | 1103 | 672 | 2.0 | 29.8 |
| 40% | Rs 4,362,600 | 25.21% | 23.94% | 26.67% | Rs 106,220 | 60.7% | 944 | 578 | 2.0 | 29.0 |
| 50% | Rs 3,570,092 | 22.55% | 21.49% | 24.02% | Rs 105,485 | 60.8% | 785 | 482 | 2.0 | 28.8 |

## SL Streak Detail

| Skip | Run | Max SL in a Single Day | Max SL Streak (All Trades) | Total Stop Exits | Total Trades | 2SL-Cap Days |
|------|-----|------------------------|----------------------------|------------------|--------------|--------------|
| 30% | 1 | 2 | 32 | 1576 | 1986 | 696 |
| 30% | 2 | 2 | 21 | 1511 | 1913 | 664 |
| 30% | 3 | 2 | 31 | 1462 | 1841 | 648 |
| 30% | 4 | 2 | 38 | 1569 | 1967 | 699 |
| 30% | 5 | 2 | 27 | 1500 | 1912 | 653 |
| 40% | 1 | 2 | 37 | 1349 | 1708 | 594 |
| 40% | 2 | 2 | 21 | 1271 | 1606 | 562 |
| 40% | 3 | 2 | 27 | 1281 | 1610 | 567 |
| 40% | 4 | 2 | 38 | 1348 | 1688 | 603 |
| 40% | 5 | 2 | 22 | 1290 | 1637 | 564 |
| 50% | 1 | 2 | 33 | 1140 | 1430 | 505 |
| 50% | 2 | 2 | 27 | 1073 | 1346 | 478 |
| 50% | 3 | 2 | 33 | 1029 | 1301 | 457 |
| 50% | 4 | 2 | 28 | 1130 | 1412 | 506 |
| 50% | 5 | 2 | 23 | 1065 | 1354 | 466 |

## Notes

- **2-SL/Day Cap**: once 2 stop-loss exits occur on the same day, no further entries are taken that day.
- **2SL-Cap Days**: number of days where the cap was triggered (trading halted before EOD due to 2 SL hits).
- **Max SL/Day**: worst single-day streak of consecutive stop-loss exits (within one day).
- **Max SL Overall**: longest consecutive SL streak across all trades in the backtest, ignoring day boundaries.
- CAGR computed on Rs 10,00,000 capital over the full data range (same as baseline).
- 'Rnd Skip' = days the random model chose not to participate.
- 'Strat Skip' = days participated but no trade completed (data gaps, no signal, etc.).
- At 09:20 the option data is sparse; most days the effective first entry falls at 09:30.
