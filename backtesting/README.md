# Backtesting Results Index

This table summarizes the result files currently present under `backtesting/results` and `backtesting/results/legacy`.

Notes:

- `Profit %` is calculated as `Net P/L / Rs 10,00,000 * 100` so every result has one comparable percentage column.
- Some older summaries do not report max drawdown; those rows are marked `N/A`.
- Results are only as current as the generated files in `backtesting/results`.

| Source | Test | Result | Net P/L | Profit % | Max DD |
|---|---|---:|---:|---:|---:|
| Current | Combined Expiry + Adjusting Short Strangle 2025 | Profit | Rs 2,52,042.69 | 25.20% | Rs 69,261.93 |
| Current | Weekly Adjusting Strangle Through Expiry 2025 | Profit | Rs 1,48,016.27 | 14.80% | Rs 85,510.77 |
| Current | Weekly Short Strangle 09:20 2025 | Loss | Rs -1,47,728.40 | -14.77% | N/A |
| Current | NIFTY Last 3 Same-Color Overnight 15m | Profit | Rs 1,50,712.25 | 15.07% | Rs 46,143.50 |
| Current | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 2,51,943.80 | 25.19% | Rs 1,02,323.00 |
| Current | Gap 100 ATM Option 09:16 2025 | Loss | Rs -5,696.40 | -0.57% | N/A |
| Current | Gap Open ATM Straddle 09:15 2025 | Loss | Rs -2,73,125.00 | -27.31% | N/A |
| Current | Short ATM Same-Week Intraday SL 2025 | Loss | Rs -1,23,796.40 | -12.38% | N/A |
| Legacy | Intraday Adjusted Weekly Straddle 2025 | Profit | Rs 1,77,017.00 | 17.70% | N/A |
| Legacy | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 2,51,943.80 | 25.19% | Rs 1,02,323.00 |
| Legacy | Long/Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 3,36,729.70 | 33.67% | Rs 80,646.50 |
| Legacy | NIFTY 25/50 SMA Crossover 1R | Loss | Rs -74,993.75 | -7.50% | Rs 1,47,403.75 |
| Legacy | NIFTY 25/50 SMA Crossover 2R | Profit | Rs 1,95,734.50 | 19.57% | Rs 1,16,119.25 |
| Legacy | NIFTY 25/50 SMA Crossover 3R | Profit | Rs 1,76,514.00 | 17.65% | Rs 1,31,488.50 |
| Legacy | NIFTY 25-SMA Continuous Trailing 15m | Profit | Rs 11,88,295.55 | 118.83% | Rs 1,65,540.05 |
| Legacy | NIFTY 25-SMA Intraday Trailing 15m | Profit | Rs 5,63,707.95 | 56.37% | Rs 93,377.70 |
| Legacy | NIFTY 25-SMA Overnight Movement 15m | Profit | Rs 10,50,786.75 | 105.08% | Rs 74,750.00 |
| Legacy | Short ATM MA Same-Week 15m 2025 | Profit | Rs 4,93,017.00 | 49.30% | N/A |
| Legacy | Short ATM MA Same-Week 15m Trailing 2025 | Profit | Rs 4,93,017.00 | 49.30% | N/A |
| Legacy | Short ATM MA Same-Week 15m Trailing Intraday Entry 2025 | Profit | Rs 5,10,661.20 | 51.07% | N/A |
| Legacy | Short ATM NIFTY MA Weekly Intraday Trailing 2025 | Profit | Rs 6,60,341.40 | 66.03% | Rs 1,30,612.40 |
| Legacy | Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 4,46,015.60 | 44.60% | Rs 76,221.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Hedged 2025 | Loss | Rs -2,18,490.00 | -21.85% | Rs 3,22,592.50 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 100 | Profit | Rs 3,63,236.80 | 36.32% | Rs 58,480.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 200 | Profit | Rs 2,81,303.60 | 28.13% | Rs 45,259.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 300 | Profit | Rs 1,99,936.00 | 19.99% | Rs 34,482.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 400 | Profit | Rs 1,35,545.00 | 13.55% | Rs 26,823.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 500 | Profit | Rs 86,768.40 | 8.68% | Rs 28,324.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset ITM 100 | Profit | Rs 5,14,952.00 | 51.50% | Rs 95,435.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset ITM 200 | Profit | Rs 5,78,795.00 | 57.88% | Rs 1,13,666.00 |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset ITM 300 | Profit | Rs 6,23,772.40 | 62.38% | Rs 1,25,171.00 |
| Legacy | Short ATM Weekly Straddle 2025 | Loss | Rs -10,824.00 | -1.08% | N/A |
| Legacy | Short Iron Condor Next Week 2025 | Loss | Rs -21,321.20 | -2.13% | N/A |
| Legacy | Short Iron Fly 2025 | Loss | Rs -4,33,828.60 | -43.38% | N/A |
