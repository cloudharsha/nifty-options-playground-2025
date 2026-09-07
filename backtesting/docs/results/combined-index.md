# Combined NIFTY + SENSEX

Strategies that trade both indices, routing each weekday to whichever index has a weekly expiry that suits it.

- Scripts: [`backtesting/python/combined-index/`](../../python/combined-index/)
- Results: [`backtesting/results/combined-index/`](../../results/combined-index/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Current | Sep 25+ | Combined NIFTY+SENSEX ATM Straddle — Expiry-Incl., no balance filter (Mon/Tue/Fri=NIFTY ~300 qty, Wed/Thu=SENSEX 100 qty) | Profit | Rs 5L | Rs 27,012 | 6.90% CAGR | Rs 1,32,821 | [Summary](../../results/combined-index/combined_nifty_sensex_expiry_incl_2025_summary.md) |  |
| Current | Sep 25+ | Combined Balanced-Strike ATM Straddle — NIFTY+SENSEX (161 days, 9 SL levels tested; best SL=50%) | Profit | Rs 5L | Rs 10,361 | 2.6% CAGR | Rs 1,57,613 | [Summary](../../results/combined-index/combined_nifty_sensex_balanced_strike_2025_summary.md) |  |
| Current | Sep 25+ | Combined Short OTM Strangle — NIFTY+SENSEX (153 days, 9 SL levels tested; best SL=90%) | Loss | Rs 5L | Rs -21,010 | -5.3% CAGR | Rs 49,425 | [Summary](../../results/combined-index/combined_strangle_2025_summary.md) |  |
