# Finalized strategies

Strategies that finished testing and settled on a configuration worth trading.

Everything else in [`../results/`](../results/) is exploration — variants, dead
ends, and sweeps. This folder holds only the conclusions, each with its rules
written out and a frozen copy of the result files behind its numbers. Re-running
a backtest overwrites `../results/`, never this folder.

| Strategy | Instrument | CAGR | Max DD | Effort | Details |
|---|---|---:|---:|---|---|
| [Weekly Adjusted ATM Straddle](weekly-adjusted-straddle/) | NIFTY weekly options, 1 lot | 13.19% | Rs 42,159 | ~6 adjustments/week | [README](weekly-adjusted-straddle/README.md) |

## Reading these

Each folder contains:

- `README.md` — the rules in full, the results, what was rejected and why, and
  what would invalidate the strategy
- `results/` — the exact `_summary.md`, `_cycles.csv`, `_legs.csv` and
  `_equity.csv` the numbers came from

CAGR is quoted against the **peak margin the position actually reaches**, not a
round reference figure, so it reflects capital you would really have to post.
Those margin estimates are modelled rather than SPAN output — each README says so
and names the number to verify with a broker before sizing.

Nothing here is advice. A backtest assumes fills that live markets may not offer,
and every strategy in this folder is short premium with real tail risk.
