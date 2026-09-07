# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (EXPIRY)

## Strategy

- Mode: Held to expiry — enter 09:20 the first session after the previous expiry, adjust through every session, close 15:20 on expiry day.
- Entry: sell 1 lot ATM straddle at `09:20` (ATM = spot rounded to nearest 50)
- Balance filter: skip unless `min(CE,PE)/max(CE,PE) >= 80%` (CE/PE within 20%)
- Add trigger: weaker side total `<= 50%` of stronger side total
- Add size: new short on the weaker side targeting `25%` of the stronger side, accepted in band `20%-30%`
- Add strike: strictly further OTM than every existing leg on that side
- Legs capped at `3` per side. At the cap the strategy ROLLS instead of adding: exit the cheapest leg on the weak side and re-sell so the weak side totals `75%` of the strong side (band `65%-85%`)
- Unwind: when the single side falls to `<= 100%` of the stacked side total, buy back the cheapest leg on the stacked side — one leg per parity touch
- Symmetric for upside and downside moves
- **No stop loss.** No target. Pure test.
- Position size: 1 lot; lot size from expiry date (75/50/25/75/65 by era)
- Costs: Rs 30 per order per leg (Rs 30 sell + Rs 30 buy), slippage 0.00 pt/order
- Pricing: 1-minute option `open`; checks every 1 minute(s)
- Reference capital for CAGR/DD: Rs 300,000

## Results

- Period: `2020-01-10` to `2026-06-16` (6.43 years)
- Cycles traded: `322` (skipped `12`)
- Total adds: `2464`, total unwinds: `2079`
- Add trigger fired but **no strike existed in the target band**: `44338` times
- Add strike rule: `otm-spot`
- Total rolls at the leg cap: `729`
- Entry strike search: +/-`5` strikes around ATM; entries away from ATM: `77` of `322`
- Orders executed: `7674`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 1,274,089.25 |
| Costs | Rs 230,220.00 |
| **Net P/L** | **Rs 1,043,869.25** |
| CAGR | 26.26% |
| Max drawdown | Rs 99,097.50 |
| Win rate | 68.32% (220W / 102L) |
| Profit factor | 2.47 |
| Best cycle | Rs 45,454.50 |
| Worst cycle | Rs -57,851.25 |
| Final equity | Rs 1,343,869.25 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 48 | Rs 149,917.50 | 66.7% |
| 2021 | 52 | Rs 267,685.00 | 73.1% |
| 2022 | 52 | Rs 169,102.50 | 73.1% |
| 2023 | 48 | Rs 38,720.00 | 58.3% |
| 2024 | 51 | Rs 76,351.75 | 62.7% |
| 2025 | 53 | Rs 301,230.40 | 79.2% |
| 2026 | 18 | Rs 40,862.10 | 55.6% |

## Skips

| Reason | Count |
|---|---:|
| `balance_check_failed` | 9 |
| `missing_entry_bar` | 3 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 37710).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_expiry_otm_stale_srch5_cap3_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_expiry_otm_stale_srch5_cap3_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_expiry_otm_stale_srch5_cap3_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_expiry_otm_stale_srch5_cap3.log`
