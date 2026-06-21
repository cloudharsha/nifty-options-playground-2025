# Backtesting Results Index

This table summarizes the result files currently present under `backtesting/results`, including archived folders such as `backtesting/results/legacy`, `backtesting/results/legacy-2`, and `backtesting/results/legacy-3`.

Notes:

- `CAGR / Return` shows **CAGR** for multi-year strategies and **total return %** for single-year strategies.
- Most short-option and index tests use a Rs 10,00,000 reference base.
- NIFTY futures strategies (1-lot, Rs 65/point) use a Rs 2,50,000 capital base — approximate margin required for 1 lot of NIFTY futures.
- The long ATM weekly overnight option strategy uses a Rs 1,00,000 reference base because it is a long-premium strategy. With the tested 4-lot sizing, its max premium outlay was Rs 89,440 and max drawdown was Rs 1,02,323, so Rs 1L is possible but very tight.
- Some older summaries do not report max drawdown; those rows are marked `N/A`.
- Results are only as current as the generated files in `backtesting/results`.
- Rows are sorted: **Profit strategies first** (highest CAGR → lowest), then **Loss strategies** (least negative → most negative). Rows without CAGR are placed at the bottom of each section, sorted by Net P/L.

| Source | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary |
|---|---|---|---:|---:|---:|---:|---:|---|
| Legacy-2 | 2025 | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 1L | Rs 2,51,943.80 | 251.94% | Rs 1,02,323.00 | [Summary](results/legacy-2/long_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy | 2025 | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 1L | Rs 2,51,943.80 | 251.94% | Rs 1,02,323.00 | [Summary](results/legacy/long_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Intraday Trailing 2025 | Profit | Rs 10L | Rs 6,60,341.40 | 66.03% | Rs 1,30,612.40 | [Summary](results/legacy/short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset ITM 300 | Profit | Rs 10L | Rs 6,23,772.40 | 62.38% | Rs 1,25,171.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset ITM 200 | Profit | Rs 10L | Rs 5,78,795.00 | 57.88% | Rs 1,13,666.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | 4Y | NIFTY 25-SMA Continuous Trailing 15m | Profit | Rs 2.5L | Rs 11,88,295.55 | 54.88% CAGR | Rs 1,65,540.05 | [Summary](results/legacy/nifty_ma_continuous_trailing_15m_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset ITM 100 | Profit | Rs 10L | Rs 5,14,952.00 | 51.50% | Rs 95,435.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | 2025 | Short ATM MA Same-Week 15m Trailing Intraday Entry 2025 | Profit | Rs 10L | Rs 5,10,661.20 | 51.07% | N/A | [Summary](results/legacy/short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md) |
| Legacy | 4Y | NIFTY 25-SMA Overnight Movement 15m | Profit | Rs 2.5L | Rs 10,50,786.75 | 51.03% CAGR | Rs 74,750.00 | [Summary](results/legacy/nifty_ma_overnight_movement_15m_summary.md) |
| Legacy | 2025 | Short ATM MA Same-Week 15m 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](results/legacy/short_atm_ma_same_week_15m_2025_summary.md) |
| Legacy | 2025 | Short ATM MA Same-Week 15m Trailing 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](results/legacy/short_atm_ma_same_week_15m_trailing_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 10L | Rs 4,46,015.60 | 44.60% | Rs 76,221.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 100 | Profit | Rs 10L | Rs 3,63,236.80 | 36.32% | Rs 58,480.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | 4Y | NIFTY 25-SMA Intraday Trailing 15m | Profit | Rs 2.5L | Rs 5,63,707.95 | 34.31% CAGR | Rs 93,377.70 | [Summary](results/legacy/nifty_ma_intraday_trailing_15m_summary.md) |
| Legacy | 2025 | Long/Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 10L | Rs 3,36,729.70 | 33.67% | Rs 80,646.50 | [Summary](results/legacy/long_short_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Current | ~4Y | Long/Short ATM NIFTY MA Weekly Overnight 2022-2026 (capital-based lots, margin ≈10%) | Profit | Rs 10L | Rs 20,77,457.90 | 32.63% CAGR | Rs 6,80,802.50 | [Summary](results/long_short_atm_nifty_ma_weekly_overnight_2020_2026_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 200 | Profit | Rs 10L | Rs 2,81,303.60 | 28.13% | Rs 45,259.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy-2 | 2025 | Combined Expiry + Adjusting Short Strangle 2025 | Profit | Rs 10L | Rs 2,52,042.69 | 25.20% | Rs 69,261.93 | [Summary](results/legacy-2/combined_expiry_adjusting_strangle_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 300 | Profit | Rs 10L | Rs 1,99,936.00 | 19.99% | Rs 34,482.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy | 2025 | Intraday Adjusted Weekly Straddle 2025 | Profit | Rs 10L | Rs 1,77,017.00 | 17.70% | N/A | [Summary](results/legacy/intraday_adjusted_straddle_2025_summary.md) |
| Legacy-3 | ~6Y | Heads & Tails Grid — Short ATM NIFTY Weekly (20 combos × 5 runs; best: SL=40%, T=open) | Profit | Rs 5L | Rs 9,73,379 avg | 17.38% avg CAGR | Rs 4,81,637 avg | [Summary](results/legacy-3/heads_tails_nifty_grid_summary.md) |
| Legacy | 4Y | NIFTY 25/50 SMA Crossover 2R | Profit | Rs 2.5L | Rs 1,95,734.50 | 15.55% CAGR | Rs 1,16,119.25 | [Summary](results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |
| Legacy-2 | 2025 | Weekly Adjusting Strangle Through Expiry 2025 | Profit | Rs 10L | Rs 1,48,016.27 | 14.80% | Rs 85,510.77 | [Summary](results/legacy-2/weekly_adjusting_strangle_through_expiry_2025_summary.md) |
| Legacy | 4Y | NIFTY 25/50 SMA Crossover 3R | Profit | Rs 2.5L | Rs 1,76,514.00 | 14.29% CAGR | Rs 1,31,488.50 | [Summary](results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |
| Current | 2025 | Intraday ATM Straddle — Independent SL per Leg (1 lot, 09:20–15:20, 2× SL each leg) | Profit | Rs 3L | Rs 40,756.25 | 13.59% | Rs 38,647.00 | [Summary](results/intraday_atm_straddle_indep_sl_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 400 | Profit | Rs 10L | Rs 1,35,545.00 | 13.55% | Rs 26,823.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy-2 | 4Y | NIFTY Last 3 Same-Color Overnight 15m | Profit | Rs 2.5L | Rs 1,50,712.25 | 12.52% CAGR | Rs 46,143.50 | [Summary](results/legacy-2/nifty_last_3_green_overnight_15m_summary.md) |
| Current | 2025 | Intraday ATM Straddle — 25-period 15m MA Filter (1 lot, 09:40–15:20, MA entry + dynamic MA SL) | Profit | Rs 3L | Rs 35,710.36 | 11.90% | Rs 24,078.33 | [Summary](results/intraday_atm_straddle_ma25_2025_summary.md) |
| Legacy-3 | ~6Y | Heads & Tails — Random Short ATM NIFTY Weekly (5 runs avg; SL=20%, T=50%, 09:30–15:20, noon re-entry) | Profit | Rs 5L | Rs 4,38,958 avg | ~9.84% avg CAGR | Rs 3,25,433 avg | [Summary](results/legacy-3/heads_tails_nifty_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 500 | Profit | Rs 10L | Rs 86,768.40 | 8.68% | Rs 28,324.00 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Legacy-3 | Sep 25+ | Combined NIFTY+SENSEX ATM Straddle — Expiry-Incl., no balance filter (Mon/Tue/Fri=NIFTY ~300 qty, Wed/Thu=SENSEX 100 qty) | Profit | Rs 5L | Rs 27,012 | 6.90% CAGR | Rs 1,32,821 | [Summary](results/legacy-3/combined_nifty_sensex_expiry_incl_2025_summary.md) |
| Current | 2025 | Intraday ATM Straddle — Joint SL (1 lot, 09:20–15:20, 2× SL exits both legs) | Profit | Rs 3L | Rs 16,595.00 | 5.53% | Rs 53,756.50 | [Summary](results/intraday_atm_straddle_joint_sl_2025_summary.md) |
| Legacy-3 | Sep 25+ | Combined Balanced-Strike ATM Straddle — NIFTY+SENSEX (161 days, 9 SL levels tested; best SL=50%) | Profit | Rs 5L | Rs 10,361 | 2.6% CAGR | Rs 1,57,613 | [Summary](results/legacy-3/combined_nifty_sensex_balanced_strike_2025_summary.md) |
| Legacy-2 | 2025 | Expiry ITM 100 MA Short 09:20 2025 | Profit | Rs 10L | Rs 15,760.60 | 1.58% | Rs 2,40,921.00 | [Summary](results/legacy-2/expiry_itm100_ma_short_0920_2025_summary.md) |
| Legacy-3 | ~6Y | NIFTY Intraday ATM Straddle — Expiry-Inclusive (~300 qty, 09:20–15:20, 20% Ind. SL per leg, balance filter) | Profit | Rs 10L | Rs 10,48,326 | N/A | Rs 2,93,983 | [Summary](results/legacy-3/intraday_atm_straddle_expiry_incl_nifty_summary.md) |
| Legacy-3 | 2024–2026 | SENSEX Intraday ATM Straddle — Expiry-Inclusive (100 qty, 09:20–15:20, 20% Ind. SL per leg, balance filter) | Profit | Rs 5L | Rs 3,29,040 | N/A | Rs 1,70,381 | [Summary](results/legacy-3/intraday_atm_straddle_expiry_incl_sensex_summary.md) |
| Legacy-3 | 2024–2026 | SENSEX Intraday ATM Straddle — 20% Ind. SL, Monthly Expiry (100 qty, 09:20–15:20, balance filter) | Profit | Rs 5L | Rs 2,52,845 | N/A | Rs 1,12,754 | [Summary](results/legacy-3/intraday_atm_straddle_20pct_sl_sensex_monthly_2024_2026_summary.md) |
| Legacy-3 | ~6Y | NIFTY Intraday ATM Straddle — 20% Ind. SL, Weekly Expiry (~300 qty, 09:20–15:20, balance filter) | Profit | Rs 10L | Rs 2,16,384 | N/A | Rs 2,60,277 | [Summary](results/legacy-3/intraday_atm_straddle_20pct_sl_nifty_2020_2026_summary.md) |
| Legacy-3 | 2024–2026 | SENSEX Intraday ATM Straddle — 20% Ind. SL, Weekly Expiry (100 qty, 09:20–15:20, balance filter) | Profit | Rs 5L | Rs 1,44,762 | N/A | Rs 1,72,031 | [Summary](results/legacy-3/intraday_atm_straddle_20pct_sl_sensex_2024_2026_summary.md) |
| Legacy-2 | 2025 | Gap 100 ATM Option 09:16 2025 | Loss | Rs 10L | Rs -5,696.40 | -0.57% | N/A | [Summary](results/legacy-2/gap_100_atm_option_0916_2025_summary.md) |
| Legacy | 2025 | Short ATM Weekly Straddle 2025 | Loss | Rs 10L | Rs -10,824.00 | -1.08% | N/A | [Summary](results/legacy/short_atm_weekly_straddle_2025_summary.md) |
| Legacy | 2025 | Short Iron Condor Next Week 2025 | Loss | Rs 10L | Rs -21,321.20 | -2.13% | N/A | [Summary](results/legacy/short_iron_condor_next_week_2025_summary.md) |
| Legacy-3 | Sep 25+ | Combined Short OTM Strangle — NIFTY+SENSEX (153 days, 9 SL levels tested; best SL=90%) | Loss | Rs 5L | Rs -21,010 | -5.3% CAGR | Rs 49,425 | [Summary](results/legacy-3/combined_strangle_2025_summary.md) |
| Legacy | 4Y | NIFTY 25/50 SMA Crossover 1R | Loss | Rs 2.5L | Rs -74,993.75 | -8.53% CAGR | Rs 1,47,403.75 | [Summary](results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |
| Current | 2025 | Overnight OTM Strangle by Day — with fallback band (1 lot, 15:20–09:20 next day) | Loss | Rs 3L | Rs -26,781.25 | -8.93% | Rs 43,118.50 | [Summary](results/overnight_strangle_by_day_2025_summary.md) |
| Current | 2025 | Intraday OTM Strangle Joint SL by Day — with fallback band (1 lot, 09:20–15:20, 2× joint SL) | Loss | Rs 3L | Rs -27,204.25 | -9.07% | Rs 35,332.00 | [Summary](results/intraday_joint_sl_strangle_2025_summary.md) |
| Legacy-2 | 2025 | Short ATM Same-Week Intraday SL 2025 | Loss | Rs 10L | Rs -1,23,796.40 | -12.38% | N/A | [Summary](results/legacy-2/short_atm_same_week_intraday_sl_2025_summary.md) |
| Legacy-2 | 2025 | Weekly Short Strangle 09:20 2025 | Loss | Rs 10L | Rs -1,47,728.40 | -14.77% | N/A | [Summary](results/legacy-2/weekly_short_strangle_0920_2025_summary.md) |
| Legacy | 2025 | Short ATM NIFTY MA Weekly Overnight Hedged 2025 | Loss | Rs 10L | Rs -2,18,490.00 | -21.85% | Rs 3,22,592.50 | [Summary](results/legacy/short_atm_nifty_ma_weekly_overnight_hedged_2025_summary.md) |
| Legacy-2 | 2025 | Gap Open ATM Straddle 09:15 2025 | Loss | Rs 10L | Rs -2,73,125.00 | -27.31% | N/A | [Summary](results/legacy-2/gap_open_atm_straddle_0915_2025_summary.md) |
| Legacy | 2025 | Short Iron Fly 2025 | Loss | Rs 10L | Rs -4,33,828.60 | -43.38% | N/A | [Summary](results/legacy/short_iron_fly_2025_summary.md) |
| Legacy-3 | ~6Y | Heads & Tails Grid — LONG ATM NIFTY Weekly (28 combos × 5 runs; best: SL=20%, T=90%) | Loss | Rs 5L | Rs -7,56,517 avg | -86.29% avg CAGR | N/A | [Summary](results/legacy-3/heads_tails_nifty_grid_long_summary.md) |
| Legacy-3 | 2024–2026 | Weekly Short Strangle — NIFTY+SENSEX Alternating (OTM, 1 lot each, 09:30–15:20, 2× SL) | Loss | Rs 5L | Rs -48,953 | N/A | Rs 66,567 | [Summary](results/legacy-3/weekly_strangle_nifty_sensex_2024_2026_summary.md) |
| Current | ~4Y | Weekly Short Iron Condor Roll 2022-2026 (1 lot, sell ±250, hedge ±450, 09:15 entry, 15:15 exit on expiry) | Loss | Rs 10L | Rs -68,495.25 | N/A | N/A | [Summary](results/weekly_iron_condor_roll_2020_2026_summary.md) |
| Legacy-3 | ~6Y | NIFTY Intraday ATM Straddle — 20% Ind. SL, Monthly Expiry (~300 qty, 09:20–15:20, balance filter) | Loss | Rs 10L | Rs -1,54,701 | N/A | Rs 3,49,483 | [Summary](results/legacy-3/intraday_atm_straddle_20pct_sl_nifty_monthly_2020_2026_summary.md) |
| Legacy-3 | ~4Y | NIFTY Intraday Iron Condor — Weekly (~300 qty, May 2022–2026, sell ±250, hedge ±450, 09:20–15:20, no SL) | Loss | Rs 10L | Rs -22,87,219 | N/A | N/A | [Summary](results/legacy-3/intraday_iron_condor_weekly_2020_2026_summary.md) |
