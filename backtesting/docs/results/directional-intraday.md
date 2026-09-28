# Directional Intraday — Gap, ORB, PDH/PDL

Three intraday directional signals from [`strategies/directional/`](../../../strategies/directional/),
each tested over ~1,600 NIFTY sessions at their **documented defaults**, with
kill criteria agreed before the run.

**All three fail.** None reaches a profit factor of 1.15 on the underlying, and
the best return-per-drawdown is 0.95 against a threshold of 2.0.

- Scripts: [`backtesting/python/directional-intraday/`](../../python/directional-intraday/)
- Results: [`backtesting/results/directional-intraday/`](../../results/directional-intraday/)

Back to the [backtesting index](../../README.md).

## Two columns, two questions

Every run reports the same trades twice:

- **Spot** — the signal as a futures-equivalent at one lot. No theta, no delta,
  no strike. Answers *does this signal predict direction at all?*
- **Option** — the same signal bought as a long ATM CE/PE of the nearest weekly,
  entered and exited at the same minutes, stop and target always defined on spot.

The option column's benchmark is **not zero**. The
[heads-tails long grid](heads-tails.md) buys random ATM options across a 4×7
stop/target grid and **all 28 cells lose**; the best averages **−Rs 119.5 per
trade per lot**. A signal only has to pay for the theta a coin flip cannot.

## Results at the documented defaults

| Strategy | Trades | Spot net | Spot PF | Win% | Max DD | Ret/DD | Option per trade | vs random −119.5 | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| [Gap FADE](../../results/directional-intraday/opening_gap_2020_2026_fade30-100_go150_stall3_r1.5_lots1_summary.md) | 641 | Rs 82,150 | 1.09 | 55.2% | Rs 129,972 | 0.63 | **+Rs 38** | +157 | Dead — but the only signal that pays for its own theta |
| Gap GO | 73 | Rs −31,671 | 0.84 | 38.4% | Rs 63,661 | −0.50 | +Rs 59 | +178 | Dead — and 73 trades is not a sample |
| [ORB 30m](../../results/directional-intraday/opening_range_breakout_2020_2026_or30_close_r1.5_min0_lots1_summary.md) | 1,522 | Rs 17,610 | 1.01 | 49.7% | Rs 182,941 | 0.10 | **−Rs 151** | **−31** | Dead — literally a coin flip, and worse than random in options |
| [PDH/PDL](../../results/directional-intraday/prev_day_range_breakout_2020_2026_skip_atr1.5_r1.5_buf0_lots1_summary.md) | 628 | Rs 63,188 | 1.08 | 43.3% | Rs 66,739 | 0.95 | −Rs 49 | +71 | Dead — best risk-adjusted of the three |

