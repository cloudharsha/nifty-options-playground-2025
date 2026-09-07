# nifty-options-playground-2025

Backtests of NIFTY and SENSEX index-option strategies against 1-minute contract
data, 2020–2026.

This is a research playground, not a trading system. Strategies here are tested
until they either hold up or fall apart, and **both outcomes are kept**. Several
of the most carefully built strategies in this repo lose money; those results
are indexed alongside the profitable ones, because a losing backtest you can
read is worth more than a profitable one you can't reproduce.

Everything is plain Python 3.13 with the standard library. No pandas, no numpy,
nothing to install.

**→ [Start with the backtesting index](backtesting/README.md)** — every strategy,
what it does, and what it returned.

## What's in the repo

Only the `backtesting/` workspace is versioned:

```
backtesting/
  README.md                 index: families, headline runs, how to run
  docs/
    dataset-reference.md    data schema, lot-size eras, expiry-day history
    results/                one index doc per strategy family
  python/
    _template/example.py    copy this to start a new strategy
    <family>/               runner scripts
    legacy/                 archived; does not run as-is
    tests/
  results/
    <family>/               generated output, mirrors python/<family>/
```

`python/<family>/` and `results/<family>/` mirror each other. That is the only
structural rule you need to hold in your head.

## Data layout

**The market data is not in this repo** — it is roughly 11 GB and stays local.
The scripts expect it at the repo root:

```
NiftyOptions_2020_2026/Options/<YYYY-MM-DD>/NIFTY_<strike>_<CE|PE>_<DD>_<MON>_<YY>.csv
SensexOptions_2024_2026/Options/<YYYY-MM-DD>/SENSEX_<strike>_<CE|PE>_<DD>_<MON>_<YY>.csv
nifty/NIFTY50_INDEX_5m_last_7y.csv        spot series used for signals and ATM selection
nifty/NIFTY50_INDEX_1m_2025.csv
nifty/SENSEX_INDEX_5m_last_7y.csv
```

Each options folder is one expiry date; each CSV is one contract, in 1-minute
OHLCV+OI bars with IST timestamps:

```csv
timestamp,open,high,low,close,volume,oi
2025-01-02T09:15:00+05:30,150.3,152.0,149.5,151.2,3750.0,284875.0
```

Every script takes `--options-dir` and `--spot-file`, so you can point them
anywhere. Full schema and the contract conventions that change P/L are in
[backtesting/docs/dataset-reference.md](backtesting/docs/dataset-reference.md).

## Running a backtest

```bash
python backtesting/python/<family>/<script>.py --help
```

For example, a short window of the adjusted straddle:

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode expiry --start-date 2025-01-01 --end-date 2025-03-31
```

Output lands in `backtesting/results/<family>/`. Each run writes a
`_summary.md` report plus CSVs of the underlying trades.

Tests run one file at a time (no `__init__.py`, so `unittest discover` won't
find them):

```bash
python backtesting/python/tests/test_run_weekly_short_strangle_0920_2025.py
```

## Reading the results honestly

A few things are easy to get wrong when comparing runs, and they are worth
knowing before you trust any number here:

- **Capital base is not uniform, deliberately.** Most rows use a fixed reference
  base; the adjusted-straddle rows use the peak margin the position actually
  reaches, because they stack multiple short legs. The same strategy shows
  25.65% on a Rs 3L base and 7.21% on the Rs 17.77L it really needs. A CAGR
  means nothing without the capital it was measured against.
- **CAGR and single-year return are different columns.** Don't rank them together.
- **Lot size changed five times** between 2020 and 2026 (75 → 50 → 25 → 75 → 65),
  keyed to the contract's *expiry* date, not the trade date. Get it wrong and
  every number in a run is silently rescaled.
- **Weekly expiry moved from Thursday to Tuesday** in September 2025.
- **Fills are assumed.** Costs are modelled per order, but every backtest assumes
  it traded at the recorded price. That is optimistic for illiquid strikes and
  for gap days.
- **Skipped days matter.** Several strategies decline to trade when an entry
  filter fails. Each summary reports how many days were skipped and why — a high
  skip rate can mean a filter is doing real work, or that the sample is thin.

## Contributing

**Pull requests with tested strategies are welcome**, including ones that lost
money. A negative result that is clearly reported saves the next person from
re-running it.

1. Fork and branch.
2. Copy [`backtesting/python/_template/example.py`](backtesting/python/_template/example.py)
   into the matching `python/<family>/` folder, or a new family folder if none
   fits. It carries the repo's conventions: argparse defaults, CSV and summary
   writers, logging, and the `parents[3]` repo-root resolution that assumes your
   script sits exactly one level below `python/`.
3. Point `--results-dir` at your own `results/<family>/` folder so a re-run
   never overwrites someone else's output.
4. Run it, and commit the generated `_summary.md` and trade CSVs.
5. Add a row to the matching doc in [`backtesting/docs/results/`](backtesting/docs/results/).
   New family? Add a doc there, a `README.md` in both new folders, and a row in
   [`backtesting/README.md`](backtesting/README.md).
6. Open the PR.

What a good strategy PR states plainly:

- the exact date range tested, and how many days or cycles actually traded
- **the cost model** — brokerage and taxes per order, and any slippage assumed
- **the capital base** and why that figure (margin required, or a stated reference)
- how many days were skipped and for what reason
- max drawdown in rupees, not just the return
- anything the backtest assumes that live trading wouldn't give you

Please don't commit market data, `.log` files, or `__pycache__` — the
`.gitignore` blocks these, and they are all regenerable.

If a result looks too good, say so in the PR. The
[Heads & Tails](backtesting/docs/results/heads-tails.md) random-entry controls
are there as a sanity check: a strategy that can't beat a coin flip on the same
instrument and the same costs hasn't shown that its signal does anything.

## Disclaimer

Research and education only. Nothing here is investment advice. Backtested
results are not predictions — they assume fills that live markets may not offer,
and past behaviour of an index or its options implies nothing about the future.
Trading options carries real risk of losing more than you put in.
