# Adjusted Straddle — Sleeve A (external spec replication)

A line-by-line replication of an externally supplied spec ("Sleeve A"), run
against this repo's 1-minute NIFTY option data for 2020–2026. The question the
spec author asked was specifically about **the margin rate in the sizing
formula**, which they reported as moving the answer from ~13% to ~25% CAGR.

- Scripts: [`backtesting/python/adjusted-straddle-sleeve-a/`](../../python/adjusted-straddle-sleeve-a/)
- Results: [`backtesting/results/adjusted-straddle-sleeve-a/`](../../results/adjusted-straddle-sleeve-a/)
- Related: the [adjusted straddle](adjusted-straddle.md) family, which shares the
  add/unwind idea but differs in add size, leg cap, costs, sizing and entry gate.

Back to the [backtesting index](../../README.md).

## The spec

One cycle per weekly expiry, no overlap. Entry 09:20 on the first session after
the previous expiry; exit 15:20 on expiry day.

- **Entry** — skip if the previous day's India VIX close < 12. ATM =
  `round(spot/50)*50`. Require `min(CE,PE)/max(CE,PE) >= 0.80`; if ATM fails,
  walk `ATM, −50, +50, … ±250` and take the first strike that passes, else skip.
  Both legs must price off an exact 09:20 bar. Sell 1 CE + 1 PE.
- **Every minute**, up to 12 actions per minute, in order: **unwind** the
  cheapest stacked leg when `single <= stacked × 1.00`; then **add** when
  `weak <= 0.50 × strong` — a new leg at `0.20 × strong` (band 0.15–0.25), OTM
  vs current spot, not already held, exact bar this minute, closest to target
  with the original ATM as tie-break. At 4 legs on the weak side, **roll**
  instead: buy back the cheapest weak leg, re-sell so the weak side totals
  `0.75 × strong` (band 0.65–0.85).
- **No stop loss, no take profit.**
- **Costs** — Rs 20/order, STT sell-side by era, exchange 0.03503%, SEBI
  0.0001%, stamp 0.003% buy, GST 18% on (brokerage + exchange + SEBI), and 0.25
  points slippage per side on every fill.
- **Sizing** — `lots = floor(10,00,000 / (spot × lot_size × margin_rate))`,
  fixed at entry, non-compounding. Run once at `margin_rate = 0.50` and once at
  `0.19`.

## Replication vs the reported numbers

Sleeve A, margin 0.50, slippage 0.25 — the run the spec author reported:

| Metric | Reported | Replicated | Δ |
|---|---:|---:|---:|
| Cycles | 270 | **266** | −4 |
| CAGR | 15.78% | **16.95%** | +1.17 pp |
| Sharpe | 2.78 | **2.58** | −0.20 |
| Max drawdown | 7.72% | **7.42%** | −0.30 pp |
| Profit factor | 2.94 | **3.17** | +0.23 |
| Win rate | 72.2% | **74.06%** | +1.9 pp |

Six of six headline metrics land within about one point of the reported values,
on an independent implementation from the written spec alone. **The strategy
replicates.**

The one number that does **not** reconcile is the three-way split. Reported
`29.34% / 9.37% / 16.65%`; this run's equal-thirds-by-cycle-count split is
`40.07% / 20.21% / 14.73%`. The spec did not define how the thirds are cut, and
the reported middle segment being the weakest does not match any calendar or
count-based thirds of this sample, which declines monotonically. Treat the split
row as unreconciled rather than as agreement or disagreement.

## The margin rate is leverage, not a modelling choice

This is the question the spec asked to have checked, and the answer is that the
margin rate does move the number, by even more than reported — but it is not
buying anything.

| | margin 0.50 | margin 0.19 |
|---|---:|---:|
| Cycles / adds / unwinds / rolls | \* identical \* | \* identical \* |
| Mean lots per cycle | 1.70 | 4.96 |
| Net P/L | Rs 17,36,875 | Rs 54,46,185 |
| **CAGR** | **16.95%** | **33.61%** |
| Sharpe | 2.58 | 2.72 |
| Max drawdown | Rs 77,100 (**7.42%**) | Rs 2,17,933 (**19.83%**) |
| Worst single cycle | −Rs 67,483 (−6.7%) | −Rs 2,01,505 (−20.2%) |
| Profit factor | 3.17 | 3.40 |

Three things follow.

**The trade path is byte-identical.** Both runs open, add, unwind and roll on the
same minutes at the same strikes — the margin rate only sets the lot count. Every
extra point of CAGR is leverage.

**CAGR roughly doubles, drawdown nearly triples.** Return over max drawdown falls
from 2.28 to 1.69. Sharpe rises slightly (2.58 → 2.72) only because the flat
Rs 20/order brokerage — 70% of all costs at margin 0.50, 53% at 0.19 — amortises
over more lots. That is a cost-efficiency effect, not a risk improvement, and it
is why net P/L scales 3.14x while lots scale only 2.92x.

**0.19 is almost certainly under-margined for this position.** The formula charges
margin as `margin_rate × spot × lot_size`, i.e. against a *single* lot of notional.
But this strategy stacks: **the position reaches 5 simultaneous short legs in 260
of 266 cycles** (4 on the weak side plus the surviving strong-side leg). NSE
SPAN + exposure on a short index option runs roughly 10–12% of contract value,
and the risk array for 4 short puts against 1 short call is dominated by the
one-sided down move, so the blocked margin is on the order of 4 naked legs —
around 40–50% of one lot's notional. That is what `0.50` approximates. `0.19`
assumes the entire 5-leg stack blocks less than two naked legs' worth, which is
below what a broker would hold against even the initial straddle.

