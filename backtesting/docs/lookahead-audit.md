# Lookahead audit — the 25-SMA directional families

**Every 2020–2026 result in the 25-SMA intraday and overnight families was
wrong, and all of them were wrong in the same direction: too good.** Three
separate places in those scripts read a price that did not exist yet at the
moment the backtest claimed to trade. Fixing all three turns the best-performing
strategy in this repo into the worst one.

This document records what the bugs were, how to recognise them, and what the
corrected numbers are. The pre-fix numbers are kept below so the size of the
error stays visible.

Back to the [backtesting index](../README.md).

## The rule that was broken

A bar stamped `T` covers `T .. T+interval`. Its high, low and close are only
knowable at `T+interval`. Two consequences the original code violated:

- A 15-minute bar stamped `09:15` closes at **09:30**. Anything before 09:30
  cannot read it.
- If a stop is detected from a 5-minute bar's high or low, the touch happened
  *inside* that bar — at or after its open. That bar's open is therefore a
  price from **before** the stop existed, and cannot be the fill.

## Bug 1 — stop-loss filled at a pre-trigger price

*Files:* all five `25ma-intraday/run_short_atm_nifty_ma_weekly_intraday_trailing*.py`

The trailing-MA stop is checked against a 5-minute spot bar's high/low. When it
fired, the exit filled at the option's open **at the same timestamp**:

```python
stop_hit = (spot_row.low_value <= stop_sma if sold_side == "PE"
            else spot_row.high_value >= stop_sma)
if stop_hit:
    exit_row = contract_data.rows_by_timestamp.get(spot_ts)   # <- bug
```

So the backtest observed the whole bar, concluded the stop had been hit, and
then exited at the price the bar started at. On a short option that bar is
almost always moving against the position, which means the fill was
systematically better than anything reachable in practice.

The fingerprint is visible in the old output: **30.7% of stop-loss exits were
profitable** — the stop supposedly "locking in gains". After the fix that figure
is 21.5%, and the day-level win rate falls from 65.7% to 53.2%.

*Fix:* fill at the option open of the next 5-minute bar, the first price
actually reachable once the touch has been observed.

## Bug 2 — the 09:20 entry read a bar that closes at 09:30

*Files:* the three `..._0920_random*.py` variants

These enter at 09:20 and took their direction from the `09:15` 15-minute bar —
which does not close until 09:30. Ten minutes of future information decided
which side to sell. This is the variant that produced the repo's former headline
number (31.72% CAGR).

*Fix:* at 09:20 the newest fully-closed 15-minute bar is the **previous
session's 15:15** candle, so that is what the signal now uses. The ATM strike is
taken from the 09:15 5-minute bar, which closes at 09:20 and is the freshest
price legitimately available at entry.

## Bug 3 — the overnight entry preceded its own signal bar

*Files:* both `25ma-overnight/run_*_2020_2026.py`

Signal bar `15:15`, entry `15:29`. The 15:15 bar closes at **15:30**. The
script's own summary described the bar as a "15:30 close proxy" — that is, it
knowingly traded one minute *before* the close it was reacting to.

*Fix:* the default signal bar is now `15:00`, which closes at 15:15 and is
genuinely known at a 15:29 entry.

## Bug 4 — CAGR returned a complex number (exposed by the fix)

`compute_cagr` evaluated `(1 + net/capital) ** (365.25/days)`. Once losses
exceed the capital base that ratio is negative, and a fractional power of a
negative number is complex. The first corrected run reported a CAGR of
`-18.87+36.32j%`.

*Fix:* a wiped-out account floors at `-100.00%`.

## Before and after

Same scripts, same data, same costs — only the causality fixed.

### 25-SMA intraday

