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
[Check frequency](#check-frequency-same-result-less-work).

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
| Gross P/L | Rs 9,10,540 |
| Costs (Rs 30/order, 3,910 orders) | Rs 1,17,300 |
| **Net P/L** | **Rs 7,93,240** |
| **CAGR on Rs 6.47L peak margin** | **13.19%** |
| **Max drawdown** | **Rs 42,159** |
| Win rate | 67.5% (222W / 107L) |
| Profit factor | 2.63 |
| Best week | Rs 48,165 |
| Worst week | −Rs 27,619 |
| **Adjustments** | **5.9 per week** (3.2 adds, 1.9 unwinds, 0.7 rolls) |

The 5 untraded weeks are dataset gaps — no priceable ATM straddle in the files —
not the strategy declining a trade.

### Every year profitable

| Year | Weeks | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 52 | Rs 1,62,221 | 73.1% |
| 2021 | 52 | Rs 1,38,033 | 67.3% |
| 2022 | 52 | Rs 1,21,115 | 71.2% |
| 2023 | 51 | Rs 8,760 | 62.7% |
| 2024 | 51 | Rs 40,731 | 66.7% |
| 2025 | 53 | Rs 2,57,225 | 71.7% |
| 2026 (part) | 18 | Rs 65,156 | 44.4% |

**2023 made almost nothing** — Rs 8,760 across 51 weeks. A full year of trading
and adjusting for a rounding error. Low volatility means thin premiums, and the
strategy has no answer to that. 2024 was only marginally better. Plan for the
possibility of a flat year, not for 2025.

### The worst weeks

| Week | Loss |
|---|---:|
| 2024-11-22 | −Rs 27,619 |
| 2021-01-29 | −Rs 25,331 |
| 2020-05-08 | −Rs 19,658 |
| 2023-12-01 | −Rs 18,165 |
| 2025-04-04 (tariff selloff) | −Rs 13,684 |

Losses cluster in fast directional moves, which is what a short straddle is
structurally exposed to. The adjustment reduces that exposure; it does not
remove it.

Notably COVID does **not** appear here. Holding through expiry day, the same
strategy lost Rs 45,101 in the week of 2020-03-06 and Rs 1,04,823 in the week of
2026-01-28. Exiting Monday removes those.

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

## Exiting before expiry day is the single most valuable rule

This is where the risk lives. Same strategy, same entries, six years, only the
exit differs:

| | Exit Mon 15:20 | Hold through Tue (expiry day) |
|---|---:|---:|
| Net P/L | Rs 7,93,240 | Rs 9,35,327 |
| CAGR | 13.19% | 14.85% |
| **Max drawdown** | **Rs 42,159** | **Rs 1,12,597** |
| **Worst week** | **-Rs 27,619** | **-Rs 1,04,823** |
| Return per Rs 1L of drawdown | **31.3** | 13.2 |

**Exiting a session early cuts drawdown 62% and the worst week 74%, for 1.7 CAGR
points.** Risk-adjusted it is 2.4x better.

The clearest evidence is which weeks vanish. Holding through expiry day, the two
worst weeks in six years are -Rs 1,04,823 (2026-01-28) and -Rs 45,101 (COVID,
2020-03-06). Exiting Monday, neither appears at all. Expiry-day gamma was
producing the entire tail.

The control run is in
[`results/weekly_adjusted_straddle_CONTROL_hold_through_expiry_summary.md`](results/weekly_adjusted_straddle_CONTROL_hold_through_expiry_summary.md).

## Check frequency: same result, less work

Contrary to what an earlier version of this document claimed, checking more often
does **not** meaningfully change returns or risk. All rows exit Monday and trade
every week across the full 6 years:

| Checks | Trigger | Adj/week | CAGR | Max DD | Worst week |
|---|---|---:|---:|---:|---:|
| Every 15 min | 0.50 | 9.2 | 13.29% | Rs 44,061 | -Rs 36,570 |
| Every 30 min | 0.50 | 7.5 | 13.12% | Rs 45,094 | -Rs 29,809 |
| **Every 60 min** | **0.50** | **5.9** | **13.18%** | **Rs 42,159** | **-Rs 27,619** |
| Every 60 min | 0.40 | 4.1 | 12.54% | Rs 47,902 | -Rs 31,309 |

Between 15, 30 and 60 minutes the CAGR spread is 0.17 points and drawdown varies
by Rs 3,000 - noise. **Hourly wins because it delivers that same result with 36%
fewer adjustments**, not because watching less is inherently better.

Practically: you are not giving anything up by checking once an hour instead of
every fifteen minutes. Do the version that you will actually execute.

### If you want less work still

Hourly with a **0.40 trigger** cuts to 4.1 adjustments per week, but now costs on
both other axes: Rs 7,41,620 net (12.54%) and a *higher* Rs 47,902 drawdown.
Adjusting less leaves the position under-hedged when a move runs. Add
`--half-trigger-ratio 0.40` if the workload matters more than the numbers; the
default 0.50 is the better trade.

## What was rejected

Each was tested, not assumed.

| Rejected | Cost | Evidence |
|---|---|---|
| Checking more often than hourly | 36-56% more adjustments for no gain | CAGR spread of 0.17 points across 15/30/60 min |
| Uncapped adds (no 3-leg cap) | −8 CAGR points, 2.75x the capital | Stacked to 12 legs, Rs 17.8L peak margin |
| Adds only further OTM than existing legs | **Silently stops adjusting in crashes** | COVID week needed a CE worth 66; the best available beyond the held leg was 27.5, so nothing was added and the week rode naked |
| ±5 strike search at entry | +Rs 31k drawdown, more adjustments | Recovers weeks earning half what a normal week earns |
| Skipping weeks where CE/PE differ >20% | −Rs 2,08,348 over 6 years | Those 76 weeks averaged +Rs 2,741 and won 66% of the time |
| Trigger below 0.40 | Raises drawdown | 0.35 gives Rs 75,466 vs 0.40's Rs 68,889 |
| Holding through expiry day | **2.7x the drawdown**, 3.8x the worst week | Rs 1,12,597 vs Rs 42,159 max DD; -Rs 1,04,823 vs -Rs 27,619 worst week |
| Intraday version | 15.00% → 2–3% | Costs consume 73–86% of gross over 893 cycles |
| Daily overnight roll (enter 15:20, exit 15:20 next day, re-enter) | 13.19% → 8.88% | **Worse even at zero cost.** See [below](#the-daily-overnight-roll) |
| Monthly contracts | 15.00% → 3.45% | 4.4x fewer cycles for identical margin |
| A stop loss | untested | Deliberately excluded — the cap and unwind are the risk control |

---

## The daily overnight roll

Tested at the request of a reader of this spec: keep every adjustment rule, but
instead of holding the contract for the week, **sell the ATM straddle at 15:20,
adjust across the next session, close everything at 15:20 the next day and open
a fresh ATM straddle.** The position carries into expiry day and closes on it; no
cycle starts on an expiry day, because next week's contract is not in the data on
expiry day before 2025 (0 of 262 expiries across 2020-2024). Checks are the open
plus hourly, so an overnight gap is seen at 09:15 rather than 09:20.

Six years, 1,264 cycles, identical rules and costs:

| | Weekly, exit 1 session early | Weekly, holds expiry day | **Daily overnight roll** |
|---|---:|---:|---:|
| Cycles | 329 | 329 | **1,264** |
| Gross P/L | Rs 9,10,540 | Rs 10,56,947 | **Rs 7,38,658** |
| Costs | Rs 1,17,300 | Rs 1,21,620 | **Rs 2,63,820** |
| Costs as % of gross | 12.9% | 11.5% | **35.7%** |
| Net P/L | Rs 7,93,240 | Rs 9,35,327 | **Rs 4,74,838** |
| Peak margin | Rs 6,46,950 | ~Rs 6.5L | Rs 6,48,075 |
| **CAGR on peak margin** | **13.19%** | **14.85%** | **8.88%** |
| Max drawdown | Rs 42,159 | Rs 1,12,597 | Rs 1,03,474 |
| Profit factor | 2.63 | 1.94 | **1.30** |
| Worst cycle | −Rs 27,619 | −Rs 1,04,823 | −Rs 70,340 |

**Rejected, and not because of costs.** That is the part worth keeping. Set the
daily roll's brokerage to zero and its net becomes its gross, Rs 7,38,658 —
still below the weekly's Rs 7,93,240 *after* the weekly has paid its own costs.
The upper bound on the daily roll is 12.50% CAGR against the weekly's realised
13.19%. No broker discount reaches it.

Costs then make it much worse on top. 8,794 orders against 3,910, and **57% of
the daily bill (Rs 1,51,680) is the mandated straddle round trip** — closing a
position only to re-open a nearly identical one. Only 16.4% of handoffs land on
the same strike, so carrying those over instead of round-tripping would save
Rs 18,240 and lift the CAGR to about 9.2%. Not a rescue.

The mechanism is that a one-overnight cycle does not give the adjustment rules
enough time to work. Adjustments run at 1.9 per cycle versus 5.9 per week, and
the add trigger fired **1,828 times with no strike available in the 20-30% band**
— more often than the 1,698 adds that did happen. The position is repeatedly
reset to flat ATM before the adjustment structure that earns the weekly its
2.63 profit factor can assemble.

Capital is not saved either. The daily roll still reaches 3 legs on one side
within a single overnight, so peak margin is Rs 6,48,075 — the same Rs 6.5L the
weekly needs.

One finding runs against expectation: the 333 cycles that close **on** expiry day
average Rs 709 against Rs 256 for all others. Expiry-day theta helps here, where
in the weekly version expiry-day gamma produced the entire tail. It is not enough
to change the conclusion.

Run it:

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py     --mode daily --allow-stale-entry --balance-max-diff 1.0     --strike-search-steps 0 --check-interval 60
```

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
