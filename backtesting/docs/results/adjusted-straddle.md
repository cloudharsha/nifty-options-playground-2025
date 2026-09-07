# Adjusted Straddle

ATM straddles that adjust as the market moves - when one side decays to half the other, sell more of the weak side, then unwind as the position comes back to parity.

- Scripts: [`backtesting/python/adjusted-straddle-half-add/`](../../python/adjusted-straddle-half-add/)
- Results: [`backtesting/results/adjusted-straddle-half-add/`](../../results/adjusted-straddle-half-add/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Current | 2024-12–2026-05 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Monthly, Held to Expiry (1 lot, 3-leg cap + 75% roll, adds OTM vs spot) | Profit | Rs 6.50L | Rs 2,25,074 | 23.30% CAGR | Rs 62,476 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_monthly_stale_srch5_cap3_summary.md) | **Only 16 cycles.** Dataset carries just 3-5 days per monthly contract before 2025, so 2020–2024 is untestable; 60 of 76 cycles skipped. Weekly earned Rs 3,22,456 over the same window |
| Archived | 2025 | Intraday Adjusted Weekly Straddle 2025 | Profit | Rs 10L | Rs 1,77,017.00 | 17.70% | N/A | [Summary](../../results/legacy/intraday_adjusted_straddle_2025_summary.md) |  |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Weekly, Held to Expiry (no balance filter, ATM only) | Profit | Rs 6.45L | Rs 10,57,265 | 16.28% CAGR | Rs 75,972 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_stale_nobal_cap3_summary.md) | 329 cycles; more total profit than the filtered run but 1.8x the drawdown — the balance filter is doing real work |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Weekly, Held to Expiry (±5 strike search, never skip on balance) | Profit | Rs 6.48L | Rs 10,55,508 | 16.23% CAGR | Rs 99,098 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_stale_srch5_fb_cap3_summary.md) | 331 cycles; shift entry strike until CE/PE balance, enter best available if none qualifies |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Weekly, Held to Expiry (±5 strike search, skip if none balanced) | Profit | Rs 6.48L | Rs 10,43,869 | 16.10% CAGR | Rs 99,098 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_stale_srch5_cap3_summary.md) | 322 cycles; entries: 245 at ATM, 58 at +50, 11 at −50, 7 at +100, 1 at +200. Per-cycle profit falls Rs 3,894 → Rs 3,242 vs the filtered baseline |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Weekly, Held to Expiry (1 lot, 3-leg cap + 75% roll, adds OTM vs spot) | Profit | Rs 6.45L | Rs 9,54,046 | 15.16% CAGR | Rs 41,725 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_cap3_summary.md) | **Best config.** 245 cycles, PF 2.91, win 68.98%, max 4 legs; 1,879 adds / 1,585 unwinds / 565 rolls |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Weekly, Held to Expiry (1 lot, adds only further OTM than existing legs) | Profit | Rs 5.12L | Rs 6,37,350 | 13.41% CAGR | Rs 73,688 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_summary.md) | PF 1.64; 3-leg cap never binds under this rule (0 rolls) — adjustment disengages in fast crashes |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Weekly, Held to Expiry (1 lot, uncapped adds, OTM vs spot) | Profit | Rs 17.77L | Rs 10,03,013 | 7.21% CAGR | Rs 91,539 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_summary.md) | Highest gross (PF 3.17) but stacked to 12 legs; worst cycle −Rs 81,568 |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Intraday (1 lot, adds only further OTM than existing legs) | Profit | Rs 4.53L | Rs 66,485 | 2.15% CAGR | Rs 1,27,548 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_intraday_summary.md) | 893 cycles; costs Rs 1,81,920 = 73% of gross |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Intraday (1 lot, 3-leg cap + 75% roll, adds OTM vs spot) | Profit | Rs 6.49L | Rs 60,386 | 1.39% CAGR | Rs 87,323 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_intraday_otm_cap3_summary.md) | Same rules as the 15.16% expiry row — the timeframe is what kills it; costs Rs 2,50,920 = 81% of gross |
| Current | 2020–2026 | Adjusted ATM Straddle — Half-Trigger / 25% Add — Intraday (1 lot, uncapped adds, OTM vs spot) | Profit | Rs 12.17L | Rs 41,517 | 0.52% CAGR | Rs 1,04,380 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_intraday_otm_summary.md) | Costs Rs 2,51,460 = 86% of gross |
| Current | 2020-2026 | Adjusted ATM Straddle - Weekly held to expiry (beyond-legs adds, 3-leg cap) | Profit | Rs 5.12L | Rs 6,37,350 | 13.41% CAGR | Rs 73,688 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_cap3_summary.md) | Identical to the uncapped beyond-legs run - the 3-leg cap never binds under that strike rule (0 rolls) |
| Current | 2020-2026 | Adjusted ATM Straddle - Weekly held to expiry (cap 3, OTM-vs-spot, stale-entry probe) | Profit | Rs 6.45L | Rs 9,54,046 | 15.16% CAGR | Rs 41,725 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_stale_cap3_summary.md) | Byte-identical traded set to the main cap-3 run: relaxing the entry-bar rule recovers zero weeks, so the data skips carry no survivorship bias |
| Current | 2020-2026 | Adjusted ATM Straddle - Monthly contracts, intraday (cap 3, OTM-vs-spot) | Profit | Rs 6.49L | Rs 90,859 | 2.06% CAGR | Rs 35,735 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_intraday_otm_monthly_stale_srch5_cap3_summary.md) | Only 540 of 1,606 days traded - before 2025 the dataset carries just the final week of each monthly contract |
| Current | 2020-2026 | Adjusted ATM Straddle - Monthly contracts, last 4 sessions to expiry (cap 3, OTM-vs-spot, +/-5 strike search, never skip) | Profit | Rs 6.49L | Rs 1,57,898 | 3.45% CAGR | Rs 41,016 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_monthly_hold4_stale_srch5_fb_cap3_summary.md) | All 76 monthly cycles traded, no skips. 2022 and 2023 lose; win rate 45-58% every year, barely above a coin flip |

## A note on the monthly rows

There are two, and they are not variants of each other - they answer different
questions, because the dataset constrains what a monthly test can even be.

Until 2025 the data carries only the **final 3-5 trading days** of each monthly
contract's life. A full-month hold therefore cannot be tested before 2025: the
`2024-12 - 2026-05` row is the honest extent of it, 16 cycles.

Clamping the hold to the last 4 sessions makes the whole 6 years testable - all
76 monthly cycles, no skips - and has the side benefit of matching the weekly
runs' holding period, so the comparison isolates the contract rather than
confounding it with hold length.
