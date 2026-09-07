# Intraday Straddle

ATM straddles opened and closed within one session, with independent or joint stop losses and a CE/PE balance filter at entry. Covers both NIFTY and SENSEX.

- Scripts: [`backtesting/python/intraday-straddle/`](../../python/intraday-straddle/)
- Results: [`backtesting/results/intraday-straddle/`](../../results/intraday-straddle/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Intraday ATM Straddle — Independent SL per Leg (1 lot, 09:20–15:20, 2× SL each leg) | Profit | Rs 3L | Rs 40,756.25 | 13.59% | Rs 38,647.00 | [Summary](../../results/legacy/intraday_atm_straddle_indep_sl_2025_summary.md) |  |
| Archived | 2025 | Intraday ATM Straddle — 25-period 15m MA Filter (1 lot, 09:40–15:20, MA entry + dynamic MA SL) | Profit | Rs 3L | Rs 35,710.36 | 11.90% | Rs 24,078.33 | [Summary](../../results/legacy/intraday_atm_straddle_ma25_2025_summary.md) |  |
| Archived | 2025 | Intraday ATM Straddle — Joint SL (1 lot, 09:20–15:20, 2× SL exits both legs) | Profit | Rs 3L | Rs 16,595.00 | 5.53% | Rs 53,756.50 | [Summary](../../results/legacy/intraday_atm_straddle_joint_sl_2025_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — Expiry-Inclusive (~300 qty, 09:20–15:20, 20% Ind. SL per leg, balance filter) | Profit | Rs 10L | Rs 10,48,326 | N/A | Rs 2,93,983 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_expiry_incl_nifty_summary.md) |  |
| Current | 2024–2026 | SENSEX Intraday ATM Straddle — Expiry-Inclusive (100 qty, 09:20–15:20, 20% Ind. SL per leg, balance filter) | Profit | Rs 5L | Rs 3,29,040 | N/A | Rs 1,70,381 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_expiry_incl_sensex_summary.md) |  |
| Current | 2024–2026 | SENSEX Intraday ATM Straddle — 20% Ind. SL, Monthly Expiry (100 qty, 09:20–15:20, balance filter) | Profit | Rs 5L | Rs 2,52,845 | N/A | Rs 1,12,754 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_sensex_monthly_2024_2026_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — 20% Ind. SL, Weekly Expiry (~300 qty, 09:20–15:20, balance filter) | Profit | Rs 10L | Rs 2,16,384 | N/A | Rs 2,60,277 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_nifty_2020_2026_summary.md) |  |
| Current | 2024–2026 | SENSEX Intraday ATM Straddle — 20% Ind. SL, Weekly Expiry (100 qty, 09:20–15:20, balance filter) | Profit | Rs 5L | Rs 1,44,762 | N/A | Rs 1,72,031 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_sensex_2024_2026_summary.md) |  |
| Archived | 2025 | Short ATM Weekly Straddle 2025 | Loss | Rs 10L | Rs -10,824.00 | -1.08% | N/A | [Summary](../../results/legacy/short_atm_weekly_straddle_2025_summary.md) |  |
| Archived | 2025 | Gap Open ATM Straddle 09:15 2025 | Loss | Rs 10L | Rs -2,73,125.00 | -27.31% | N/A | [Summary](../../results/legacy-2/gap_open_atm_straddle_0915_2025_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — 20% Ind. SL, Monthly Expiry (~300 qty, 09:20–15:20, balance filter) | Loss | Rs 10L | Rs -1,54,701 | N/A | Rs 3,49,483 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_nifty_monthly_2020_2026_summary.md) |  |
