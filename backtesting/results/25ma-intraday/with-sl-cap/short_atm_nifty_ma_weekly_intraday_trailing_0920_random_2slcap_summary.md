# 09:20-Start Random-Skip + 2-SL/Day Cap Backtest — Short ATM NIFTY MA Weekly Intraday Trailing

## Strategy changes vs baseline

- **Entry start**: 09:20 (vs 09:30 in baseline); falls through to 09:30 if no option data at 09:20
- **Signal at 09:20**: uses the previous session's 15:15 bar - the newest 15m
  candle closed by 09:20. ATM strike comes from the 09:15 5m bar close.
- **Day skipping**: random at 30% / 40% / 50% (5 runs each, 15 total)
- **Seeds**: [42, 137, 999, 2024, 31415]
- **Exit logic**: trailing 25-SMA stop on 5m candles, or EOD 15:15
- **Re-entry after stop**: next 15m boundary
- **NEW — Daily SL cap**: if stop-loss fires 2 times in a day, no further entries that day

## Baseline (full participation, 09:30 start, no SL cap)

| Metric | Value |
|--------|-------|
| Net P/L | -Rs 1,415,087 |
| CAGR | -100.00% |
| Max Drawdown | Rs 1,986,026 |
| Capital base | Rs 10,00,000 |

## Simulation Results

| Skip | Run | Seed | Traded Days | Rnd Skip | Strat Skip | 2SL-Cap Days | Net P/L | CAGR | vs Base | Max DD | Win% | Max SL/Day | Max SL Overall |
|------|-----|------|-------------|----------|------------|-------------|---------|------|---------|--------|------|------------|----------------|
| 30% | 1 | 42 | 1137 | 533 | 181 | 707 | -Rs 243,421 | -3.67% | +96.3pp | Rs 844,391 | 47.4% | 2 | 27 |
| 30% | 2 | 137 | 1099 | 560 | 192 | 680 | Rs 203,153 | 2.51% | +102.5pp | Rs 727,580 | 48.8% | 2 | 21 |
| 30% | 3 | 999 | 1056 | 611 | 184 | 657 | -Rs 304,587 | -4.75% | +95.2pp | Rs 876,774 | 47.6% | 2 | 40 |
| 30% | 4 | 2024 | 1123 | 536 | 192 | 710 | -Rs 567,300 | -10.62% | +89.4pp | Rs 885,790 | 47.4% | 2 | 38 |
| 30% | 5 | 31415 | 1099 | 560 | 192 | 668 | -Rs 116,459 | -1.65% | +98.4pp | Rs 901,905 | 48.1% | 2 | 26 |
| 40% | 1 | 42 | 980 | 709 | 162 | 606 | -Rs 36,908 | -0.50% | +99.5pp | Rs 720,676 | 47.1% | 2 | 37 |
| 40% | 2 | 137 | 921 | 766 | 164 | 574 | -Rs 15,122 | -0.20% | +99.8pp | Rs 590,690 | 48.2% | 2 | 23 |
| 40% | 3 | 999 | 917 | 778 | 156 | 574 | -Rs 445,112 | -7.59% | +92.4pp | Rs 893,858 | 46.6% | 2 | 36 |
| 40% | 4 | 2024 | 963 | 731 | 157 | 614 | -Rs 545,764 | -10.03% | +90.0pp | Rs 832,425 | 46.4% | 2 | 38 |
| 40% | 5 | 31415 | 941 | 751 | 159 | 575 | -Rs 39,733 | -0.54% | +99.5pp | Rs 785,978 | 49.0% | 2 | 22 |
| 50% | 1 | 42 | 819 | 896 | 136 | 512 | -Rs 85,814 | -1.19% | +98.8pp | Rs 711,016 | 47.4% | 2 | 33 |
| 50% | 2 | 137 | 770 | 937 | 144 | 491 | -Rs 337,034 | -5.36% | +94.6pp | Rs 632,840 | 47.3% | 2 | 29 |
| 50% | 3 | 999 | 747 | 973 | 131 | 465 | -Rs 234,989 | -3.53% | +96.5pp | Rs 725,758 | 46.5% | 2 | 33 |
| 50% | 4 | 2024 | 807 | 918 | 126 | 516 | -Rs 525,914 | -9.52% | +90.5pp | Rs 896,429 | 46.8% | 2 | 28 |
| 50% | 5 | 31415 | 780 | 941 | 130 | 479 | -Rs 165,881 | -2.40% | +97.6pp | Rs 771,208 | 48.8% | 2 | 23 |

## Aggregated by Skip Rate (5 runs each)

| Skip Rate | Avg Net P/L | Avg CAGR | Min CAGR | Max CAGR | Avg Max DD | Avg Win% | Avg Traded Days | Avg 2SL-Cap Days | Avg Max SL/Day | Avg Max SL Overall |
|-----------|-------------|----------|----------|----------|------------|----------|-----------------|------------------|----------------|---------------------|
| 30% | -Rs 205,723 | -3.63% | -10.62% | 2.51% | Rs 847,288 | 47.9% | 1103 | 684 | 2.0 | 30.4 |
| 40% | -Rs 216,528 | -3.77% | -10.03% | -0.20% | Rs 764,725 | 47.5% | 944 | 589 | 2.0 | 31.2 |
| 50% | -Rs 269,926 | -4.40% | -9.52% | -1.19% | Rs 747,450 | 47.4% | 785 | 493 | 2.0 | 29.2 |

## SL Streak Detail

| Skip | Run | Max SL in a Single Day | Max SL Streak (All Trades) | Total Stop Exits | Total Trades | 2SL-Cap Days |
|------|-----|------------------------|----------------------------|------------------|--------------|--------------|
| 30% | 1 | 2 | 27 | 1655 | 2048 | 707 |
| 30% | 2 | 2 | 21 | 1601 | 1985 | 680 |
| 30% | 3 | 2 | 40 | 1540 | 1907 | 657 |
| 30% | 4 | 2 | 38 | 1648 | 2031 | 710 |
| 30% | 5 | 2 | 26 | 1576 | 1970 | 668 |
| 40% | 1 | 2 | 37 | 1421 | 1764 | 606 |
| 40% | 2 | 2 | 23 | 1346 | 1666 | 574 |
| 40% | 3 | 2 | 36 | 1349 | 1668 | 574 |
| 40% | 4 | 2 | 38 | 1418 | 1743 | 614 |
| 40% | 5 | 2 | 22 | 1352 | 1685 | 575 |
| 50% | 1 | 2 | 33 | 1197 | 1477 | 512 |
| 50% | 2 | 2 | 29 | 1139 | 1397 | 491 |
| 50% | 3 | 2 | 33 | 1090 | 1351 | 465 |
| 50% | 4 | 2 | 28 | 1192 | 1463 | 516 |
| 50% | 5 | 2 | 23 | 1120 | 1393 | 479 |

## Notes

- **2-SL/Day Cap**: once 2 stop-loss exits occur on the same day, no further entries are taken that day.
- **2SL-Cap Days**: number of days where the cap was triggered (trading halted before EOD due to 2 SL hits).
- **Max SL/Day**: worst single-day streak of consecutive stop-loss exits (within one day).
- **Max SL Overall**: longest consecutive SL streak across all trades in the backtest, ignoring day boundaries.
- CAGR computed on Rs 10,00,000 capital over the full data range (same as baseline).
- 'Rnd Skip' = days the random model chose not to participate.
- 'Strat Skip' = days participated but no trade completed (data gaps, no signal, etc.).
- At 09:20 the option data is sparse; most days the effective first entry falls at 09:30.
