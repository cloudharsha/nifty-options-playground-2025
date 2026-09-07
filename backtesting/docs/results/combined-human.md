# Human-Compatible Strategy

A deliberately low-attention strategy: check the market every 15 minutes, set GTT-equivalent stop and target orders at entry, and stop trading for the day after two stop-outs.

- Scripts: [`backtesting/python/combined-human/`](../../python/combined-human/)
- Results: [`backtesting/results/combined-human/`](../../results/combined-human/)

Back to the [backtesting index](../../README.md).

> **Audited 2026-09-08 for the lookahead bugs found in the 25-SMA families —
> clean, own numbers unchanged.** `resolve_trade_exit_human` reads the last
> *completed* 15-minute candle and fills at the open of the candle starting at
> the check time, which is after that signal candle closed. Correct causality.
>
> One caveat on the two variant folders: `test-no-premsl/` and `test-wide-sl/`
> summaries carry a "vs base intraday" comparison table that still quotes the
> pre-fix 25-SMA figures (31.48% / 27.43%). The base run was regenerated with
> corrected references; the two variants were not, because their summaries do
> not record every parameter they were run with and re-running them from the
> displayed parameters does not reproduce their numbers. Their own results are
> unaffected — read the comparison rows in those two files against the
> [lookahead audit](../lookahead-audit.md) instead.

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Current | 2020-2026 | Human-Compatible Intraday - 15-min checks, GTT SL/target, 2 SL/day cap (base) | Loss | Rs 10L | -Rs 3,41,725 | -5.45% CAGR | Rs 7,90,135 | [Summary](../../results/combined-human/combined_human_strategy_2020_2026_summary.md) | 1,851 days, 53.2% win days. The low-attention framing does not rescue the edge |
| Current | 2020-2026 | Human-Compatible Intraday - no premium stop | Loss | Rs 10L | -Rs 4,45,047 | -7.59% CAGR | Rs 10,20,915 | [Summary](../../results/combined-human/test-no-premsl/combined_human_strategy_2020_2026_summary.md) | Removing the premium stop makes it worse, not better |
| Current | 2020-2026 | Human-Compatible Intraday - wide stop | Loss | Rs 10L | -Rs 5,11,387 | -9.15% CAGR | Rs 10,34,800 | [Summary](../../results/combined-human/test-wide-sl/combined_human_strategy_2020_2026_summary.md) | Widest stop, worst result of the three |

