# Weekly Adjusted ATM Straddle

**Status: finalized.** Selected from 30+ tested variants of the straddle-adjustment
idea against five constraints — never skip a week, testable across the full six
years, low drawdown, CAGR above 10%, and few adjustments.

This folder is self-contained: the rules below, and in [`results/`](results/) the
exact output files the numbers come from. Re-running the strategy overwrites
`backtesting/results/`, but never this folder.

---

## The rules

**1. Entry.** At 09:20 on the first session after the previous weekly expiry,
sell 1 lot of that week's **ATM** straddle — CE and PE at the strike nearest to
spot, rounded to 50.

No entry filter. No strike shopping. **Every week is traded.**

**2. Monitoring.** Check the position **once an hour**: 09:20, 10:20, 11:20,
12:20, 13:20, 14:20, 15:20. Not continuously — see
[Why hourly](#why-hourly-checking-beats-watching-continuously).

At each check, compare the **total premium of all CE legs** against the **total
premium of all PE legs**. One side is "strong" (worth more), the other "weak".

**3. Unwind first.** If one side holds more legs than the other, and the
single-leg side has fallen to at or below the total of the stacked side, buy back
**one** leg from the stacked side — the cheapest. Only one per check.

**4. Otherwise, adjust.** If the weak side's total has fallen to **50% or less**
of the strong side's total, sell one more option on the **weak** side, priced at
about **25%** of the strong side's total. Accept anything between 20% and 30%.

The new strike must be **out of the money against current spot** — not merely
further out than the legs already held. That distinction matters; see
[What was rejected](#what-was-rejected).

*Example.* Sold 24000 CE and PE at 100 each. Market falls: PE now 150, CE now 75.
CE is half of PE, so sell another CE priced near 37.50 (25% of 150), at whatever
strike is OTM against spot right now.

**5. Leg cap.** Never hold more than **3 legs on one side**. If the trigger fires
when the weak side already has 3 legs, do not add a fourth. Instead **roll**: buy
back the cheapest leg on that side, and sell a replacement so the side's total
comes to about **75%** of the strong side (accept 65–85%).

**6. Exit.** Close everything at 15:20 **one session before expiry**. Stay flat
through expiry day. Re-enter the following week per rule 1.

**7. No stop loss.** The leg cap and the unwind rule are the risk control.

---

## Running it

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode expiry \
    --allow-stale-entry \
    --exit-lead-sessions 1 \
    --balance-max-diff 1.0 \
    --strike-search-steps 0 \
    --check-interval 60
```

| Flag | Why |
|---|---|
| `--exit-lead-sessions 1` | Exit a session before expiry |
| `--balance-max-diff 1.0` | Disables the entry filter, so no week is skipped |
| `--strike-search-steps 0` | Plain ATM, no strike shopping |
| `--check-interval 60` | Hourly checks |

---

## Results — 2020-01-01 to 2026-06-16

| | |
|---|---:|
| Weeks traded | **329 of 334** |
| Gross P/L | Rs 10,59,594 |
| Costs (Rs 30/order, 3,910 orders) | Rs 1,17,300 |
| **Net P/L** | **Rs 9,42,294** |
| **CAGR on Rs 6.47L peak margin** | **15.00%** |
| **Max drawdown** | **Rs 67,919** |
| Win rate | 64.4% (212W / 117L) |
| Profit factor | 1.92 |
| Best week | Rs 51,045 |
| Worst week | −Rs 57,019 |
| **Adjustments** | **5.9 per week** (3.2 adds, 1.9 unwinds, 0.7 rolls) |

The 5 untraded weeks are dataset gaps — no priceable ATM straddle in the files —
not the strategy declining a trade.

### Every year profitable

| Year | Weeks | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 52 | Rs 89,865 | 61.5% |
| 2021 | 52 | Rs 1,97,715 | 75.0% |
| 2022 | 52 | Rs 1,37,410 | 63.5% |
| 2023 | 51 | Rs 59,625 | 56.9% |
| 2024 | 51 | Rs 44,656 | 56.9% |
| 2025 | 53 | Rs 3,77,225 | 75.5% |
| 2026 (part) | 18 | Rs 35,799 | 55.6% |

2023 and 2024 are the realistic years: low volatility, thin premiums, roughly
Rs 50k on Rs 6.5L. 2025 was exceptional and should not be planned around.

### The worst weeks

| Week | Loss |
|---|---:|
| 2026-01-28 | −Rs 57,019 |
| 2020-03-06 (COVID) | −Rs 45,101 |
| 2025-04-11 (tariff selloff) | −Rs 33,086 |
| 2021-01-29 | −Rs 28,661 |
| 2020-09-18 | −Rs 28,463 |

Losses cluster in fast directional moves, which is what a short straddle is
structurally exposed to. The adjustment reduces that exposure; it does not
remove it.

---

## Capital

**Budget Rs 6.5 lakh of margin per lot.**

That is the *peak* requirement — the position at its heaviest, 3 legs on one side
and 1 on the other. The median across the 329 weeks is about Rs 3.0L, but the
peak is what must be funded, or the position is liquidated in exactly the week
that matters.

**This figure is modelled, not SPAN.** It assumes 10% of contract value per naked
short lot, same-side legs additive, cross-side netting at 30%. **Verify a
3 CE + 1 PE NIFTY position on a real margin calculator before sizing.** Every
return number here rests on it: if the true peak is Rs 10L, the CAGR falls to
about 10%.

Lot size varies by era (75 → 50 → 25 → 75 → 65), keyed to the contract's expiry
date. See [dataset-reference.md](../../docs/dataset-reference.md).

---

## Why hourly checking beats watching continuously

This was the last parameter tuned, and it mattered more than anything tuned
before it. All rows trade every week across the full 6 years:

| Checks | Trigger | Adj/week | CAGR | Max DD |
|---|---|---:|---:|---:|
| Every minute (+ strike search) | 0.50 | 14.8 | 16.53% | Rs 99,098 |
| Every 15 min | 0.50 | 9.2 | 15.60% | Rs 91,993 |
| Every 30 min | 0.50 | 7.5 | 14.67% | Rs 68,066 |
| **Every 60 min** | **0.50** | **5.9** | **15.00%** | **Rs 67,919** |
| Every 60 min | 0.40 | 4.1 | 13.52% | Rs 68,889 |
| Every 30 min | 0.40 | 4.7 | 13.15% | Rs 79,180 |
| Every 30 min | 0.35 | 3.8 | 12.48% | Rs 75,466 |

Minute-level to hourly cuts adjustments **60%** and drawdown **32%** for 1.5 CAGR
points. Hourly also beats 30-minute on adjustments, profit *and* drawdown at the
same time — 30-minute is dominated, not a trade-off.

The reason: a minute-level checker reacts to noise. It opens a leg, pays Rs 60,
and unwinds it shortly after when the move reverses. An hourly check only sees
moves that persisted. Checking less often is a better rule, not a concession to
convenience.

### If you want less work

**Hourly checks with a 0.40 trigger** — adjust only when the weak side falls to
40% of the strong side. **4.1 adjustments per week, 31% less work, for 1.5 CAGR
points, with drawdown unchanged.**

Add `--half-trigger-ratio 0.40`. Results in
[`results/weekly_adjusted_straddle_LIGHT_summary.md`](results/weekly_adjusted_straddle_LIGHT_summary.md):
Rs 8,16,250 net, 13.52% CAGR, Rs 68,889 max drawdown.

**Do not go below 0.40.** At 0.35 drawdown starts rising again (Rs 75,466) —
adjusting less leaves the position under-hedged when a move runs.

---

## What was rejected

Each was tested, not assumed.

| Rejected | Cost | Evidence |
|---|---|---|
| Minute-level monitoring | +60% adjustments, +32% drawdown | Table above |
| Uncapped adds (no 3-leg cap) | −8 CAGR points, 2.75x the capital | Stacked to 12 legs, Rs 17.8L peak margin |
| Adds only further OTM than existing legs | **Silently stops adjusting in crashes** | COVID week needed a CE worth 66; the best available beyond the held leg was 27.5, so nothing was added and the week rode naked |
| ±5 strike search at entry | +Rs 31k drawdown, more adjustments | Recovers weeks earning half what a normal week earns |
| Skipping weeks where CE/PE differ >20% | −Rs 2,08,348 over 6 years | Those 76 weeks averaged +Rs 2,741 and won 66% of the time |
| Trigger below 0.40 | Raises drawdown | 0.35 gives Rs 75,466 vs 0.40's Rs 68,889 |
| Holding to expiry day instead of exiting early | Nothing either way | Under half a CAGR point, identical drawdown, identical on every stress week |
| Intraday version | 15.00% → 2–3% | Costs consume 73–86% of gross over 893 cycles |
| Monthly contracts | 15.00% → 3.45% | 4.4x fewer cycles for identical margin |
| A stop loss | untested | Deliberately excluded — the cap and unwind are the risk control |

---

## What would invalidate this

**Margin.** If a real broker requires materially more than Rs 6.5L at peak, the
CAGR drops proportionally and the strategy may not clear 10%.

**Fills.** Costs are charged per order, but the backtest assumes it traded at the
recorded price. Hourly checking makes this more realistic than minute-level did —
an hourly decision has time to be executed — but a fast market still fills worse
than modelled, and adjustments happen precisely when markets are fast.

**Regime.** 2025 contributed Rs 3.77L of the Rs 9.42L total. Strip it out and the
remaining years average roughly Rs 94k/year on Rs 6.5L — about 14% — with 2023
and 2024 nearer Rs 50k. Plan for the quiet years, not the good one.

**Untested tail.** The worst week in the sample is −Rs 57,019. COVID is in the
sample, but a worse event is always possible with a naked short straddle and no
stop.

---

## A variant worth revisiting

`--mode roll` — enter next week's contract at 15:20 a session before expiry so
the book is never flat and never holds expiry day — returned 39% CAGR with a
Rs 25,597 drawdown. **It covers only 18 months and cannot be tested further back:**
an exhaustive scan found next-week contract data available a day early in 0 of 52
expiries in 2020, 0 of 52 in 2021, 0 of 52 in 2022, 1 of 53 in 2023, 0 of 52 in
2024, then 53 of 53 in 2025. Its window contains no crisis and paid 1.85x per
cycle versus 2020–24.

The clean six-year test of the same idea — exiting a session early, which this
spec already does — shows **no drawdown benefit at all**. So treat the roll's
numbers as regime rather than mechanism.

To settle it: re-pull 2020–2024 weekly contracts with full listed history, then
run `--mode roll` unchanged.
