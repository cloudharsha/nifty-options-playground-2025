# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (INTRADAY)

## Strategy

- Mode: Intraday — enter 09:20, close all legs 15:20 same session.
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

- Period: `2020-01-28` to `2026-06-19` (6.39 years)
- Cycles traded: `540` (skipped `1066`)
- Total adds: `679`, total unwinds: `401`
- Add trigger fired but **no strike existed in the target band**: `1074` times
- Add strike rule: `otm-spot`
- Contract: **monthly expiry** (last expiry of each calendar month)
- Total rolls at the leg cap: `122`
- Entry strike search: +/-`5` strikes around ATM; entries away from ATM: `252` of `540`
- Orders executed: `3762`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 203,718.75 |
| Costs | Rs 112,860.00 |
| **Net P/L** | **Rs 90,858.75** |
| CAGR | 4.23% |
| Max drawdown | Rs 35,735.25 |
| Win rate | 57.96% (313W / 227L) |
| Profit factor | 1.24 |
| Best cycle | Rs 30,987.75 |
| Worst cycle | Rs -15,011.25 |
| Final equity | Rs 390,858.75 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 33 | Rs 13,376.25 | 60.6% |
| 2021 | 39 | Rs 14,056.25 | 61.5% |
| 2022 | 43 | Rs -2,157.50 | 60.5% |
| 2023 | 32 | Rs -2,595.00 | 43.8% |
| 2024 | 47 | Rs -11,901.25 | 53.2% |
| 2025 | 244 | Rs 71,672.75 | 63.1% |
| 2026 | 102 | Rs 8,407.25 | 49.0% |

## Skips

| Reason | Count |
|---|---:|
| `missing_entry_bar` | 1023 |
| `balance_check_failed` | 43 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 3726).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_intraday_otm_monthly_stale_srch5_cap3_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_intraday_otm_monthly_stale_srch5_cap3_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_intraday_otm_monthly_stale_srch5_cap3_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_intraday_otm_monthly_stale_srch5_cap3.log`
