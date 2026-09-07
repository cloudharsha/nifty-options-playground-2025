# 25-SMA Intraday

Short ATM options entered on a 25-period SMA signal and closed the same session, with trailing stops, stop-loss caps, MA-gap filters and random-skip robustness runs.

- Scripts: [`backtesting/python/25ma-intraday/`](../../python/25ma-intraday/)
- Results: [`backtesting/results/25ma-intraday/`](../../results/25ma-intraday/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Short ATM NIFTY MA Weekly Intraday Trailing 2025 | Profit | Rs 10L | Rs 6,60,341.40 | 66.03% | Rs 1,30,612.40 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md) | [6Y: 31.48% CAGR](../../results/25ma-intraday/base/short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_summary.md) |
| Archived | 2025 | Short ATM MA Same-Week 15m Trailing Intraday Entry 2025 | Profit | Rs 10L | Rs 5,10,661.20 | 51.07% | N/A | [Summary](../../results/legacy/short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md) | [6Y: 1.76% CAGR](../../results/25ma-intraday/same-week/short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_summary.md) |
| Archived | 2025 | Short ATM MA Same-Week 15m 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](../../results/legacy/short_atm_ma_same_week_15m_2025_summary.md) |  |
| Archived | 2025 | Short ATM MA Same-Week 15m Trailing 2025 | Profit | Rs 10L | Rs 4,93,017.00 | 49.30% | N/A | [Summary](../../results/legacy/short_atm_ma_same_week_15m_trailing_2025_summary.md) |  |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 Entry, 30% Random Skip (5 runs avg) | Profit | Rs 10L | Rs 68,20,328 avg | 31.72% CAGR avg | Rs 1,14,299 avg | [Summary](../../results/25ma-intraday/random-skip/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_summary.md) | 40% skip: 29.24%, 50% skip: 26.47%; avg of 5 seeds per rate |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing (5m stop) | Profit | Rs 10L | Rs 67,11,939 | 31.48% CAGR | Rs 1,36,705 | [Summary](../../results/25ma-intraday/base/short_atm_nifty_ma_weekly_intraday_trailing_2020_2026_summary.md) | [2025: 66.03%](../../results/legacy/short_atm_nifty_ma_weekly_intraday_trailing_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 Entry, 2-SL/Day Cap, 30% Random Skip (5 runs avg) | Profit | Rs 10L | Rs 51,08,988 avg | 27.43% CAGR avg | Rs 1,16,493 avg | [Summary](../../results/25ma-intraday/with-sl-cap/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_summary.md) | 40% skip: 25.21%, 50% skip: 22.55%; halt after 2 SL/day |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤150pts, 30% Skip (5 runs avg) | Profit | Rs 10L | Rs 42,92,189 avg | 24.99% CAGR avg | Rs 1,42,824 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: 22.77%, 50% skip: 20.46%; skip entry if \ | close−SMA\ | > 150 |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤125pts, 30% Skip (5 runs avg) | Profit | Rs 10L | Rs 39,54,349 avg | 23.88% CAGR avg | Rs 1,40,008 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: 21.57%, 50% skip: 19.45%; skip entry if \ | close−SMA\ | > 125 |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤100pts, 30% Skip (5 runs avg) | Profit | Rs 10L | Rs 36,49,025 avg | 22.83% CAGR avg | Rs 1,21,120 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: 20.62%, 50% skip: 18.52%; skip entry if \ | close−SMA\ | > 100 |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Intraday Trailing — 09:20 + 2-SL Cap + MA Gap ≤75pts, 30% Skip (5 runs avg) | Profit | Rs 10L | Rs 32,23,660 avg | 21.26% CAGR avg | Rs 1,00,874 avg | [Summary](../../results/25ma-intraday/with-magap-filter/short_atm_nifty_ma_weekly_intraday_trailing_0920_random_2slcap_magap_summary.md) | 40% skip: 19.09%, 50% skip: 17.14%; skip entry if \ | close−SMA\ | > 75 |
| Current | 2020–2026 | Short ATM MA Same-Week 15m Trailing Intraday Entry | Profit | Rs 10L | Rs 1,39,007 | 1.76% CAGR | Rs 6,38,220 | [Summary](../../results/25ma-intraday/same-week/short_atm_ma_same_week_15m_trailing_intraday_entry_2020_2026_summary.md) | [2025: 51.07%](../../results/legacy/short_atm_ma_same_week_15m_trailing_intraday_entry_2025_summary.md) |
| Archived | 2025 | Short ATM Same-Week Intraday SL 2025 | Loss | Rs 10L | Rs -1,23,796.40 | -12.38% | N/A | [Summary](../../results/legacy-2/short_atm_same_week_intraday_sl_2025_summary.md) |  |
| Current | 2020-2026 | Short ATM NIFTY MA Weekly Intraday Trailing - random-skip sweep baseline | Profit | Rs 10L | Rs 67,11,939 | 31.48% CAGR | Rs 1,36,705 | [Summary](../../results/25ma-intraday/random-skip/short_atm_nifty_ma_weekly_intraday_trailing_random_summary.md) | The 0%-skip control inside the random sweep; same underlying run as the trailing baseline row |