Capital base for the spot column is ~Rs 190k–200k of modelled futures margin
(10% of contract value at one lot). Read the
[index notes](../../README.md#reading-the-numbers) before comparing across families.

## The one result worth keeping: gap fill rate by size

Independent of any P/L, and measured over **every** session in range rather than
only days a trade triggered:

| Gap (abs pts) | Sessions | Filled same day | Filled by 11:00 | Median mins to fill |
|---|---:|---:|---:|---:|
| 0–25 | 396 | 363 (91.7%) | 350 (88.4%) | 0 |
| 25–50 | 331 | 264 (79.8%) | 226 (68.3%) | 8 |
| 50–70 | 237 | 150 (63.3%) | 113 (47.7%) | 25 |
| 70–100 | 265 | 139 (52.5%) | 87 (32.8%) | 50 |
| 100–150 | 185 | 71 (38.4%) | 41 (22.2%) | 80 |
| 150–200 | 83 | 22 (26.5%) | 2 (2.4%) | 220 |
| 200+ | 96 | 9 (9.4%) | 3 (3.1%) | 290 |

**Strictly monotonic across all seven buckets**, with median time to fill rising
from 0 to 290 minutes. The premise the gap strategies rest on — small gaps are
noise that reverts, large gaps are information that persists — is confirmed
decisively on 1,593 sessions.

The third-party claim that gaps under 70 points fill within 90 minutes about 62%
of the time is, if anything, conservative: our figure for that range is 71.5% by
11:00. The claim that 150+ point gaps fill under 25% of the time also holds
(26.5%, and 9.4% beyond 200).

**The statistic is real and the trade built on it is not.** Knowing that a 40-point
gap fills 80% of the time does not produce an edge once you must also choose a
stop, survive the 20% that run, and pay costs.

## Why the gap fade dies: the edge stopped in 2022

| Period | Trades | Spot net | Win% |
|---|---:|---:|---:|
| 2020–2022 | 295 | **Rs 193,182** | 61.0% |
| 2023–2026 | 346 | **Rs −111,032** | 50.3% |

The second half is a coin flip. A single year (2021, +Rs 93,792) exceeds the
whole-sample net, which trips the pre-registered "one regime, not a strategy"
criterion on its own.

### A hypothesis that was tested and rejected

NIFTY roughly doubled across the sample, so the fixed 30–100 point band was
0.27–0.88% of spot in 2020 and only 0.12–0.40% by 2025 — the band more than
halved in real terms. That is the same defect the
[Rs 5–10 premium band](expiry-day-short-premium.md#why-the-band-is-often-unreachable)
had in the expiry-day family, so it was the obvious suspect.

It is not the cause. Re-running with the band fixed as a **percentage of the
previous close** (`--band-mode pct`, 0.15–0.50%) leaves the split essentially
unchanged:

| Band | 2020–2022 | 2023–2026 |
|---|---|---|
| 30–100 points | +Rs 193,182, 61.0% win | −Rs 111,032, 50.3% win |
| 0.15–0.50% of spot | +Rs 162,396, 62.8% win | −Rs 141,567, 50.4% win |

Normalising the band made the full-sample profit factor *worse* (1.09 → 1.03).
Whatever changed after 2022, it is not the index level.

## ORB is the clearest negative

1,522 trades — the largest sample in this folder — at profit factor **1.01** and
a 49.7% win rate. That is not a weak edge; it is the absence of one.

The option column is the damning part: **−Rs 151 per trade against a random
buyer's −Rs 119.5.** Trading the opening-range breakout with long options was
worse than flipping a coin, because the signal produced no directional edge to
offset the theta while still concentrating entries in the morning when premium
is richest.

Two source claims checked:

- *"Shorts produced 75% of ORB profit despite a bull market."* Directionally
  consistent — down-breaks made Rs 72,522 and up-breaks lost Rs 54,912 — but at
  PF 1.01 with 49.3%/50.2% win rates on the two sides, this is noise, not a
  finding.
- *"Large-range sessions outperform small ones."* Not supported. Range buckets
  show no monotonic pattern: 70–100 points made Rs 101,928 while 100–150 lost
  Rs 96,460, and the narrowest bucket (0–40, 64 trades) had the best win rate.

## Where the option expression dies: 0-DTE

A fifth of all sessions are expiry days, so a "nearest weekly" option is 0-DTE on
a fifth of trades. That is where the long option is destroyed:

| Strategy | 0-DTE trades | Spot net | Option net |
|---|---:|---:|---:|
| Gap FADE | 130 | Rs 20,870 | Rs −5,506 |
| ORB | 317 | Rs 11,913 | **Rs −95,181** |

ORB's 0-DTE trades lost **Rs 300 each** while the same signal made money on spot.
Any future long-option expression of an intraday signal should either skip expiry
day or roll to the next weekly — a change worth more than any parameter in these
specs.

## What this rules out, and what it does not

**Ruled out:** these three signals, at their documented defaults, expressed as a
long ATM option. Three independent sources of failure — no spot edge (ORB), a
regime-dependent edge (gap fade), and an edge too small to pay costs (PDH/PDL).

**Not ruled out:** the gap fade's 2020–2022 behaviour is large enough that
something real may have been there and then stopped. And the gap-fill statistic
is solid enough to build a different trade on — one with a stop that is not a
multiple of the gap, which is the parameter most likely to be doing the damage.

Per the pre-registered rule, no parameter sweeps were run: nothing survived the
default configuration, and sweeping a dead strategy until a cell looks good is
how curve fits are manufactured.

## Honest caveats

- Costs are Rs 25/order plus 0.5 pt/order slippage on **both** columns, with spot
  modelled as a futures-equivalent at one lot.
- A 5-minute bar containing both the stop and the target is resolved as the
  **stop**. The series cannot order them, and assuming the target would flatter
  every row here.
- An intrabar spot exit sells the option on the **next** bar; that bar's own open
  is a price from before the trigger existed.
- The nine anomalous sessions (Muhurat evenings, special Saturdays) are excluded
  from trading and from setting reference levels.
- Fills are assumed throughout.
