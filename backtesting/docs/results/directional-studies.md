# Directional & Signal Studies

Underlying-only and single-leg studies used to test signals before wiring them into an options strategy: SMA crossovers, continuous trailing, gap opens and streak-following.

- Results: archived under [`backtesting/results/legacy/`](../../results/legacy/) and [`backtesting/results/legacy-2/`](../../results/legacy-2/)
- Scripts: [`backtesting/python/legacy/`](../../python/legacy/) (archived - see that folder's README before running)

Back to the [backtesting index](../../README.md).

> **Not audited, not re-run — treat every row as an upper bound.** These scripts
> live in the deliberately non-functional `python/legacy/` folder, so the
> [lookahead fixes](../lookahead-audit.md) applied to the 25-SMA families were
> not applied here and these numbers were not regenerated. They carry a second,
> larger problem of their own: each summary states "No brokerage, slippage,
> lots, or option data are used". At this repo's own convention (Rs 25/order
> plus 1 pt/order slippage, 1 pt = Rs 65) that is roughly Rs 180 per round trip
> — about Rs 7.75L of the Rs 11.88L headline on the 4,306-trade continuous
> trailing run, and enough to leave the two crossover rows barely positive.
> Reviving one of these means fixing the folder's path bugs, adding costs,
> checking causality, and indexing it as a new result.

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 4Y | NIFTY 25-SMA Continuous Trailing 15m | Profit | Rs 2.5L | Rs 11,88,295.55 | 54.88% CAGR | Rs 1,65,540.05 | [Summary](../../results/legacy/nifty_ma_continuous_trailing_15m_summary.md) |  |
| Archived | 4Y | NIFTY 25-SMA Overnight Movement 15m | Profit | Rs 2.5L | Rs 10,50,786.75 | 51.03% CAGR | Rs 74,750.00 | [Summary](../../results/legacy/nifty_ma_overnight_movement_15m_summary.md) |  |
| Archived | 4Y | NIFTY 25-SMA Intraday Trailing 15m | Profit | Rs 2.5L | Rs 5,63,707.95 | 34.31% CAGR | Rs 93,377.70 | [Summary](../../results/legacy/nifty_ma_intraday_trailing_15m_summary.md) |  |
| Archived | 4Y | NIFTY 25/50 SMA Crossover 2R | Profit | Rs 2.5L | Rs 1,95,734.50 | 15.55% CAGR | Rs 1,16,119.25 | [Summary](../../results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |  |
| Archived | 4Y | NIFTY 25/50 SMA Crossover 3R | Profit | Rs 2.5L | Rs 1,76,514.00 | 14.29% CAGR | Rs 1,31,488.50 | [Summary](../../results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |  |
| Archived | 4Y | NIFTY Last 3 Same-Color Overnight 15m | Profit | Rs 2.5L | Rs 1,50,712.25 | 12.52% CAGR | Rs 46,143.50 | [Summary](../../results/legacy-2/nifty_last_3_green_overnight_15m_summary.md) |  |
| Archived | 2025 | Expiry ITM 100 MA Short 09:20 2025 | Profit | Rs 10L | Rs 15,760.60 | 1.58% | Rs 2,40,921.00 | [Summary](../../results/legacy-2/expiry_itm100_ma_short_0920_2025_summary.md) |  |
| Archived | 2025 | Gap 100 ATM Option 09:16 2025 | Loss | Rs 10L | Rs -5,696.40 | -0.57% | N/A | [Summary](../../results/legacy-2/gap_100_atm_option_0916_2025_summary.md) |  |
| Archived | 4Y | NIFTY 25/50 SMA Crossover 1R | Loss | Rs 2.5L | Rs -74,993.75 | -8.53% CAGR | Rs 1,47,403.75 | [Summary](../../results/legacy/nifty_ma_25_50_crossover_rr_15m_summary.md) |  |