| Run | Was | Now |
|---|---:|---:|
| Trailing baseline, 09:30 (5m stop) | Rs 67,11,939 / 31.48% | **−Rs 14,15,087 / −100%** |
| 09:20 entry, 30% random skip | Rs 68,20,328 / 31.72% | **−Rs 11,68,852 / −69.06%** |
| 09:20 entry, 40% random skip | Rs 57,86,958 / 29.24% | **−Rs 10,52,214 / −51.39%** |
| 09:20 entry, 50% random skip | Rs 47,74,003 / 26.47% | **−Rs 9,50,304 / −39.07%** |
| 09:30 entry, 30% random skip | Rs 27,02,634 / 19.16% | **−Rs 4,13,558 / −7.85%** |
| 09:20 + 2-SL/day cap, 30% skip | Rs 51,08,988 / 27.43% | **−Rs 2,05,723 / −3.63%** |
| 09:20 + 2-SL cap + gap ≤150, 30% skip | Rs 42,92,189 / 24.99% | **−Rs 3,13,403 / −6.38%** |
| 09:20 + 2-SL cap + gap ≤75, 30% skip | Rs 32,23,660 / 21.26% | **−Rs 1,19,994 / −2.27%** |

Max drawdown on the baseline moves from Rs 1,36,705 to Rs 19,86,026 — the old
figure was not a plausible drawdown for a strategy claiming Rs 67L of profit,
which is the kind of thing worth noticing earlier than we did.

### 25-SMA overnight

| Offset | Was | Now |
|---|---:|---:|
| ITM 300 | Rs 26,53,098 / 18.96% | **Rs 16,29,235 / 13.83%** |
| ITM 200 | Rs 27,36,233 / 19.32% | **Rs 18,24,282 / 14.93%** |
| ITM 100 | Rs 23,08,668 / 17.39% | **Rs 16,52,625 / 13.96%** |
| OTM 100 | Rs 11,72,399 / 10.95% | **Rs 6,51,606 / 6.95%** |
| OTM 200 | Rs 7,36,394 / 7.67% | **Rs 2,26,421 / 2.77%** |
| OTM 300 | Rs 4,45,963 / 5.07% | **Rs 22,715 / 0.30%** |
| OTM 400 | Rs 1,85,151 / 2.30% | **−Rs 1,52,176 / −2.19%** |
| OTM 500 | −Rs 86,223 / −1.20% | **−Rs 3,63,001 / −5.86%** |
| Long ATM | Rs 3,30,944 / 7.04% | **−Rs 1,82,442 / −5.90%** |

One minute of hindsight was worth 4–5 percentage points of CAGR a year.

Offset rows are exact-match runs (`--fallback-window-minutes 0`); the script's
own default of 30 produces the separate
[`short-offsets-fallback/`](../results/25ma-overnight/short-offsets-fallback/)
folder, which was re-run too.

## What this does to the conclusions

The [Heads & Tails](results/heads-tails.md) random-entry control was audited
and is **clean** — it fills a triggered stop at the stop price itself, not at a
bar open, which is the correct treatment for a resting order. Its 17.38% CAGR
therefore stands unchanged.

That leaves the comparison unambiguous: after the fix, **no 25-SMA directional
variant is profitable at all**, while the coin-flip control on the same
instrument and the same costs returns 17.38%. The signal was never beating
random entry; it was beating it only by reading prices from the future.

The [same-week intraday](results/25ma-intraday.md) script was audited and needed
no fix — it computes its MA over `ordered_rows[idx - ma_period : idx]`, strictly
prior bars, and compares against the current bar's open. It was already correct,
and its 1.76% CAGR is unchanged.

## Guarding against a repeat

[`python/tests/test_lookahead_guards.py`](../python/tests/test_lookahead_guards.py)
asserts each rule directly: signal bars must have closed before the entry they
inform, stop fills must follow the bar that detected the touch, and CAGR must
stay a real number. Run it with:

```bash
python backtesting/python/tests/test_lookahead_guards.py
```

## The archived studies

The underlying-only studies in [directional-studies.md](results/directional-studies.md)
were **not** re-run: `python/legacy/` is deliberately non-functional (see that
folder's README). They carry a separate and larger problem — they charge no
brokerage or slippage at all, over as many as 4,306 trades. At this repo's own
cost convention that is roughly Rs 180/trade, which removes about Rs 7.75L of
the Rs 11.88L headline on the continuous-trailing run. Treat every number in
that table as an upper bound that has not been audited for lookahead either.
