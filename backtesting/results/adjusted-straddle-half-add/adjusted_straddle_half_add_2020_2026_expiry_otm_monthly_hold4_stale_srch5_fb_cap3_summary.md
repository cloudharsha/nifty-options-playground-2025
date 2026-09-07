# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (EXPIRY)

## Strategy

- Mode: Held to expiry — enter 09:20 the first session after the previous monthly expiry, adjust through every session, close 15:20 on expiry day.
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

- Period: `2020-01-27` to `2026-05-26` (6.33 years)
- Cycles traded: `76` (skipped `0`)
- Total adds: `593`, total unwinds: `505`
- Add trigger fired but **no strike existed in the target band**: `9571` times
- Add strike rule: `otm-spot`
- Hold capped to the last `4` sessions before expiry
- Contract: **monthly expiry** (last expiry of each calendar month)
- Total rolls at the leg cap: `171`
- Entry strike search: +/-`5` strikes around ATM with best-balance fallback; entries away from ATM: `23` of `76`
- Orders executed: `1832`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 212,857.65 |
| Costs | Rs 54,960.00 |
| **Net P/L** | **Rs 157,897.65** |
| CAGR | 6.91% |
| Max drawdown | Rs 41,015.60 |
| Win rate | 51.32% (39W / 37L) |
| Profit factor | 1.82 |
| Best cycle | Rs 47,752.50 |
| Worst cycle | Rs -21,915.00 |
| Final equity | Rs 457,897.65 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 12 | Rs 58,605.00 | 50.0% |
| 2021 | 12 | Rs 11,196.25 | 58.3% |
| 2022 | 12 | Rs -3,105.00 | 50.0% |
| 2023 | 11 | Rs -14,840.00 | 45.5% |
| 2024 | 12 | Rs 44,213.75 | 50.0% |
| 2025 | 12 | Rs 52,317.75 | 58.3% |
| 2026 | 5 | Rs 9,509.90 | 40.0% |

## Skips

| Reason | Count |
|---|---:|

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 3410).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_expiry_otm_monthly_hold4_stale_srch5_fb_cap3_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_expiry_otm_monthly_hold4_stale_srch5_fb_cap3_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_expiry_otm_monthly_hold4_stale_srch5_fb_cap3_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_expiry_otm_monthly_hold4_stale_srch5_fb_cap3.log`
