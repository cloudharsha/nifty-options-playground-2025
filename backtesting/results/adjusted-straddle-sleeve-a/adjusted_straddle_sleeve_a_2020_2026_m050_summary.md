# NIFTY Adjusted Straddle — Sleeve A replication (margin 0.50)

## Strategy

- One cycle per weekly expiry, no overlap. Entry is the first session after the previous expiry; exit is expiry day.
- **Entry 09:20:** skip if the previous day's India VIX close < `12`; ATM = `round(spot/50)*50`; require `min(CE,PE)/max(CE,PE) >= 0.80`; if ATM fails, walk out `ATM, -50, +50, ... +/-250` and take the first strike that passes, else skip the cycle. Both legs must price off an exact `09:20` bar. Sell 1 CE + 1 PE.
- **Every minute**, up to `12` actions per minute, in order:
  1. **Unwind** — if the leg counts differ and `single <= stacked * 1.00`, buy back the cheapest stacked leg.
  2. **Add** — if `weak <= 0.50 * strong`: with `< 4` legs on the weak side, sell one new leg targeting `0.20 * strong` (band `0.15`-`0.25`), OTM against current spot, not already held, exact bar this minute, closest to target with the original ATM as tie-break. At `4` legs, **roll** instead: buy back the cheapest weak leg and sell so the weak side totals `0.75 * strong` (band `0.65`-`0.85`).
  3. **Exit** every leg at `15:20` on expiry day.
- **No stop loss. No take profit.**

## Sizing and costs

- `lots = floor(1,000,000 / (spot x lot_size x 0.50))`, fixed at entry, non-compounding. Mean lots per cycle: `1.70`.
- Lot size from the contract's expiry date (75 / 50 / 25 / 75 / 65 by era).
- Costs per order: Rs 20 brokerage; STT `0.05% -> 0.0625% (2023-04-01) -> 0.10% (2024-10-01) -> 0.15% (2026-04-01)` on sell-side premium; exchange `0.03503%`; SEBI `0.0001%`; stamp `0.003%` buy-side; GST `18%` on brokerage + exchange + SEBI.
- Slippage `0.25` points per side on every fill.

## Results

- Period: `2020-01-10` to `2026-06-16` (6.43 years)
- Cycles traded: `266` (skipped `68` of `334`)
- Adds `2665` · unwinds `2191` · rolls `521`
- Minute-checks where the add trigger was live but no strike sat in the target band: `41559` (the trigger stays live until a strike qualifies, so this counts minutes, not distinct events); same for rolls: `73571`
- Orders executed: `7436`
- Max legs open at once: `5`
- Entries away from ATM: `80` of `266`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 1,948,766.25 |
| Costs | Rs 211,891.75 |
| **Net P/L** | **Rs 1,736,874.50** |
| CAGR | 16.95% |
| Sharpe | 2.58 |
| Max drawdown | Rs 77,100.11 (7.42%) |
| Profit factor | 3.17 |
| Win rate | 74.06% (197W / 69L) |
| Best cycle | Rs 96,783.67 |
| Worst cycle | Rs -67,482.98 |
| Final equity | Rs 2,736,874.50 |

## Splits (equal thirds of the traded cycles)

| Segment | From | To | Cycles | Net P/L | CAGR |
|---|---|---|---:|---:|---:|
| 1 | 2020-01-10 | 2021-10-28 | 88 | Rs 833,353.77 | 40.07% |
| 2 | 2021-10-29 | 2024-02-15 | 89 | Rs 526,199.35 | 20.21% |
| 3 | 2024-02-16 | 2026-06-16 | 89 | Rs 377,321.38 | 14.73% |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 48 | Rs 635,392.92 | 77.1% |
| 2021 | 49 | Rs 270,589.69 | 81.6% |
| 2022 | 51 | Rs 346,075.02 | 74.5% |
| 2023 | 23 | Rs 108,471.35 | 73.9% |
| 2024 | 48 | Rs 121,415.96 | 66.7% |
| 2025 | 33 | Rs 187,463.73 | 69.7% |
| 2026 | 14 | Rs 67,465.83 | 71.4% |

## Skips

| Reason | Count |
|---|---:|
| `vix_below_floor` | 56 |
| `balance_check_failed` | 8 |
| `no_spot_at_entry` | 2 |
| `no_prev_vix` | 1 |
| `missing_entry_bar` | 1 |

## Notes

- Option prices are the 1-minute bar **close**; a leg already open is marked at the last close at or before the check minute. `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 32267).
- A candidate strike for an add or roll must have an **exact** bar at the check minute, so an illiquid strike is never sold on a stale quote.
- Spot is the 5-minute index close (the repo has no 1-minute spot before 2025), used for the entry ATM and for the OTM test on adds.
- India VIX is the daily close from `backtesting/data/india_vix_daily.csv`; the gate reads the last session strictly before the entry date.
- Sharpe is computed on per-cycle returns over the fixed Rs 1,000,000 base, annualised by sqrt(41.4) cycles/year, with a zero risk-free rate.
- Weekly expiry comes from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).

## Files

- Cycles: `adjusted_straddle_sleeve_a_2020_2026_m050_cycles.csv`
- Legs: `adjusted_straddle_sleeve_a_2020_2026_m050_legs.csv`
- Equity: `adjusted_straddle_sleeve_a_2020_2026_m050_equity.csv`
