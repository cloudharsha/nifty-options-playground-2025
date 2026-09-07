# 09:20-Start Random-Skip Backtest — Short ATM NIFTY MA Weekly Intraday Trailing

## Strategy changes vs baseline

- **Entry start**: 09:20 (vs 09:30 in baseline); if no option data at 09:20,
  falls through to the standard 09:30 slot automatically
- **Signal at 09:20**: uses the previous session's 15:15 bar - the newest 15m
  candle closed by 09:20. ATM strike comes from the 09:15 5m bar close.
- **Day skipping**: random at 30% / 40% / 50% (5 runs each, 15 total)
- **Exit logic**: unchanged — trailing 25-SMA stop on 5m candles, or EOD 15:15
- **Re-entry after stop**: next 15m boundary (unchanged)
- **Seeds**: [42, 137, 999, 2024, 31415]

## Baseline (full participation, 09:30 start)

| Metric | Value |
|--------|-------|
| Net P/L | -Rs 14,15,087 |
| CAGR | -100.00% |
| Max Drawdown | Rs 19,86,026 |
| Capital base | Rs 10,00,000 |

## Simulation Results

| Skip | Run | Seed | Traded Days | Rnd Skip | Strat Skip | Net P/L | CAGR | vs Base | Max DD | Win% | Max SL/Day | Max SL Overall |
|------|-----|------|-------------|----------|------------|---------|------|---------|--------|------|------------|----------------|
| 30% | 1 | 42 | 1137 | 533 | 181 | -Rs 1,191,680 | -100.00% | +0.0pp | Rs 1,740,919 | 51.5% | 15 | 27 |
| 30% | 2 | 137 | 1099 | 560 | 192 | -Rs 608,112 | -11.80% | +88.2pp | Rs 1,207,810 | 52.7% | 15 | 30 |
| 30% | 3 | 999 | 1056 | 611 | 184 | -Rs 1,324,809 | -100.00% | +0.0pp | Rs 1,818,975 | 51.6% | 15 | 23 |
| 30% | 4 | 2024 | 1123 | 536 | 192 | -Rs 1,767,111 | -100.00% | +0.0pp | Rs 2,130,606 | 50.6% | 15 | 23 |
| 30% | 5 | 31415 | 1099 | 560 | 192 | -Rs 952,547 | -33.53% | +66.5pp | Rs 1,603,950 | 52.0% | 15 | 26 |
| 40% | 1 | 42 | 980 | 709 | 162 | -Rs 838,172 | -21.65% | +78.3pp | Rs 1,488,986 | 52.2% | 15 | 28 |
| 40% | 2 | 137 | 921 | 766 | 164 | -Rs 743,000 | -16.64% | +83.4pp | Rs 1,070,906 | 52.1% | 15 | 30 |
| 40% | 3 | 999 | 917 | 778 | 156 | -Rs 1,409,176 | -100.00% | +0.0pp | Rs 1,795,531 | 50.4% | 15 | 23 |
| 40% | 4 | 2024 | 963 | 731 | 157 | -Rs 1,485,038 | -100.00% | +0.0pp | Rs 1,900,131 | 50.2% | 15 | 23 |
| 40% | 5 | 31415 | 941 | 751 | 159 | -Rs 785,682 | -18.65% | +81.4pp | Rs 1,454,330 | 52.6% | 15 | 26 |
| 50% | 1 | 42 | 819 | 896 | 136 | -Rs 918,329 | -28.51% | +71.5pp | Rs 1,463,004 | 51.8% | 15 | 28 |
| 50% | 2 | 137 | 770 | 937 | 144 | -Rs 873,074 | -24.16% | +75.8pp | Rs 1,182,833 | 51.8% | 15 | 30 |
| 50% | 3 | 999 | 747 | 973 | 131 | -Rs 736,498 | -16.36% | +83.6pp | Rs 1,219,962 | 50.9% | 15 | 27 |
| 50% | 4 | 2024 | 807 | 918 | 126 | -Rs 1,326,142 | -100.00% | +0.0pp | Rs 1,697,530 | 50.6% | 15 | 20 |
| 50% | 5 | 31415 | 780 | 941 | 130 | -Rs 897,475 | -26.30% | +73.7pp | Rs 1,468,828 | 52.3% | 15 | 26 |

## Aggregated by Skip Rate (5 runs each)

| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days | Avg Max SL/Day | Avg Max SL Overall |
|-----------|-------------|----------|----------|----------|------------|----------|-----------------|----------------|---------------------|
| 30% | -Rs 1,168,852 | -69.06% | -100.00% | -11.80% | Rs 1,700,452 | 51.7% | 1103 | 15.0 | 25.8 |
| 40% | -Rs 1,052,214 | -51.39% | -100.00% | -16.64% | Rs 1,541,977 | 51.5% | 944 | 15.0 | 26.0 |
| 50% | -Rs 950,304 | -39.07% | -100.00% | -16.36% | Rs 1,406,431 | 51.5% | 785 | 15.0 | 26.2 |

## SL Streak Detail

| Skip | Run | Max SL in a Single Day | Max SL Streak (All Trades) | Total Stop Exits | Total Trades |
|------|-----|------------------------|----------------------------|------------------|--------------|
| 30% | 1 | 15 | 27 | 3560 | 4446 |
| 30% | 2 | 15 | 30 | 3454 | 4302 |
| 30% | 3 | 15 | 23 | 3389 | 4202 |
| 30% | 4 | 15 | 23 | 3637 | 4500 |
| 30% | 5 | 15 | 26 | 3412 | 4264 |
| 40% | 1 | 15 | 28 | 3019 | 3787 |
| 40% | 2 | 15 | 30 | 2954 | 3673 |
| 40% | 3 | 15 | 23 | 2982 | 3694 |
| 40% | 4 | 15 | 23 | 3105 | 3847 |
| 40% | 5 | 15 | 26 | 2916 | 3642 |
| 50% | 1 | 15 | 28 | 2571 | 3203 |
| 50% | 2 | 15 | 30 | 2482 | 3088 |
| 50% | 3 | 15 | 27 | 2378 | 2961 |
| 50% | 4 | 15 | 20 | 2624 | 3244 |
| 50% | 5 | 15 | 26 | 2434 | 3033 |

## Notes

- **Max SL/Day**: worst single-day streak of consecutive stop-loss exits (within one day).
- **Max SL Overall**: longest consecutive SL streak across all trades in the backtest, ignoring day boundaries.
- CAGR computed on Rs 10,00,000 capital over the full data range (same as baseline).
- 'Rnd Skip' = days the random model chose not to participate.
- 'Strat Skip' = days participated but no trade completed (data gaps, no signal, etc.).
- At 09:20 the option data is sparse; most days the effective first entry falls at 09:30.
