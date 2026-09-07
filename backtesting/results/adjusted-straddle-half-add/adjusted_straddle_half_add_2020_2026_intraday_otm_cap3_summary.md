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

- Period: `2020-01-06` to `2026-06-16` (6.44 years)
- Cycles traded: `893` (skipped `713`)
- Total adds: `1984`, total unwinds: `1249`
- Add trigger fired but **no strike existed in the target band**: `3848` times
- Add strike rule: `otm-spot`
- Total rolls at the leg cap: `412`
- Orders executed: `8364`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 311,306.20 |
| Costs | Rs 250,920.00 |
| **Net P/L** | **Rs 60,386.20** |
| CAGR | 2.89% |
| Max drawdown | Rs 87,322.50 |
| Win rate | 56.22% (502W / 391L) |
| Profit factor | 1.09 |
| Best cycle | Rs 14,100.00 |
| Worst cycle | Rs -16,808.25 |
| Final equity | Rs 360,386.20 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 123 | Rs 43,852.50 | 61.0% |
| 2021 | 153 | Rs 30,231.25 | 60.1% |
| 2022 | 154 | Rs 11,420.00 | 60.4% |
| 2023 | 96 | Rs -22,842.50 | 45.8% |
| 2024 | 147 | Rs -35,334.50 | 52.4% |
| 2025 | 143 | Rs 38,991.00 | 58.0% |
| 2026 | 77 | Rs -5,931.55 | 49.4% |

## Skips

| Reason | Count |
|---|---:|
| `balance_check_failed` | 427 |
| `missing_entry_bar` | 277 |
| `no_spot_at_entry` | 6 |
| `missing_atm_contract` | 3 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 2185).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_intraday_otm_cap3_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_intraday_otm_cap3_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_intraday_otm_cap3_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_intraday_otm_cap3.log`
