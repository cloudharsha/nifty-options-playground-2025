# Iron Condors & Flies

Defined-risk short premium: sell a strangle, buy wings. Includes weekly rolls and the intraday variant.

- Scripts: [`backtesting/python/iron-condor/`](../../python/iron-condor/)
- Results: [`backtesting/results/iron-condor/`](../../results/iron-condor/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Short Iron Condor Next Week 2025 | Loss | Rs 10L | Rs -21,321.20 | -2.13% | N/A | [Summary](../../results/legacy/short_iron_condor_next_week_2025_summary.md) |  |
| Archived | 2025 | Short Iron Fly 2025 | Loss | Rs 10L | Rs -4,33,828.60 | -43.38% | N/A | [Summary](../../results/legacy/short_iron_fly_2025_summary.md) |  |
| Archived | ~4Y | Weekly Short Iron Condor Roll 2022-2026 (1 lot, sell ±250, hedge ±450, 09:15 entry, 15:15 exit on expiry) | Loss | Rs 10L | Rs -68,495.25 | N/A | N/A | [Summary](../../results/legacy/weekly_iron_condor_roll_2020_2026_summary.md) |  |
| Current | ~4Y | NIFTY Intraday Iron Condor — Weekly (~300 qty, May 2022–2026, sell ±250, hedge ±450, 09:20–15:20, no SL) | Loss | Rs 10L | Rs -22,87,219 | N/A | N/A | [Summary](../../results/iron-condor/intraday_iron_condor_weekly_2020_2026_summary.md) |  |
| Current | 2020-2026 | NIFTY Weekly Iron Condor - expiry day (1 lot) | Loss | Rs 10L | -Rs 22,25,574 | -100.00% CAGR | Rs 22,55,596 | [Summary](../../results/iron-condor/nifty_iron_condor_weekly_expiry_2020_2026_summary.md) | 26.2% win rate; the Rs 10L reference base is fully wiped out |
