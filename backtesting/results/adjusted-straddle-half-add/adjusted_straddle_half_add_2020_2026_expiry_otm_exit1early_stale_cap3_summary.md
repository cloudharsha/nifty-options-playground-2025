# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (EXPIRY)

## Strategy

- Mode: Held to expiry — enter 09:20 the first session after the previous weekly expiry, adjust through every session, close 15:20 on expiry day.
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
- Cycles traded: `245` (skipped `89`)
- Total adds: `1707`, total unwinds: `1400`
- Add trigger fired but **no strike existed in the target band**: `9350` times
- Add strike rule: `otm-spot`
- Held from the day after the previous expiry
- Contract: **weekly expiry**
- Total rolls at the leg cap: `557`
- Entry strike search: +/-`0` strikes around ATM; entries away from ATM: `0` of `245`
- Orders executed: `5508`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 1,099,437.35 |
| Costs | Rs 165,240.00 |
| **Net P/L** | **Rs 934,197.35** |
| CAGR | 24.60% |
| Max drawdown | Rs 41,246.25 |
| Win rate | 68.16% (167W / 78L) |
| Profit factor | 2.68 |
| Best cycle | Rs 45,454.50 |
| Worst cycle | Rs -41,246.25 |
| Final equity | Rs 1,234,197.35 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 41 | Rs 142,151.25 | 65.9% |
| 2021 | 48 | Rs 214,291.25 | 68.8% |
| 2022 | 42 | Rs 143,610.00 | 71.4% |
| 2023 | 29 | Rs 48,187.50 | 58.6% |
| 2024 | 40 | Rs 59,431.25 | 60.0% |
| 2025 | 31 | Rs 271,515.00 | 90.3% |
| 2026 | 14 | Rs 55,011.10 | 57.1% |

## Skips

| Reason | Count |
|---|---:|
| `balance_check_failed` | 84 |
| `missing_entry_bar` | 5 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 18990).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_cap3_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_cap3_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_cap3_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_cap3.log`
