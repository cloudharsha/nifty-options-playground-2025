# Weekly Adjusted ATM Straddle — Low-Touch

**Status: finalized.** The [weekly adjusted straddle](../weekly-adjusted-straddle/)
retuned for someone who cannot watch the screen every hour. Same structure, same
adjustment logic, two parameters changed:

- **Check three times a day instead of seven** — 09:20, 12:20, 15:20
- **Adjust at a 0.40 trigger instead of 0.50** — a weaker side must fall further
  before you act

That halves the workload to **~3 adjustments a week** and costs **0.65 CAGR
points**. It is not a different strategy; it is the same one, run at a pace a
person with a job can actually keep.

This folder is self-contained: the rules below, and in [`results/`](results/) the
exact output files the numbers come from. Re-running the strategy overwrites
`backtesting/results/`, but never this folder.

---

## In one paragraph

Every week, sell a NIFTY at-the-money straddle — one call and one put at the same
strike. You are betting the index does not move far. When it does move, one side
gets expensive and the other gets cheap; each time the cheap side falls to 40% of
the expensive side, you sell one more option on the cheap side to bring the
position back into balance. When the two sides come back to parity you buy those
extra options back. You never hold more than three options on one side, and you
close everything the day before expiry so you are flat on expiry day. Check three
times a day. Expect about three adjustments a week.

---

## The rules

### 1. Entry

At **09:20** on the first session after the previous weekly expiry, sell **1 lot**
of that week's **ATM** straddle — the CE and the PE at the strike nearest to spot,
rounded to 50.

No entry filter. No strike shopping. **Every week is traded.**

### 2. Monitoring

Check the position **three times a day: 09:20, 12:20, 15:20.** Nothing between.

At each check, compare the **total premium of all CE legs** against the **total
premium of all PE legs**. Whichever is worth more is the "strong" side; the other
is "weak".

### 3. Unwind first

If one side holds more legs than the other, and the single-leg side has fallen to
at or below the total of the stacked side, buy back **one** leg from the stacked
side — the cheapest one. Only one per check.

Do this check before the add check. Coming back to parity takes priority over
pushing further out.

### 4. Otherwise, adjust

If the weak side's total has fallen to **40% or less** of the strong side's total,
sell one more option on the **weak** side, priced at about **25%** of the strong
side's total. Accept anything between 20% and 30%.

