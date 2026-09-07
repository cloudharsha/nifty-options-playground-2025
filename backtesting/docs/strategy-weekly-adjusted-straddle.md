# Weekly Adjusted ATM Straddle — final spec

The configuration settled on after testing 25+ variants. Full tables:
[adjusted-straddle.md](results/adjusted-straddle.md). Runner:
[`../python/adjusted-straddle-half-add/`](../python/adjusted-straddle-half-add/).

## Rules

**Entry.** At 09:20 on the first session after the previous expiry, sell 1 lot of
that week's **ATM** straddle. Enter only if CE and PE are within 20% of each
other; otherwise sit the week out.

**Adjustment.** When the weaker side's total falls to **≤50%** of the stronger
side, sell one more option on the weak side worth **~25%** of the stronger side
(accept 20–30%). The new strike must be **OTM against current spot** — not merely
further out than the legs already held.

**Cap.** Never exceed **3 legs per side**. At the cap, exit the cheapest leg on
the weak side and re-sell so that side totals ~75% of the strong side.

**Unwind.** When the single side falls back to at or below the stacked side's
total, buy back **one** leg — the cheapest. One per parity touch.

**Exit.** Close at 15:20 **one session before expiry**, and stay flat through
expiry day.

**No stop loss.** Costs Rs 30 per order per leg.

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode expiry --allow-stale-entry --exit-lead-sessions 1 --strike-search-steps 0
```

## What to expect

245 cycles over 6.4 years, every year profitable:

| | Value |
|---|---:|
| Net P/L | Rs 9,34,197 |
| CAGR on Rs 6.45L peak margin | **14.94%** |
| Max drawdown | Rs 41,246 |
| Win rate | ~69% |

Budget **Rs 6.5L** of margin per lot — the peak (3 legs one side, 1 the other),
not the median of ~Rs 3.0L. The peak is what must be funded. That figure is
modelled (10% of contract value per naked short lot, cross-side netting at 30%),
**not SPAN**: verify a 3 CE + 1 PE position on a real calculator before sizing,
because every return number rests on it.

## The one decision that matters

Entry strike selection drives drawdown; almost nothing else does.

| Entry rule | Cycles | Net P/L | CAGR | Max DD | CAGR per Rs 1L of DD |
|---|---:|---:|---:|---:|---:|
| **ATM only, skip unbalanced weeks** | 245 | Rs 9,34,197 | 14.94% | **Rs 41,246** | **36.2** |
| ±5 strike search | 322 | Rs 10,84,694 | 16.53% | Rs 99,098 | 16.7 |

The strike search earns 1.6 more CAGR points and **2.4x the drawdown**. The 77
extra weeks it unlocks are precisely the ones the balance filter was right to
decline: they earn about a third of what a core week earns. Skip them.

## Exit timing barely matters

Closing a session early versus holding to expiry, same entries, 6 years:

| | Net P/L | Max DD |
|---|---:|---:|
| Exit 1 session early | Rs 9,34,197 | Rs 41,246 |
| Hold to expiry day | Rs 9,54,046 | Rs 41,725 |

Under half a CAGR point apart, drawdown effectively identical. **Choose on
execution, not on edge** — the spec exits early because an expiry-day 15:20 exit
in a multi-leg adjusted position is hard to actually achieve.

**Avoiding expiry day does not reduce tail risk.** On every stress week the two
are identical to the rupee:

| Week | Difference |
|---|---:|
| 2020-03-06, 2020-03-13 (COVID) | +0 |
| 2022-06-10 | +0 |
| 2025-04-04 (tariff selloff) | +0 |

By expiry day the damage is already done — those weeks were lost mid-week, on the
move itself, not to expiry-day gamma.

## Why each rejected alternative was rejected

| Rejected | Cost | Evidence |
|---|---|---|
| Uncapped adds | −8 CAGR points, 2.75x capital | Stacked to 12 legs, Rs 17.8L peak margin |
| Adds only further OTM than existing legs | Silently disengages in crashes | COVID week needed a CE worth 66; best available beyond the held leg was 27.5, so nothing was added and the week lost Rs 72,596 |
| Dropping the 20% balance filter | Rs 41,725 → Rs 75,972 drawdown | 6-year runs |
| ±5 strike search | 2.4x drawdown for 1.6 CAGR points | Table above |
| Intraday instead of weekly | 14.94% → 2–3% | Costs consume 73–86% of gross over 893 cycles |
| Monthly contracts | 14.94% → 3.45% | 4.4x fewer cycles for identical margin |
| A stop loss | not tested | Deliberately excluded; the leg cap and unwind are the risk control |

## `--mode roll`: promising, unproven, do not size for it

A continuous roll — enter next week's contract at 15:20 a session before expiry,
never flat, never holding expiry day — returned 39% CAGR with only Rs 25,597
drawdown over 73 cycles.

**Do not plan around those numbers.**

- **It covers 18 months, and cannot be tested further back.** The roll must buy
  next week's contract while this week is still alive. In this dataset that
  contract has no bars until the day after the current expiry: an exhaustive scan
  found next-week data available early in **0 of 52 expiries in 2020**, 0 of 52
  in 2021, 0 of 52 in 2022, 1 of 53 in 2023, 0 of 52 in 2024 — then **53 of 53 in
  2025**. Five empty years. This is a data-capture gap, not a market fact: NSE
  listed those weeklies concurrently and they really were tradeable.
- **Its window contains no crisis.** Three of the six-year strategy's five worst
  weeks fall outside it, including both COVID weeks (−Rs 57,851 and −Rs 41,246
  back to back).
- **The window was unusually generous** — Rs 4,981 per cycle in 2025–26 against
  Rs 2,691 in 2020–24.
- **Its low drawdown is not evidence the mechanism helps.** The clean 6-year test
  of the same idea (exit-lead-sessions, above) shows zero drawdown improvement.

The roll is still the more realistic way to trade — no overnight flat gap, no
expiry-day fills — and worth running live. Just size from the 14.94% / Rs 41,246
figures above, and treat any improvement as upside rather than plan.

To settle it properly: re-pull 2020–2024 weekly contracts with full listed
history. `--mode roll` then runs unchanged.