So the honest reading of the two runs is not "13% or 25%, pick your assumption."
It is that **16.95% is the number this strategy earns on a margin assumption the
position can actually support**, and the 0.19 figure is that same result levered
about 2.9x against margin that would not be granted. Confirming the exact
requirement needs the SPAN risk arrays for the stacked position, which this repo
does not carry — but the direction is not in doubt.

## What the entry gates actually do

68 of 334 weekly cycles are skipped:

| Reason | Count |
|---|---:|
| `vix_below_floor` (previous day's India VIX < 12) | 56 |
| `balance_check_failed` (no strike within ±250 at 80% balance) | 8 |
| `no_spot_at_entry` | 2 |
| `no_prev_vix` (first cycle of the sample) | 1 |
| `missing_entry_bar` | 1 |

The VIX gate is doing nearly all of the skipping, and it is heavily concentrated
in the two low-volatility years:

| Year | Expiries | VIX skips | Other skips | Traded |
|---|---:|---:|---:|---:|
| 2020 | 53 | 1 | 4 | 48 |
| 2021 | 53 | 1 | 3 | 49 |
| 2022 | 52 | 0 | 1 | 51 |
| 2023 | 52 | **28** | 1 | 23 |
| 2024 | 52 | 3 | 1 | 48 |
| 2025 | 53 | **20** | 0 | 33 |
| 2026 | 19 | 3 | 2 | 14 |

It sits out more than half of 2023 and over a third of 2025, while touching
2020–2022 essentially not at all. It is a "don't sell cheap premium" rule, and
the years it thins out are the years with the weakest per-cycle edge — 2023
returns Rs 108k across 23 cycles against 2020's Rs 635k across 48.

## Runs

Capital base is the Rs 10L the spec sizes against, for both rows — unlike most
[adjusted straddle](adjusted-straddle.md) rows, which are quoted against the peak
margin the position reaches. Read the
[index notes](../../README.md#reading-the-numbers) before comparing across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Current | 2020–2026 | Sleeve A — weekly adjusted straddle, VIX>=12 gate, 4-leg cap + 75% roll, full cost stack, **margin 0.50** | Profit | Rs 10L | Rs 17,36,875 | 16.95% | Rs 77,100 (7.42%) | [Summary](../../results/adjusted-straddle-sleeve-a/adjusted_straddle_sleeve_a_2020_2026_m050_summary.md) | **Replicates the reported run.** 266 cycles, Sharpe 2.58, PF 3.17, win 74.06%; 2,665 adds / 2,191 unwinds / 521 rolls; mean 1.70 lots |
| Current | 2020–2026 | Sleeve A — identical rules, **margin 0.19** | Profit | Rs 10L | Rs 54,46,185 | 33.61% | Rs 2,17,933 (19.83%) | [Summary](../../results/adjusted-straddle-sleeve-a/adjusted_straddle_sleeve_a_2020_2026_m019_summary.md) | Same trades, 2.92x the lots. Worst single cycle −Rs 2,01,505 = 20% of capital. Margin assumption is not supportable for a 5-leg stack — see above |

## Data notes and departures from the spec

Two spec inputs did not exist in the repo and had to be handled:

- **India VIX** — not present. Sourced as daily OHLC from the Yahoo Finance chart
  API for `^INDIAVIX`, 2020-01-02 to 2026-09-08, and committed to
  [`backtesting/data/india_vix_daily.csv`](../../data/) so the run stays
  reproducible. Spot-checked against the known extremes (83.61 on 2020-03-24,
  9.15 on 2025-12-26). The gate reads the last session **strictly before** the
  entry date, so no same-day close leaks into a 09:20 decision.
- **1-minute spot** — the repo has 1-minute spot only for 2025, so the 5-minute
  index series is used for the entry ATM and for the OTM test on adds. The
  09:20 bar exists on the 5-minute grid, so entry is unaffected; the only cost
  is that an add's OTM test resolves spot to within 5 minutes rather than 1.

Everything else follows the spec as written. Option prices are the 1-minute bar
**close** as specified; a strike must have an exact bar at the check minute to be
sold, so nothing is ever sold on a stale quote, while an already-open leg is
marked at the last close at or before the check minute. The STT eras are the
statutory ones — 0.05% to 2023-03-31, 0.0625% from 2023-04-01, 0.10% from
2024-10-01, 0.15% from 2026-04-01 — which is exactly the four-step ladder the
spec named.

Sharpe is per-cycle net return over the fixed Rs 10L base, annualised by
`sqrt(cycles/year)` with a zero risk-free rate. The spec did not define it; a
different convention will move the 2.58 without any trade changing.

## Reproducing

```bash
python backtesting/python/adjusted-straddle-sleeve-a/run_adjusted_straddle_sleeve_a_2020_2026.py --margin-rate 0.50
python backtesting/python/adjusted-straddle-sleeve-a/run_adjusted_straddle_sleeve_a_2020_2026.py --margin-rate 0.19
```

Roughly 25 minutes per run; the two are independent and can run in parallel.
`--vix-floor 0` disables the VIX gate, `--start-date` / `--end-date` cut the
window, and `--help` lists every rule constant as a flag.
