# 25-SMA Intraday

Short ATM options entered on a 25-period SMA signal and closed the same session, with trailing stops, stop-loss caps, MA-gap filters and random-skip robustness runs.

- Scripts: [`backtesting/python/25ma-intraday/`](../../python/25ma-intraday/)
- Results: [`backtesting/results/25ma-intraday/`](../../results/25ma-intraday/)

Back to the [backtesting index](../../README.md).

> **Corrected 2026-09-08 — every "Current" row below changed sign.**
> Three lookahead bugs were found in these scripts: the trailing stop filled at
> the option open of the very 5-minute bar whose high/low triggered it (a price
> from before the stop existed), and the 09:20 entry took its direction from the
> 09:15 15-minute bar, which does not close until 09:30. With both fixed, no
> variant in this family is profitable. Full detail and the pre-fix numbers are
> in the [lookahead audit](../lookahead-audit.md). The "Archived" 2025 rows were
> produced by `python/legacy/` scripts that are not runnable and were **not**
> re-run; they still carry the bug.


Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Short ATM NIFTY MA Weekly Intraday Trailing 2025 | Profit | Rs 10L | Rs 6,60,341.40 | 66.03% | Rs 1,30,612.40 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md) | [6Y (corrected): −100% CAGR](../../results/25ma-intraday/base/short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_summary.md) |
| Archived | 2025 | Short ATM MA Same-Week 15m Trailing Intraday Entry 2025 | Profit | Rs 10L | Rs 5,10,661.20 | 51.07% | N/A | [Summary](../../results/legacy/short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md) | [6Y: 1.76% CAGR](../../results/25ma-intraday/same-week/short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_summary.md) |
| Archived | 2025 | Short ATM MA Same-Week 15m 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](../../results/legacy/short_atm_ma_same_week_15m_2025_summary.md) |  |
| Archived | 2025 | Short ATM MA Same-Week 15m Trailing 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](../../results/legacy/short_atm_ma_same_week_15m_trailing_2025_summary.md) |  |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 Entry, 30% Random Skip (5 runs avg) | Loss | Rs 10L | −Rs 11,68,852 avg | −69.06% CAGR avg | Rs 17,00,452 avg | [Summary](../../results/25ma-intraday/random-skip/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_summary.md) | 40% skip: −51.39%, 50% skip: −39.07%; avg of 5 seeds per rate |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing (5m stop) | Loss | Rs 10L | −Rs 14,15,087 | −100% (wiped out) | Rs 19,86,026 | [Summary](../../results/25ma-intraday/base/short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_summary.md) | [2025: 66.03%](../../results/legacy/short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 Entry, 2-SL/Day Cap, 30% Random Skip (5 runs avg) | Loss | Rs 10L | −Rs 2,05,723 avg | −3.63% CAGR avg | Rs 8,47,288 avg | [Summary](../../results/25ma-intraday/with-sl-cap/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_summary.md) | 40% skip: −3.77%, 50% skip: −4.40%; halt after 2 SL/day |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤150pts, 30% Skip (5 runs avg) | Loss | Rs 10L | −Rs 3,13,403 avg | −6.38% CAGR avg | Rs 9,23,108 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: −6.35%, 50% skip: −6.22%; skip entry if \ | close−SMA\ | > 150 |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤125pts, 30% Skip (5 runs avg) | Loss | Rs 10L | −Rs 3,24,239 avg | −6.48% CAGR avg | Rs 8,58,006 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: −7.31%, 50% skip: −6.76%; skip entry if \ | close−SMA\ | > 125 |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤100pts, 30% Skip (5 runs avg) | Loss | Rs 10L | −Rs 2,04,727 avg | −3.87% CAGR avg | Rs 7,80,258 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: −4.73%, 50% skip: −5.13%; skip entry if \ | close−SMA\ | > 100 |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤75pts, 30% Skip (5 runs avg) | Loss | Rs 10L | −Rs 1,19,994 avg | −2.27% CAGR avg | Rs 6,31,263 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: −2.80%, 50% skip: −3.53%; skip entry if \ | close−SMA\ | > 75 |
| Current | 2020–2026 | Short ATM MA Same-Week 15m Trailing Intraday Entry | Profit | Rs 10L | Rs 1,39,007 | 1.76% CAGR | Rs 6,38,220 | [Summary](../../results/25ma-intraday/same-week/short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_summary.md) | [2025: 51.07%](../../results/legacy/short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md) |
| Archived | 2025 | Short ATM Same-Week Intraday SL 2025 | Loss | Rs 10L | Rs -1,23,796.40 | -12.38% | N/A | [Summary](../../results/legacy-2/short_atm_same_week_intraday_sl_2025_summary.md) |  |
| Current | 2020-2026 | Short ATM NIFTY MA Weekly Intraday Trailing - random-skip sweep, 30% skip (5 runs avg) | Loss | Rs 10L | −Rs 4,13,558 avg | −7.85% CAGR avg | Rs 7,86,325 avg | [Summary](../../results/25ma-intraday/random-skip/short_atm_nifty_ma_weekly_intraday_trailing_random_summary.md) | 09:30-entry sweep; the 09:20 variant is a separate row above |
