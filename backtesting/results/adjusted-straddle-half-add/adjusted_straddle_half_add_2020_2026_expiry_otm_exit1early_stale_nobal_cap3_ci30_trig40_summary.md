# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (EXPIRY)

## Strategy

- Mode: Held to expiry — enter 09:20 the first session after the previous weekly expiry, adjust through every session, close 15:20 on expiry day.
- Entry: sell 1 lot ATM straddle at `09:20` (ATM = spot rounded to nearest 50)
- Balance filter: skip unless `min(CE,PE)/max(CE,PE) >= 0%` (CE/PE within 100%)
- Add trigger: weaker side total `<= 40%` of stronger side total
- Add size: new short on the weaker side targeting `25%` of the stronger side, accepted in band `20%-30%`
- Add strike: strictly further OTM than every existing leg on that side
- Legs capped at `3` per side. At the cap the strategy ROLLS instead of adding: exit the cheapest leg on the weak side and re-sell so the weak side totals `75%` of the strong side (band `65%-85%`)
- Unwind: when the single side falls to `<= 100%` of the stacked side total, buy back the cheapest leg on the stacked side — one leg per parity touch
- Symmetric for upside and downside moves
- **No stop loss.** No target. Pure test.
- Position size: 1 lot; lot size from expiry date (75/50/25/75/65 by era)
- Costs: Rs 30 per order per leg (Rs 30 sell + Rs 30 buy), slippage 0.00 pt/order
- Pricing: 1-minute option `open`; checks every 30 minute(s)
- Reference capital for CAGR/DD: Rs 300,000

## Results

- Period: `2020-01-01` to `2026-06-16` (6.46 years)
- Cycles traded: `329` (skipped `5`)
- Total adds: `952`, total unwinds: `509`
- Add trigger fired but **no strike existed in the target band**: `401` times
- Add strike rule: `otm-spot`
- Held from the day after the previous expiry
- Contract: **weekly expiry**
- Total rolls at the leg cap: `77`
- Entry strike search: +/-`0` strikes around ATM; entries away from ATM: `0` of `329`
- Orders executed: `3374`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 887,461.15 |
| Costs | Rs 101,220.00 |
| **Net P/L** | **Rs 786,241.15** |
| CAGR | 22.06% |
| Max drawdown | Rs 79,180.00 |
| Win rate | 63.53% (209W / 120L) |
| Profit factor | 1.72 |
| Best cycle | Rs 50,447.25 |
| Worst cycle | Rs -51,468.75 |
| Final equity | Rs 1,086,241.15 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 52 | Rs 131,962.50 | 63.5% |
| 2021 | 52 | Rs 154,376.25 | 71.2% |
| 2022 | 52 | Rs 116,087.50 | 61.5% |
| 2023 | 51 | Rs 36,920.00 | 60.8% |
| 2024 | 51 | Rs 15,618.00 | 51.0% |
| 2025 | 53 | Rs 291,267.00 | 77.4% |
| 2026 | 18 | Rs 40,009.90 | 50.0% |

## Skips

| Reason | Count |
|---|---:|
| `missing_entry_bar` | 5 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 844).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_nobal_cap3_ci30_trig40_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_nobal_cap3_ci30_trig40_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_nobal_cap3_ci30_trig40_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_expiry_otm_exit1early_stale_nobal_cap3_ci30_trig40.log`
