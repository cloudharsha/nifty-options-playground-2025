# Heads & Tails (Random Entry)

Coin-flip entry baselines. These exist to answer 'is the signal doing anything?' - if a strategy cannot beat a random-entry control on the same instrument and costs, the signal is not earning its keep.

- Scripts: [`backtesting/python/heads-tails/`](../../python/heads-tails/)
- Results: [`backtesting/results/heads-tails/`](../../results/heads-tails/)

Back to the [backtesting index](../../README.md).

> **Audited 2026-09-08 for the lookahead bugs found in the 25-SMA families —
> clean, numbers unchanged.** `resolve_sell_leg` checks the bar open first (so a
> gap through the level fills at the gapped price), then fills a triggered stop
> or target at the level itself rather than at the bar's open. That is the
> correct treatment for a resting order. Because this control is sound and the
> directional strategies were not, it is now the top row of the
> [headline table](../../README.md#headline-six-year-runs). See the
> [lookahead audit](../lookahead-audit.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Current | ~6Y | Heads & Tails Grid — Short ATM NIFTY Weekly (20 combos × 5 runs; best: SL=40%, T=open) | Profit | Rs 5L | Rs 9,73,379 avg | 17.38% avg CAGR | Rs 4,81,637 avg | [Summary](../../results/heads-tails/heads_tails_nifty_grid_summary.md) |  |
| Current | ~6Y | Heads & Tails — Random Short ATM NIFTY Weekly (5 runs avg; SL=20%, T=50%, 09:30–15:20, noon re-entry) | Profit | Rs 5L | Rs 4,38,958 avg | ~9.84% avg CAGR | Rs 3,25,433 avg | [Summary](../../results/heads-tails/heads_tails_nifty_summary.md) |  |
| Current | ~6Y | Heads & Tails Grid — LONG ATM NIFTY Weekly (28 combos × 5 runs; best: SL=20%, T=90%) | Loss | Rs 5L | Rs -7,56,517 avg | -86.29% avg CAGR | N/A | [Summary](../../results/heads-tails/heads_tails_nifty_grid_long_summary.md) |  |
