# Weekly Adjusted ATM Straddle — final spec

The strategy settled on after testing 20+ variants of the straddle-adjustment
idea. Full result tables: [adjusted-straddle.md](results/adjusted-straddle.md).
Runner: [`../python/adjusted-straddle-half-add/`](../python/adjusted-straddle-half-add/).

## Rules

**Entry.** At 15:20 one session before expiry, sell 1 lot of the **next week's**
ATM straddle. Search ±5 strikes around ATM and take the nearest strike whose CE
and PE are within 20% of each other. If none qualifies, sit the week out.

**Adjustment.** When the weaker side's total falls to **≤50%** of the stronger
side, sell one more option on the weak side worth **~25%** of the stronger side
(accept anything in 20–30%). The new strike must be **OTM against current spot** —
not merely further out than the legs already held.

**Cap.** Never exceed **3 legs per side**. At the cap, do not add a fourth: exit
the cheapest leg on the weak side and re-sell so that side totals ~75% of the
strong side.

**Unwind.** When the single side falls back to at or below the stacked side's
total, buy back **one** leg — the cheapest. One leg per parity touch, so the
stack unwinds gradually. The original ATM leg is the most expensive on its side
and therefore always the last to go.

**Exit.** Roll the entire position at 15:20 one session before expiry: close the
old and open the next week's in the same minute. Never hold expiry day.

**No stop loss.** Costs Rs 30 per order per leg.

```bash
python backtesting/python/adjusted-straddle-half-add/run_adjusted_straddle_half_add_2020_2026.py \
    --mode roll --allow-stale-entry
```

## Capital

Budget **Rs 6.5L** of margin for one lot. That is the peak the position reaches
(3 legs one side + 1 the other), not the typical requirement — median across
cycles is about Rs 3.1L, but the peak is what must be funded or the position is
liquidated in the week that matters.

This figure comes from a model (10% of contract value per naked short lot,
same-side legs additive, cross-side netting at 30%), **not from SPAN**. Verify a
3 CE + 1 PE NIFTY position on a real margin calculator before sizing — every
return figure below rests on it.

## What to expect

Use the six-year held-to-expiry numbers, not the roll's headline:

| | Value |
|---|---:|
| CAGR | **15.16%** |
| Max drawdown | Rs 41,725 |
| Win rate | 69% |
| Profit factor | 2.91 |
| Cycles | 245 over 6.4 years, every year profitable |

The roll returns 39% CAGR over its measurable window, but that is 73 cycles in
18 months of a single regime. Treat it as "the roll does not hurt, and probably
helps" rather than as a forecast.

## Why each choice

Every rejected alternative was tested, not assumed:

| Rejected | Cost | Evidence |
|---|---|---|
| Uncapped adds | −8 CAGR points, 2.75x the capital | Stacked to 12 legs, Rs 17.8L peak margin |
| Adds only further OTM than existing legs | Disengages in crashes, silently | COVID week needed a CE worth 66; the best available beyond the existing leg was 27.5, so nothing was added and the week lost Rs 72,596 |
| Dropping the 20% balance requirement | Rs 41,725 → Rs 75,972 drawdown for +1 CAGR point | 6-year held-to-expiry runs |
| Holding through expiry day | −14% net, 2x drawdown | 73-cycle like-for-like against the roll |
| Intraday instead of weekly | 15.16% → 2–3% | Costs consume 73–86% of gross over 893 cycles |
| Monthly contracts | 15.16% → 3.45% | 4.4x fewer cycles for identical margin |
| A stop loss | not tested | Deliberately excluded; the cap and unwind are the risk control |

## Two things that are not settled

**The ±5 strike search is mode-dependent, and that is unexplained.** Held to
expiry it costs 2.4x drawdown for one CAGR point and should be dropped. In roll
mode it is mildly positive (return per unit drawdown 14.3 → 15.9) and the weeks
it recovers earn 39% of a core week rather than 30%. The spec above includes it
because the spec rolls. A plausible reason is that CE/PE imbalance at 15:20 the
day before expiry is mechanical — forward and skew — rather than informative,
while imbalance at 09:20 with five days to run says something real about the
week ahead. That is a hypothesis, not a finding. **If you drop the roll, drop
the strike search with it.**

**The roll is the weakest-evidenced part.** 2020–2024 cannot be tested: the
dataset carries no bars for next week's contract until the current one expires
(pre-2025 weekly contracts hold exactly 5 sessions, starting the day after the
previous expiry). If the roll disappoints live, fall back to holding to expiry
with ATM-only entry — that is the 6-year-validated configuration.

`--balance-fallback` is deliberately **not** in the spec. In 73 roll cycles the
±5 search always found a balanced strike, so the flag never once changed an
outcome.
