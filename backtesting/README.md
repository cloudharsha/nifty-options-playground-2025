# Backtesting Results Index

This table summarizes the result files currently present under `backtesting/results`, including archived folders such as `backtesting/results/legacy` and `backtesting/results/legacy-2`.

Notes:

- `Profit %` is calculated from the `Capital Base` column.
- Most short-option and index tests use a Rs 10,00,000 reference base.
- NIFTY futures strategies (1-lot, Rs 65/point) use a Rs 2,50,000 capital base — approximate margin required for 1 lot of NIFTY futures.
- The long ATM weekly overnight option strategy uses a Rs 1,00,000 reference base because it is a long-premium strategy. With the tested 4-lot sizing, its max premium outlay was Rs 89,440 and max drawdown was Rs 1,02,323, so Rs 1L is possible but very tight.
- Some older summaries do not report max drawdown; those rows are marked `N/A`.
- Results are only as current as the generated files in `backtesting/results`.

| Source | Test | Result | Capital Base | Net P/L | Profit % | Max DD | Summary |
|---|---|---:|---:|---:|---:|---:|---|
| Legacy-2 | Combined Expiry + Adjusting Short Strangle 2025 | Profit | Rs 10L | Rs 2,52,042.69 | 25.20% | Rs 69,261.93 | [Summary](results/legacy-2/combined_expiry_adjusting_strangle_2025_summary.md) |
| Legacy-2 | Weekly Adjusting Strangle Through Expiry 2025 | Profit | Rs 10L | Rs 1,48,016.27 | 14.80% | Rs 85,510.77 | [Summary](results/legacy-2/weekly_adjusting_strangle_through_expiry_2025_summary.md) |
| Legacy-2 | Weekly Short Strangle 09:20 2025 | Loss | Rs 10L | Rs -1,47,728.40 | -14.77% | N/A | [Summary](results/legacy-2/weekly_short_strangle_0920_2025_summary.md) |
| Legacy-2 | NIFTY Last 3 Same-Color Overnight 15m | Profit | Rs 2.5L | Rs 1,50,712.25 | 60.28% | Rs 46,143.50 | [Summary](results/legacy-2/nifty_last_3_green_overnight_15m_summary.md) |
| Legacy-2 | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 1L | Rs 2,51,943.80 | 251.94% | Rs 1,02,323.00 | [Summary](results/legacy-2/long_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy-2 | Gap 100 ATM Option 09:16 2025 | Loss | Rs 10L | Rs -5,696.40 | -0.57% | N/A | [Summary](results/legacy-2/gap_100_atm_option_0916_2025_summary.md) |
| Legacy-2 | Gap Open ATM Straddle 09:15 2025 | Loss | Rs 10L | Rs -2,73,125.00 | -27.31% | N/A | [Summary](results/legacy-2/gap_open_atm_straddle_0915_2025_summary.md) |
| Legacy-2 | Short ATM Same-Week Intraday SL 2025 | Loss | Rs 10L | Rs -1,23,796.40 | -12.38% | N/A | [Summary](results/legacy-2/short_atm_same_week_intraday_sl_2025_summary.md) |
| Legacy-2 | Expiry ITM 100 MA Short 09:20 2025 | Profit | Rs 10L | Rs 15,760.60 | 1.58% | Rs 2,40,921.00 | [Summary](results/legacy-2/expiry_itm100_ma_short_0920_2025_summary.md) |
| Legacy | Intraday Adjusted Weekly Straddle 2025 | Profit | Rs 10L | Rs 1,77,017.00 | 17.70% | N/A | [Summary](results/legacy/intraday_adjusted_straddle_2025_summary.md) |
| Legacy | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 1L | Rs 2,51,943.80 | 251.94% | Rs 1,02,323.00 | [Summary](results/legacy/long_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy | Long/Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 10L | Rs 3,36,729.70 | 33.67% | Rs 80,646.50 | [Summary](results/legacy/long_short_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy | NIFTY 25/50 SMA Crossover 1R | Loss | Rs 2.5L | Rs -74,993.75 | -30.00% | Rs 1,47,403.75 | [Summary](results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |
| Legacy | NIFTY 25/50 SMA Crossover 2R | Profit | Rs 2.5L | Rs 1,95,734.50 | 78.29% | Rs 1,16,119.25 | [Summary](results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |
| Legacy | NIFTY 25/50 SMA Crossover 3R | Profit | Rs 2.5L | Rs 1,76,514.00 | 70.61% | Rs 1,31,488.50 | [Summary](results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |
| Legacy | NIFTY 25-SMA Continuous Trailing 15m | Profit | Rs 2.5L | Rs 11,88,295.55 | 475.32% | Rs 1,65,540.05 | [Summary](results/legacy/nifty_ma_continuous_trailing_15m_summary.md) |
| Legacy | NIFTY 25-SMA Intraday Trailing 15m | Profit | Rs 2.5L | Rs 5,63,707.95 | 225.48% | Rs 93,377.70 | [Summary](results/legacy/nifty_ma_intraday_trailing_15m_summary.md) |
| Legacy | NIFTY 25-SMA Overnight Movement 15m | Profit | Rs 2.5L | Rs 10,50,786.75 | 420.31% | Rs 74,750.00 | [Summary](results/legacy/nifty_ma_overnight_movement_15m_summary.md) |
| Legacy | Short ATM MA Same-Week 15m 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](results/legacy/short_atm_ma_same_week_15m_2025_summary.md) |
| Legacy | Short ATM MA Same-Week 15m Trailing 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](results/legacy/short_atm_ma_same_week_15m_trailing_2025_summary.md) |
| Legacy | Short ATM MA Same-Week 15m Trailing Intraday Entry 2025 | Profit | Rs 10L | Rs 5,10,661.20 | 51.07% | N/A | [Summary](results/legacy/short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Intraday Trailing 2025 | Profit | Rs 10L | Rs 6,60,341.40 | 66.03% | Rs 1,30,612.40 | [Summary](results/legacy/short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 10L | Rs 4,46,015.60 | 44.60% | Rs 76,221.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Hedged 2025 | Loss | Rs 10L | Rs -2,18,490.00 | -21.85% | Rs 3,22,592.50 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_hedged_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 100 | Profit | Rs 10L | Rs 3,63,236.80 | 36.32% | Rs 58,480.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 200 | Profit | Rs 10L | Rs 2,81,303.60 | 28.13% | Rs 45,259.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 300 | Profit | Rs 10L | Rs 1,99,936.00 | 19.99% | Rs 34,482.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 400 | Profit | Rs 10L | Rs 1,35,545.00 | 13.55% | Rs 26,823.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset OTM 500 | Profit | Rs 10L | Rs 86,768.40 | 8.68% | Rs 28,324.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset ITM 100 | Profit | Rs 10L | Rs 5,14,952.00 | 51.50% | Rs 95,435.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset ITM 200 | Profit | Rs 10L | Rs 5,78,795.00 | 57.88% | Rs 1,13,666.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM NIFTY MA Weekly Overnight Offset ITM 300 | Profit | Rs 10L | Rs 6,23,772.40 | 62.38% | Rs 1,25,171.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | Short ATM Weekly Straddle 2025 | Loss | Rs 10L | Rs -10,824.00 | -1.08% | N/A | [Summary](results/legacy/short_atm_weekly_straddle_2025_summary.md) |
| Legacy | Short Iron Condor Next Week 2025 | Loss | Rs 10L | Rs -21,321.20 | -2.13% | N/A | [Summary](results/legacy/short_iron_condor_next_week_2025_summary.md) |
| Legacy | Short Iron Fly 2025 | Loss | Rs 10L | Rs -4,33,828.60 | -43.38% | N/A | [Summary](results/legacy/short_iron_fly_2025_summary.md) |
