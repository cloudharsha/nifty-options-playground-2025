# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (DAILY)

## Strategy

- Mode: Daily overnight roll — sell the current week's ATM straddle at 15:20, adjust across the next session, close every leg at 15:20 the next day and open a fresh ATM straddle. Carries into expiry day and closes on it; no cycle starts on an expiry day, so the book is flat one overnight a week.
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

- Period: `2020-01-01` to `2026-06-19` (6.46 years)
- Cycles traded: `1264` (skipped `7`)
- Total adds: `1698`, total unwinds: `554`
- Add trigger fired but **no strike existed in the target band**: `1828` times
- Add strike rule: `otm-spot`
- Held from the day after the previous expiry
- Contract: **weekly expiry**
- Total rolls at the leg cap: `171`
- Entry strike search: +/-`0` strikes around ATM; entries away from ATM: `0` of `1264`
- Orders executed: `8794`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 738,657.75 |
| Costs | Rs 263,820.00 |
| **Net P/L** | **Rs 474,837.75** |
| CAGR | 15.81% |
| Max drawdown | Rs 103,473.75 |
| Win rate | 63.69% (805W / 459L) |
| Profit factor | 1.30 |
| Best cycle | Rs 20,662.50 |
| Worst cycle | Rs -70,339.50 |
| Final equity | Rs 774,837.75 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 199 | Rs 6,971.25 | 62.3% |
| 2021 | 195 | Rs 134,507.50 | 67.2% |
| 2022 | 196 | Rs 78,300.00 | 65.8% |
| 2023 | 191 | Rs 19,285.00 | 62.8% |
| 2024 | 196 | Rs 30,552.50 | 61.2% |
| 2025 | 196 | Rs 184,383.75 | 67.3% |
| 2026 | 91 | Rs 20,837.75 | 53.8% |

## Skips

| Reason | Count |
|---|---:|
| `missing_entry_bar` | 7 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 318).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_daily_otm_stale_nobal_cap3_ci60_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_daily_otm_stale_nobal_cap3_ci60_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_daily_otm_stale_nobal_cap3_ci60_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_daily_otm_stale_nobal_cap3_ci60.log`
