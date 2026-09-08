# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (ROLL)

## Strategy

- Mode: Weekly roll — enter 15:20 one session before expiry in the NEXT week's contract, hold, then roll at 15:20 one session before that expiry. Never flat, never holds expiry-day gamma.
- Entry: sell 1 lot ATM straddle at `15:20` (ATM = spot rounded to nearest 50)
- Balance filter: skip unless `min(CE,PE)/max(CE,PE) >= 0%` (CE/PE within 100%)
- Add trigger: weaker side total `<= 50%` of stronger side total
- Add size: new short on the weaker side targeting `25%` of the stronger side, accepted in band `20%-30%`
- Add strike: strictly further OTM than every existing leg on that side
- Legs capped at `3` per side. At the cap the strategy ROLLS instead of adding: exit the cheapest leg on the weak side and re-sell so the weak side totals `75%` of the strong side (band `65%-85%`)
- Unwind: when the single side falls to `<= 100%` of the stacked side total, buy back the cheapest leg on the stacked side — one leg per parity touch
- Symmetric for upside and downside moves
- **No stop loss.** No target. Pure test.
- Position size: 1 lot; lot size from expiry date (75/50/25/75/65 by era)
- Costs: Rs 30 per order per leg (Rs 30 sell + Rs 30 buy), slippage 0.00 pt/order
- Pricing: 1-minute option `open`; checks every 60 minute(s)
- Reference capital for CAGR/DD: Rs 300,000

## Results

- Period: `2024-12-24` to `2026-06-15` (1.47 years)
- Cycles traded: `73` (skipped `260`)
- Total adds: `273`, total unwinds: `179`
- Add trigger fired but **no strike existed in the target band**: `66` times
- Add strike rule: `otm-spot`
- Held from the day after the previous expiry
- Contract: **weekly expiry**
- Total rolls at the leg cap: `56`
- Entry strike search: +/-`0` strikes around ATM; entries away from ATM: `0` of `73`
- Orders executed: `950`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 292,350.35 |
| Costs | Rs 28,500.00 |
| **Net P/L** | **Rs 263,850.35** |
| CAGR | 53.48% |
| Max drawdown | Rs 54,172.50 |
| Win rate | 63.01% (46W / 27L) |
| Profit factor | 2.33 |
| Best cycle | Rs 44,293.50 |
| Worst cycle | Rs -24,952.50 |
| Final equity | Rs 563,850.35 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2024 | 1 | Rs -4,106.25 | 0.0% |
| 2025 | 53 | Rs 234,333.00 | 67.9% |
| 2026 | 19 | Rs 33,623.60 | 52.6% |

## Skips

| Reason | Count |
|---|---:|
| `missing_entry_bar` | 260 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 176).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_roll_otm_stale_nobal_cap3_ci60_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_roll_otm_stale_nobal_cap3_ci60_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_roll_otm_stale_nobal_cap3_ci60_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_roll_otm_stale_nobal_cap3_ci60.log`
