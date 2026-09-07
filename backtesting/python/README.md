# Strategy scripts

Each folder is one strategy family and mirrors the matching folder under
[`../results/`](../results/). A script's generated output defaults into its own
family folder, so re-running one strategy never disturbs another.

Every script is standalone: Python 3.13, standard library only, no shared
imports between them. That is deliberate — a run script is meant to be readable
top to bottom without chasing helpers, and old runs stay reproducible even when
newer strategies change how they do things. The cost is duplicated helpers
across files, which is a trade this repo accepts.

| Folder | Scripts | Strategy | Results index |
|---|---:|---|---|
| [`25ma-intraday/`](25ma-intraday/) | 6 | Short ATM on a 25-SMA signal, closed same session | [index](../docs/results/25ma-intraday.md) |
| [`25ma-overnight/`](25ma-overnight/) | 2 | Same signal held overnight to weekly expiry | [index](../docs/results/25ma-overnight.md) |
| [`adjusted-straddle-half-add/`](adjusted-straddle-half-add/) | 1 | ATM straddle that adds to the weak side, then unwinds | [index](../docs/results/adjusted-straddle.md) |
| [`intraday-straddle/`](intraday-straddle/) | 5 | Plain ATM straddle, one session, NIFTY and SENSEX | [index](../docs/results/intraday-straddle.md) |
| [`combined-index/`](combined-index/) | 3 | NIFTY and SENSEX routed by weekday | [index](../docs/results/combined-index.md) |
| [`combined-human/`](combined-human/) | 1 | 15-minute checks and GTT orders | [index](../docs/results/combined-human.md) |
| [`heads-tails/`](heads-tails/) | 3 | Random-entry controls | [index](../docs/results/heads-tails.md) |
| [`iron-condor/`](iron-condor/) | 1 | Defined-risk short premium | [index](../docs/results/iron-condor.md) |
| [`_template/`](_template/) | 1 | Starting point for a new strategy | — |
| [`legacy/`](legacy/) | 34 | Archived. **Does not run as-is** — see its README | [index](../docs/results/strangles.md) |
| [`tests/`](tests/) | 5 | Unit tests for legacy helper functions | — |

## Starting a new strategy

Copy [`_template/example.py`](_template/example.py) into the right family folder
(or a new one) and adapt it. It carries the conventions the rest of the repo
follows: argparse defaults, CSV and summary writers, logging setup, and the
`parents[3]` repo-root resolution that assumes your script sits exactly one
level below `python/`.

If you nest deeper than `python/<family>/<script>.py`, you **must** bump that
`parents[3]`. Getting it wrong raises no error — the script silently writes to
`backtesting/backtesting/results/`. That is precisely how every script in
`legacy/` came to be broken.

## Running

```bash
# from the repo root, not from this folder
python backtesting/python/<family>/<script>.py --help
```

Tests run one file at a time; there is no `__init__.py`, so `unittest discover`
will not find them:

```bash
python backtesting/python/tests/test_run_weekly_short_strangle_0920_2025.py
```