The new strike must be **out of the money against current spot** — not merely
further out than the legs you already hold. That distinction matters; see
[What was rejected](../weekly-adjusted-straddle/README.md#what-was-rejected) in the parent spec.

> *Example.* You sold 24000 CE and PE at 100 each. The market falls: PE is now
> 150, CE is now 60. 60 is 40% of 150, so the trigger fires. Sell another CE
> priced near 37.50 (25% of 150), at whatever strike is OTM against spot right
> now.

### 5. Leg cap

Never hold more than **3 legs on one side**. If the trigger fires when the weak
side already has 3 legs, do not add a fourth. Instead **roll**: buy back the
cheapest leg on that side and sell a replacement so the side's total comes to
about **75%** of the strong side (accept 65–85%).

This is rare at this trigger — 20 rolls in 329 weeks, about once every 16 weeks.

### 6. Exit

Close everything at **15:20 one session before expiry**. Stay flat through expiry
day. Re-enter the following week per rule 1.

This is the single most valuable rule in the parent spec: it cuts drawdown 62%
and the worst week 74% for 1.7 CAGR points. Do not skip it.

### 7. No stop loss

There is none, deliberately. The leg cap and the unwind rule are the risk
control. See [What would invalidate this](#what-would-invalidate-this).

---

## Running it

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode expiry \
    --allow-stale-entry \
    --exit-lead-sessions 1 \
    --balance-max-diff 1.0 \
    --strike-search-steps 0 \
    --check-interval 180 \
    --half-trigger-ratio 0.40
```

| Flag | Why |
|---|---|
| `--exit-lead-sessions 1` | Exit a session before expiry |
| `--balance-max-diff 1.0` | Disables the entry filter, so no week is skipped |
| `--strike-search-steps 0` | Plain ATM, no strike shopping |
| `--check-interval 180` | **Three checks a day** |
| `--half-trigger-ratio 0.40` | **The 0.40 add trigger** |

The last two are the only differences from the parent spec.

---

## Results — 2020-01-01 to 2026-06-15

| | |
|---|---:|
| Weeks traded | **329 of 334** |
| Gross P/L | Rs 8,20,726 |
| Costs (Rs 30/order, 2,738 orders) | Rs 82,140 |
| **Net P/L** | **Rs 7,38,586** |
| **CAGR on Rs 6.46L peak margin** | **12.54%** |
| **Max drawdown** | **Rs 56,768** (8.8% of capital) |
| Win rate | 69.0% (227W / 102L) |
| Profit factor | 2.22 |
| Median week | Rs 2,719 |
| Best week | Rs 55,246 |
| Worst week | −Rs 41,190 |
| **Adjustments** | **2.95 per week** (2.1 adds, 0.8 unwinds, 0.06 rolls) |

The 5 untraded weeks are dataset gaps — no priceable ATM straddle in the files —
not the strategy declining a trade.

### Every year profitable

| Year | Weeks | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 52 | Rs 1,52,674 | 73.1% |
| 2021 | 52 | Rs 1,07,250 | 67.3% |
| 2022 | 52 | Rs 1,42,765 | 76.9% |
| 2023 | 51 | Rs 28,235 | 70.6% |
| 2024 | 51 | Rs 20,578 | 56.9% |
| 2025 | 53 | Rs 2,32,032 | 77.4% |
| 2026 (part) | 18 | Rs 55,052 | 44.4% |

**2024 made almost nothing** — Rs 20,578 across 51 weeks. 2023 was not much
better. Low volatility means thin premiums and this strategy has no answer to
that. Plan for the possibility of a flat year, not for 2025.

---

## What the week actually looks like

This is the part that matters if you are choosing on workload.

**Adjustments per week**

| Adjustments | Weeks | Share | Cumulative |
|---:|---:|---:|---:|
| 0 | 12 | 3.6% | 3.6% |
| 1 | 16 | 4.9% | 8.5% |
| **2** | **154** | **46.8%** | **55.3%** |
| 3 | 36 | 10.9% | 66.3% |
| 4 | 58 | 17.6% | 83.9% |
| 5 | 25 | 7.6% | 91.5% |
| 6 | 18 | 5.5% | 97.0% |
| 7 | 7 | 2.1% | 99.1% |
| 8 | 3 | 0.9% | 100.0% |

**The median week needs exactly 2 adjustments.** Half of all weeks are 2 or
fewer. One week in ten needs 6 or more — those are the fast-moving weeks, and
they are also when the adjustments matter most.

**Your actual routine**

| When | What |
|---|---|
| Day after expiry, 09:20 | Sell the ATM straddle. One order pair. |
| Every day, 09:20 / 12:20 / 15:20 | Look at CE total vs PE total. Usually do nothing. |
| ~3 times a week | One adjustment: either an unwind or an add. |
| Session before expiry, 15:20 | Close everything. |
| Expiry day | Flat. Do nothing. |

That is **12 checks a week** (3 a day × 4 sessions) and about **8 orders a week**
including entry and exit.

---

## Capital

**Budget Rs 6.5 lakh of margin per lot.**

That is the *peak* requirement — the position at its heaviest, 3 legs on one side
and 1 on the other, which happens in 255 of the 329 weeks. The **median** margin
across the whole sample is about **Rs 2.07L**, but the peak is what must be
funded, or the position is liquidated in exactly the week that matters.

**This figure is modelled, not SPAN.** It assumes 10% of contract value per naked
short lot, same-side legs additive, cross-side netting at 30%. **Verify a
3 CE + 1 PE NIFTY position on a real margin calculator before sizing.** Every
return number here rests on it: if the true peak is Rs 10L, the CAGR falls to
about 8%, and this stops being worth trading.

Lot size varies by era (75 → 50 → 25 → 75 → 65), keyed to the contract's expiry
date. See [dataset-reference.md](../../docs/dataset-reference.md).

---

## Why 0.40 and not 0.50

**Because the trigger and the check frequency interact, and the parent spec's
advice inverts once you check less often.**

The parent spec tested the 0.40 trigger only at hourly checks, where it was
worse — Rs 7,41,620 net against Rs 7,93,240, and a *higher* drawdown of
Rs 47,902 against Rs 42,159. Its conclusion was "the default 0.50 is the better
trade," and at hourly that is right.

At three checks a day it reverses:

| Checks/day | Trigger | CAGR | Max DD | DD as % of capital | Adj/week |
|---|---|---:|---:|---:|---:|
| 7 (hourly) | 0.50 | 13.19% | Rs 42,159 | 6.5% | 5.86 |
| 7 (hourly) | 0.40 | 12.54% | Rs 47,902 | 7.4% | 4.10 |
| 4 | 0.50 | 12.57% | Rs 45,094 | 7.0% | 4.67 |
| 3 | 0.50 | 12.20% | Rs 80,378 | 12.4% | 4.00 |
| 2 | 0.50 | 12.11% | Rs 93,739 | 14.5% | 3.12 |
| **3** | **0.40** | **12.54%** | **Rs 56,768** | **8.8%** | **2.95** |

*Every configuration reaches the same 3+1 leg maximum, so all peak margins land
between Rs 6.45L and Rs 6.47L; the percentage column uses Rs 6.46L throughout.*

At three checks a day, 0.40 beats 0.50 on **every axis** — more return, a
drawdown Rs 23,610 smaller, and a quarter fewer adjustments.

The reason is that a sparse checker who adjusts at 0.50 keeps catching moves
late. The trigger fires, but hours after the level was crossed, so the add goes
on at a worse price and does less work. Raising the bar to 0.40 means you only
act when the imbalance is large enough to still be worth acting on when you
happen to look.

**The practical warning: do not simply turn down the check frequency and leave
the trigger alone.** That is the 12.4%-drawdown row — you would take nearly half
again the risk of the hourly version for less return.

One bonus: 2023, the flat year the parent spec warns about, improves from
Rs 8,760 to **Rs 28,235** under this configuration.

The control runs are in
[`results/low_touch_straddle_CONTROL_trigger50_summary.md`](results/low_touch_straddle_CONTROL_trigger50_summary.md)
(3 checks, 0.50 trigger) and
[`results/low_touch_straddle_CONTROL_2checks_summary.md`](results/low_touch_straddle_CONTROL_2checks_summary.md)
(2 checks, 0.50 trigger).

---

## What you give up against the parent spec

| | [Hourly, 0.50](../weekly-adjusted-straddle/) | **This (3 checks, 0.40)** |
|---|---:|---:|
| CAGR | 13.19% | **12.54%** |
| Max drawdown | Rs 42,159 (6.5%) | **Rs 56,768 (8.8%)** |
| Adjustments/week | 5.86 | **2.95** |
| Checks/week | 28 | **12** |
| Win rate | 67.5% | **69.0%** |
| Profit factor | 2.63 | 2.22 |
| Worst week | −Rs 27,619 | −Rs 41,190 |
| Return per rupee of drawdown | 18.8 | 13.0 |

**0.65 CAGR points and a Rs 14,609 wider drawdown, for half the adjustments and
57% fewer checks.**

If you can genuinely check hourly, trade the parent spec — it is better on
return and materially better on risk. This version exists because most people
cannot, and a strategy you execute badly at 7 checks a day is worse than one you
execute properly at 3.

---

## The worst weeks

| Week | Loss | Adjustments |
|---|---:|---|
| 2021-01-29 | −Rs 41,190 | 3 adds, 1 unwind |
| 2024-05-31 | −Rs 38,939 | 4 adds, 4 unwinds |
| 2024-11-22 | −Rs 23,456 | 2 adds |
| 2020-11-06 | −Rs 20,509 | 2 adds |
| 2021-01-22 | −Rs 15,578 | 2 adds |
| 2023-12-01 | −Rs 15,145 | 2 adds |

Losses cluster in fast directional moves, which is what a short straddle is
structurally exposed to. The adjustment reduces that exposure; it does not
remove it.

**The longest run of losing weeks is 6.** Expect to sit through that at some
point without concluding the strategy is broken.

Notably COVID does not appear here — exiting the session before expiry removes
it, same as in the parent spec.

---

## What would invalidate this

**Margin.** If a real broker requires materially more than Rs 6.5L at peak, the
CAGR drops proportionally. At Rs 10L it is roughly 8% and no longer clears a
sensible bar.

**Fills.** Costs are charged per order, but the backtest assumes it traded at the
recorded price. Three checks a day actually helps here — a decision made at 12:20
has hours to be executed, unlike a minute-level rule — but a fast market still
fills worse than modelled, and adjustments happen precisely when markets are fast.

**Regime.** 2025 contributed Rs 2.32L of the Rs 7.39L total. Strip it out and the
remaining Rs 5.07L over 5.4 years averages about Rs 93k/year on Rs 6.5L — roughly
14% — but 2023 and 2024 averaged only Rs 24k. Plan for the quiet years, not the
good one.

**Untested tail.** The worst week in the sample is −Rs 41,190. COVID is in the
sample, but this is a naked short straddle with no stop, and a worse event is
always possible.

**Discipline.** This configuration assumes you actually look at 09:20, 12:20 and
15:20. Missing checks does not degrade gracefully — the 2-checks-a-day row above
shows drawdown rising to 14.5% of capital. If you will realistically only look
once a day, this is not the right strategy and none in this repo is.

---

## Provenance

Derived from [`weekly-adjusted-straddle`](../weekly-adjusted-straddle/), which
selected these rules from 30+ tested variants. The only new work here is the
check-frequency and trigger sweep documented above; everything else — the leg
cap, the OTM-vs-spot add rule, the exit a session before expiry, the rejection of
strike search and entry filters — was settled there and is unchanged.

Nothing here is advice. Backtested results are not predictions.
