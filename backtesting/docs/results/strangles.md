# Strangles

Short OTM strangles - overnight, intraday, weekly-held and adjusting variants. All runs here are archived.

- Results: archived under [`backtesting/results/legacy/`](../../results/legacy/) and [`backtesting/results/legacy-2/`](../../results/legacy-2/)
- Scripts: [`backtesting/python/legacy/`](../../python/legacy/) (archived - see that folder's README before running)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Combined Expiry + Adjusting Short Strangle 2025 | Profit | Rs 10L | Rs 2,52,042.69 | 25.20% | Rs 69,261.93 | [Summary](../../results/legacy-2/combined_expiry_adjusting_strangle_2025_summary.md) |  |
| Archived | 2025 | Weekly Adjusting Strangle Through Expiry 2025 | Profit | Rs 10L | Rs 1,48,016.27 | 14.80% | Rs 85,510.77 | [Summary](../../results/legacy-2/weekly_adjusting_strangle_through_expiry_2025_summary.md) |  |
| Archived | 2025 | Overnight OTM Strangle by Day — with fallback band (1 lot, 15:20–09:20 next day) | Loss | Rs 3L | Rs -26,781.25 | -8.93% | Rs 43,118.50 | [Summary](../../results/legacy/overnight_strangle_by_day_2025_summary.md) |  |
| Archived | 2025 | Intraday OTM Strangle Joint SL by Day — with fallback band (1 lot, 09:20–15:20, 2× joint SL) | Loss | Rs 3L | Rs -27,204.25 | -9.07% | Rs 35,332.00 | [Summary](../../results/legacy/intraday_joint_sl_strangle_2025_summary.md) |  |
| Archived | 2025 | Weekly Short Strangle 09:20 2025 | Loss | Rs 10L | Rs -1,47,728.40 | -14.77% | N/A | [Summary](../../results/legacy-2/weekly_short_strangle_0920_2025_summary.md) |  |
| Archived | 2024–2026 | Weekly Short Strangle — NIFTY+SENSEX Alternating (OTM, 1 lot each, 09:30–15:20, 2× SL) | Loss | Rs 5L | Rs -48,953 | N/A | Rs 66,567 | [Summary](../../results/legacy/weekly_strangle_nifty_sensex_2024_2026_summary.md) |  |
