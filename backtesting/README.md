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

**[Finalized strategies](finalized/)** — the ones that finished testing, with rules,
frozen results and the rejected alternatives. Start there if you want the conclusions
rather than the exploration.

## Results by strategy family

| Family | What it tests | Runs |
|---|---|---:|
| [25-SMA Intraday](docs/results/25ma-intraday.md) | Short ATM on a 25-SMA signal, closed same session | 14 |
| [25-SMA Overnight](docs/results/25ma-overnight.md) | Same signal carried overnight to weekly expiry, plus the strike-offset sweep | 23 |
| [Adjusted Straddle](docs/results/adjusted-straddle.md) | ATM straddle that adds to the weak side as the market moves, then unwinds | 15 |
| [Intraday Straddle](docs/results/intraday-straddle.md) | Plain ATM straddle, one session, independent or joint stops | 11 |
| [Iron Condors & Flies](docs/results/iron-condor.md) | Defined-risk short premium | 5 |
| [Strangles](docs/results/strangles.md) | Short OTM strangles, various holds | 6 |
| [Combined NIFTY + SENSEX](docs/results/combined-index.md) | Routes each weekday to whichever index suits it | 3 |
| [Human-Compatible](docs/results/combined-human.md) | 15-minute checks and GTT orders instead of constant monitoring | 3 |
| [Expiry-Day Short Premium](docs/results/expiry-day-short-premium.md) | Straddle vs strangles sold on expiry day, per-leg stop swept 50-100% | 8 |
| [Heads & Tails](docs/results/heads-tails.md) | Random-entry controls | 3 |
| [Directional & Signal Studies](docs/results/directional-studies.md) | Underlying-only signal tests | 9 |

### Headline six-year runs

Only 2020–2026 runs appear here, because a single-year return and a six-year
CAGR are not comparable numbers.

| Strategy | Net P/L | CAGR | Max DD |
|---|---:|---:|---:|
| [Heads & Tails random-entry control](docs/results/heads-tails.md) | Rs 9,73,379 | 17.38% | Rs 4,81,637 |
| [Adjusted straddle, held to expiry, 3-leg cap](docs/results/adjusted-straddle.md) | Rs 9,54,046 | 15.16% | Rs 41,725 |
| [25-SMA overnight, ITM 200 offset](docs/results/25ma-overnight.md) | Rs 18,24,282 | 14.93% | Rs 3,53,561 |
| [25-SMA intraday trailing, 09:30 entry](docs/results/25ma-intraday.md) | −Rs 14,15,087 | −100% | Rs 19,86,026 |

**The random-entry control is now first, and nothing beats it.** That is the
point of running it: any signal-based strategy below ~17% CAGR on this
instrument has not shown that its signal beats a coin flip on the same costs.

The two 25-SMA rows used to head this table at 31.72% and 19.32%. Both were
inflated by lookahead — a trailing stop that filled at a price recorded before
the stop triggered, an entry that read a 15-minute bar ten minutes before it
closed, and an overnight entry placed one minute before its own signal bar
closed. All three are fixed; see the [lookahead audit](docs/lookahead-audit.md)
for the before-and-after on every affected run. The control itself was audited
and needed no change.

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
- **A bar stamped `T` closes at `T + interval`, and nothing before then can read
  it.** Three violations of this in the 25-SMA families turned two losing
  strategies into the best-performing rows in this repo. If a stop is detected
  from a bar's high or low, the fill belongs on the *next* bar — that bar's own
  open predates the trigger. See the [lookahead audit](docs/lookahead-audit.md),
  and `python/tests/test_lookahead_guards.py` for the assertions that now hold
  the line.
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
