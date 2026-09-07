# Adjusted Straddle

ATM straddles that adjust as the market moves - when one side decays to half the other, sell more of the weak side, then unwind as the position comes back to parity.

- Scripts: [`backtesting/python/adjusted-straddle-half-add/`](../../python/adjusted-straddle-half-add/)
- Results: [`backtesting/results/adjusted-straddle-half-add/`](../../results/adjusted-straddle-half-add/)

**The settled spec from this family is written up in [strategy-weekly-adjusted-straddle.md](../strategy-weekly-adjusted-straddle.md).**

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
| Current | 2020-2026 | Adjusted ATM Straddle - Weekly, last 4 sessions to expiry (cap 3, OTM-vs-spot, +/-5 strike search, never skip) | Profit | Rs 6.49L | Rs 7,93,303 | 13.23% CAGR | Rs 63,497 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_hold4_stale_srch5_fb_cap3_summary.md) | Hold-matched control for the monthly row: same capital, same 4-session hold, same rules. 333 cycles vs monthly's 76 |

## Does avoiding expiry day help?

Barely on return, and **not at all on risk**. Closing one session before expiry
against holding to expiry day, identical entries, 6 years:

| | Net P/L | Max DD |
|---|---:|---:|
| Exit 1 session early | Rs 9,34,197 | Rs 41,246 |
| Hold to expiry day | Rs 9,54,046 | Rs 41,725 |

On every stress week the two are identical to the rupee - 2020-03-06,
2020-03-13, 2022-06-10 and 2025-04-04 all differ by exactly 0. Those weeks were
lost mid-week on the move itself; by expiry day the damage was already done.

So exit timing is an execution choice, not an edge. The `--mode roll` numbers
below look far better on drawdown, but this test is the clean isolation of the
same idea and it finds nothing - which is good reason to read the roll's
Rs 25,597 as a property of its calm 18-month window rather than of the mechanism.

## Rolling instead of expiring

Holding to 15:20 on expiry day has two problems the backtest was quietly
ignoring: the book went **flat overnight every week** between the expiry-day
exit and the next morning's entry, and it carried expiry-day gamma, where an ATM
straddle moves fastest and an adjustment is least likely to fill anywhere near
the recorded price.

`--mode roll` fixes both. It enters at 15:20 one session before expiry in the
*next* week's contract and rolls at 15:20 one session before that expiry, so the
old position closes and the new one opens in the same minute. Every cycle exits
with a full day of contract life left, and one cycle's exit day is the next
cycle's entry day.

On the 73 cycles where both can be measured (from 2024-12-24):

| | Cycles | Net P/L | Per cycle | Win rate | Max DD |
|---|---:|---:|---:|---:|---:|
| Roll, never holds expiry day | 73 | Rs 4,05,833 | Rs 5,559 | 75.3% | **Rs 25,597** |
| Held to expiry | 73 | Rs 3,56,517 | Rs 4,884 | 72.6% | Rs 55,647 |

The roll earns 14% more and halves the drawdown. Giving up the last day of
theta - normally the richest - costs less than the expiry-day gamma it avoids.

**This is an 18-month result, not a six-year one.** The roll must buy next
week's contract a day before this week expires, and until 2025 the dataset has
no bars for that contract until the morning after the current one expires:
pre-2025 weekly contracts carry exactly 5 sessions, starting the day after the
previous expiry. So 2020-2024 traded zero roll cycles. The same limitation means
the overnight flat gap in the held-to-expiry runs is not fixable on this data
either - the next contract genuinely is not there to roll into.

## Monthly vs weekly

Holding the same strategy on monthly contracts is worse, and the reason is
frequency rather than edge. Both rows below use the same capital base, the same
4-session hold, the same rules and the same six years, so the only difference is
the contract:

| Contract | Cycles | Per cycle | Net P/L | CAGR |
|---|---:|---:|---:|---:|
| Weekly | 333 | Rs 2,382 | Rs 7,93,303 | 13.23% |
| Monthly | 76 | Rs 2,078 | Rs 1,57,898 | 3.45% |
| Current | 2024-12 - 2026-06 | Adjusted ATM Straddle - Weekly continuous roll, never holds expiry day (cap 3, OTM-vs-spot, +/-5 strike search, never skip) | Profit | Rs 6.48L | Rs 4,05,833 | 39.05% CAGR | Rs 25,597 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_roll_otm_stale_srch5_fb_cap3_summary.md) | **73 cycles only** - the roll needs next week's contract to exist a day early, and pre-2025 data does not carry it. Beats held-to-expiry on the same 73 cycles: Rs 4,05,833 vs Rs 3,56,517, drawdown Rs 25,597 vs Rs 55,647 |
| Current | 2020-2026 | Adjusted ATM Straddle - **FINAL SPEC**: exit 1 session before expiry, ATM-only entry (cap 3, OTM-vs-spot) | Profit | Rs 6.45L | Rs 9,34,197 | 14.94% CAGR | Rs 41,246 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_cap3_summary.md) | 245 cycles, every year profitable. See [the spec](../strategy-weekly-adjusted-straddle.md) |
| Current | 2020-2026 | Adjusted ATM Straddle - exit 1 session before expiry, +/-5 strike search (cap 3, OTM-vs-spot) | Profit | Rs 6.48L | Rs 10,84,694 | 16.53% CAGR | Rs 99,098 | [Summary](../../results/adjusted-straddle-half-add/adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_srch5_cap3_summary.md) | 1.6 more CAGR points than the final spec for 2.4x the drawdown - the 77 extra weeks earn a third of a core week |

A monthly cycle earns 87% of what a weekly cycle earns - close enough that the
monthly contract is not the problem. There are simply **4.4x fewer of them** for
the same margin commitment, and the capital sits idle between expiries. That is
the whole gap.

The corollary is that the strategy's return is roughly linear in how often it
can be run, which is worth knowing before trying to improve it by tuning the
adjustment rules.

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
