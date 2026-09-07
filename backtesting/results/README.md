# Results

Generated output, one folder per strategy family, mirroring
[`../python/`](../python/). Nothing here is written by hand — every file is
produced by a script and is safe to delete and regenerate.

Browse the numbers through the [index docs](../docs/results/) rather than these
folders; the index is where the runs are described and compared.

| Folder | Produced by | Index |
|---|---|---|
| [`25ma-intraday/`](25ma-intraday/) | [`python/25ma-intraday/`](../python/25ma-intraday/) | [index](../docs/results/25ma-intraday.md) |
| [`25ma-overnight/`](25ma-overnight/) | [`python/25ma-overnight/`](../python/25ma-overnight/) | [index](../docs/results/25ma-overnight.md) |
| [`adjusted-straddle-half-add/`](adjusted-straddle-half-add/) | [`python/adjusted-straddle-half-add/`](../python/adjusted-straddle-half-add/) | [index](../docs/results/adjusted-straddle.md) |
| [`intraday-straddle/`](intraday-straddle/) | [`python/intraday-straddle/`](../python/intraday-straddle/) | [index](../docs/results/intraday-straddle.md) |
| [`combined-index/`](combined-index/) | [`python/combined-index/`](../python/combined-index/) | [index](../docs/results/combined-index.md) |
| [`combined-human/`](combined-human/) | [`python/combined-human/`](../python/combined-human/) | [index](../docs/results/combined-human.md) |
| [`heads-tails/`](heads-tails/) | [`python/heads-tails/`](../python/heads-tails/) | [index](../docs/results/heads-tails.md) |
| [`iron-condor/`](iron-condor/) | [`python/iron-condor/`](../python/iron-condor/) | [index](../docs/results/iron-condor.md) |
| [`legacy/`](legacy/), [`legacy-2/`](legacy-2/) | [`python/legacy/`](../python/legacy/) (archived) | [strangles](../docs/results/strangles.md), [studies](../docs/results/directional-studies.md) |

## File naming

Every artifact is `<base>` plus a fixed suffix, so the base name joins them:

| Suffix | Contents |
|---|---|
| `_summary.md` | The report — parameters, headline P/L, yearly breakdown, skip reasons |
| `_trades.csv` | One row per trade or leg |
| `_daywise.csv` | One row per session |
| `_cycles.csv`, `_legs.csv`, `_equity.csv` | Per-cycle, per-leg and equity-curve detail |

Parameter sweeps encode the parameters in the base name rather than nesting,
e.g. `..._gap100_skip30_run1_trades.csv` for gap 100 / 30% skip / seed 1.

Two things are deliberately untracked in git: `.log` files, and the two
heads-tails grid `_daywise.csv` dumps (67 MB). All are regenerable by re-running
the script. See the root `.gitignore`.
