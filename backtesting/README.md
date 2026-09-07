# Backtesting

Every strategy in this repo lives here: the runner scripts, the generated
results, and the index that ties them together.

The layout has one rule — **`python/<family>/` and `results/<family>/` mirror
each other**. Find a strategy in one and you know where its output is.

```
backtesting/
  docs/
    dataset-reference.md      data schema, lot-size eras, expiry-day history
    results/                  one index doc per strategy family
  python/
    _template/example.py      copy this to start a new strategy
    <family>/                 runner scripts
    legacy/                   archived, does not run as-is
    tests/
  results/
    <family>/                 generated output
    legacy/ legacy-2/         archived runs
```

## Results by strategy family

| Family | What it tests | Runs |
|---|---|---:|
| [25-SMA Intraday](docs/results/25ma-intraday.md) | Short ATM on a 25-SMA signal, closed same session | 14 |
| [25-SMA Overnight](docs/results/25ma-overnight.md) | Same signal carried overnight to weekly expiry, plus the strike-offset sweep | 23 |
| [Adjusted Straddle](docs/results/adjusted-straddle.md) | ATM straddle that adds to the weak side as the market moves, then unwinds | 14 |
| [Intraday Straddle](docs/results/intraday-straddle.md) | Plain ATM straddle, one session, independent or joint stops | 11 |
| [Iron Condors & Flies](docs/results/iron-condor.md) | Defined-risk short premium | 5 |
| [Strangles](docs/results/strangles.md) | Short OTM strangles, various holds | 6 |
| [Combined NIFTY + SENSEX](docs/results/combined-index.md) | Routes each weekday to whichever index suits it | 3 |
| [Human-Compatible](docs/results/combined-human.md) | 15-minute checks and GTT orders instead of constant monitoring | 3 |
| [Heads & Tails](docs/results/heads-tails.md) | Random-entry controls | 3 |
| [Directional & Signal Studies](docs/results/directional-studies.md) | Underlying-only signal tests | 9 |

### Headline six-year runs

Only 2020–2026 runs appear here, because a single-year return and a six-year
CAGR are not comparable numbers.

| Strategy | Net P/L | CAGR | Max DD |
|---|---:|---:|---:|
| [25-SMA intraday trailing, 09:20 entry, 30% random skip](docs/results/25ma-intraday.md) | Rs 68,20,328 | 31.72% | Rs 1,14,299 |
| [25-SMA overnight, ITM 200 offset](docs/results/25ma-overnight.md) | Rs 27,36,233 | 19.32% | Rs 2,70,220 |
| [Heads & Tails random-entry control](docs/results/heads-tails.md) | Rs 9,73,379 | 17.38% | Rs 4,81,637 |
| [Adjusted straddle, held to expiry, 3-leg cap](docs/results/adjusted-straddle.md) | Rs 9,54,046 | 15.16% | Rs 41,725 |

The random-entry control sits third. That is the point of running it: any
signal-based strategy below ~17% CAGR on this instrument has not yet shown
that its signal beats a coin flip on the same costs.

## Running a backtest

Python 3.13, standard library only — no dependencies to install. Every script
is standalone and takes `--help`.

```bash
# from the repo root
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode expiry --start-date 2025-01-01 --end-date 2025-03-31
```

Each script defaults `--results-dir` to its own `results/<family>/` folder, so
a re-run overwrites that strategy's output and nothing else. Market data paths
default to the layout described in the [root README](../README.md#data-layout);
the data is not in this repo.

Tests run one file at a time (there is no package, so `unittest discover` will
not work):

```bash
python backtesting/python/tests/test_run_weekly_short_strangle_0920_2025.py
```

## Reading the numbers

Read this before comparing rows across families.

- **Capital Base is not consistent between strategies, on purpose.** Most rows
  use a fixed reference base (Rs 10L for short-option runs, Rs 2.5L for futures,
  Rs 3L for 1-lot intraday). The adjusted-straddle rows instead use the
  *estimated peak margin the position actually reaches*, because those
  strategies stack up to 12 short legs — on a fixed base they would report
  25.65% where the honest figure is 7.21%. A CAGR is only as meaningful as the
  capital it is measured against.
- **CAGR vs total return.** Multi-year rows show CAGR; single-year rows show
  total return for that year. Do not rank them against each other.
- **Costs are modelled, fills are not.** Brokerage and taxes are charged per
  order. Every backtest assumes it got filled at the recorded price, which is
  optimistic for illiquid strikes and for gap days.
- **Skipped days matter.** Several strategies decline to trade when an entry
  filter fails. A high skip rate can mean the filter is doing real work, or that
  the sample is thin — the per-strategy summaries report skip counts and reasons.
- **Max DD is in rupees**, measured on the equity curve of that run.

Contract conventions that change P/L — lot-size eras, the Thursday-to-Tuesday
expiry switch, strike intervals — are in
[docs/dataset-reference.md](docs/dataset-reference.md). Getting the lot size
wrong silently scales every number in a run.

## Adding a strategy

See [Contributing](../README.md#contributing) in the root README.
