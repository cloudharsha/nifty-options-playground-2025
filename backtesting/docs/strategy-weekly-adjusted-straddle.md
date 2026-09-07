# Weekly Adjusted ATM Straddle — final spec

Chosen against five constraints: **never skip a week**, **testable across the
full 6 years**, **low drawdown**, **CAGR above 10%**, and **few adjustments**.

Full tables: [adjusted-straddle.md](results/adjusted-straddle.md). Runner:
[`../python/adjusted-straddle-half-add/`](../python/adjusted-straddle-half-add/).

## Rules

**Entry.** 09:20 on the first session after the previous expiry. Sell 1 lot of
that week's **ATM** straddle. No balance filter, no strike search — every week is
traded.

**Monitoring.** Check **once an hour** (09:20, 10:20, 11:20 …). Not continuously.

**Adjustment.** When the weaker side's total falls to **≤50%** of the stronger
side, sell one more option on the weak side worth **~25%** of the stronger side
(accept 20–30%), struck **OTM against current spot**.

**Cap.** Never exceed **3 legs per side**. At the cap, exit the cheapest leg on
the weak side and re-sell so that side totals ~75% of the strong side.

**Unwind.** When the single side falls back to at or below the stacked side's
total, buy back **one** leg — the cheapest. One per parity touch.

**Exit.** Close at 15:20 **one session before expiry**; stay flat through expiry
day.

**No stop loss.** Rs 30 per order per leg. Budget **Rs 6.5L** margin per lot.

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode expiry --allow-stale-entry --exit-lead-sessions 1 \
    --balance-max-diff 1.0 --strike-search-steps 0 --check-interval 60
```

## Results, 2020–2026

| | Value |
|---|---:|
| Net P/L | Rs 9,42,294 |
| CAGR on Rs 6.47L peak margin | **15.00%** |
| Max drawdown | Rs 67,919 |
| Adjustments | **5.9 per cycle** (3.2 adds, 1.9 unwinds, 0.7 rolls) |
| Weeks traded | 329 of 334 |

Every year profitable: 2020 +89,865 · 2021 +197,715 · 2022 +137,410 ·
2023 +59,625 · 2024 +44,656 · 2025 +377,225 · 2026 +35,799 (part).

The 5 untraded weeks are pure data gaps — no priceable ATM straddle in the
dataset — not the strategy declining.

## Check frequency is the biggest lever, and it was hiding in plain sight

Every other parameter was tuned before this one was touched. All rows below
trade every week over the full 6 years:

| Checks | Trigger | Adj/cycle | CAGR | Max DD |
|---|---|---:|---:|---:|
| Every minute + ±5 strike search | 0.50 | 14.8 | 16.53% | Rs 99,098 |
| Every 15 min | 0.50 | 9.2 | 15.60% | Rs 91,993 |
| Every 30 min | 0.50 | 7.5 | 14.67% | Rs 68,066 |
| **Every 60 min** | **0.50** | **5.9** | **15.00%** | **Rs 67,919** |
| Every 60 min | 0.40 | 4.1 | 13.52% | Rs 68,889 |
| Every 30 min | 0.40 | 4.7 | 13.15% | Rs 79,180 |
| Every 30 min | 0.35 | 3.8 | 12.48% | Rs 75,466 |

Going from minute-level to hourly checks cuts adjustments by **60%** and
drawdown by **32%**, for 1.5 CAGR points. Hourly also beats 30-minute on all
three axes at once — it is not a trade-off, 30-minute is simply dominated.

The reason: a minute-level checker reacts to noise. It opens a leg, pays
Rs 60, and unwinds it shortly after when the move reverses. An hourly check only
sees moves that persisted. Checking less is not a concession to convenience — it
is a better rule.

**If you want less work still:** trigger 0.40 at hourly checks gives 4.1
adjustments per cycle — 31% fewer — for 1.5 CAGR points, with drawdown unchanged
(Rs 68,889). Below that the stricter triggers start *raising* drawdown, because
adjusting less leaves the position less hedged when a move runs.

## Rejected, with the evidence

| Rejected | Cost | Why |
|---|---|---|
| Minute-level monitoring | +60% adjustments, +32% drawdown | Table above |
| Uncapped adds | −8 CAGR points, 2.75x capital | Stacked to 12 legs, Rs 17.8L peak margin |
| Adds only further OTM than existing legs | Silently disengages in crashes | COVID week needed a CE worth 66; best beyond the held leg was 27.5, so nothing was added |
| ±5 strike search | +Rs 31k drawdown, more adjustments | Recovers weeks earning half a normal week |
| Skipping unbalanced weeks | −Rs 2,08,348 over 6 years | Those 76 weeks averaged +Rs 2,741 and won 66% |
| Trigger below 0.40 | Raises drawdown | 0.35 gives Rs 75,466 vs 0.40's Rs 68,889 |
| Intraday instead of weekly | 15.00% → 2–3% | Costs consume 73–86% of gross |
| Monthly contracts | 15.00% → 3.45% | 4.4x fewer cycles for identical margin |

## Caveats

**Margin is modelled, not SPAN.** Rs 6.5L is the peak (3 legs one side, 1 the
other) under a 10%-of-contract-value model with 30% cross-side netting. Median
is ~Rs 3.0L but the peak must be funded. Verify a 3 CE + 1 PE position on a real
calculator — every return figure rests on it.

**Fills are assumed.** Costs are charged per order, but the backtest assumes it
traded at the recorded price. Hourly checking makes this more realistic than
minute-level did, since an hourly decision has time to be executed.

**`--mode roll` remains untested at scale.** A continuous roll that never holds
expiry day looked strong (39% CAGR, Rs 25,597 drawdown) but covers only 18
months and cannot be tested earlier: an exhaustive scan found next-week contract
data available a day early in 0 of 52 expiries in 2020, 0 of 52 in 2021, 0 of 52
in 2022, 1 of 53 in 2023, 0 of 52 in 2024, then 53 of 53 in 2025. Its window
contains no crisis and paid 1.85x per cycle versus 2020–24. The clean 6-year
test of the same idea — exiting a session early, which this spec does — shows no
drawdown benefit at all, so treat the roll's numbers as regime, not mechanism.
