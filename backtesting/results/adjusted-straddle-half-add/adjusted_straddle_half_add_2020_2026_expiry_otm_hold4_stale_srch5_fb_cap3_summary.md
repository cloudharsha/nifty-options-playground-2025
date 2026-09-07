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

- Period: `2020-01-01` to `2026-06-16` (6.46 years)
- Cycles traded: `333` (skipped `1`)
- Total adds: `2543`, total unwinds: `2173`
- Add trigger fired but **no strike existed in the target band**: `45539` times
- Add strike rule: `otm-spot`
- Hold capped to the last `4` sessions before expiry
- Contract: **weekly expiry**
- Total rolls at the leg cap: `677`
- Entry strike search: +/-`5` strikes around ATM with best-balance fallback; entries away from ATM: `88` of `333`
- Orders executed: `7772`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 1,026,462.75 |
| Costs | Rs 233,160.00 |
| **Net P/L** | **Rs 793,302.75** |
| CAGR | 22.18% |
| Max drawdown | Rs 63,497.15 |
| Win rate | 62.46% (208W / 125L) |
| Profit factor | 2.07 |
| Best cycle | Rs 47,752.50 |
| Worst cycle | Rs -41,246.25 |
| Final equity | Rs 1,093,302.75 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 53 | Rs 141,363.75 | 60.4% |
| 2021 | 52 | Rs 186,480.00 | 73.1% |
| 2022 | 52 | Rs 148,345.00 | 65.4% |
| 2023 | 51 | Rs 34,795.00 | 56.9% |
| 2024 | 53 | Rs 59,544.25 | 52.8% |
| 2025 | 52 | Rs 239,304.75 | 75.0% |
| 2026 | 20 | Rs -16,530.00 | 40.0% |

## Skips

| Reason | Count |
|---|---:|
| `missing_entry_bar` | 1 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 24398).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_expiry_otm_hold4_stale_srch5_fb_cap3_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_expiry_otm_hold4_stale_srch5_fb_cap3_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_expiry_otm_hold4_stale_srch5_fb_cap3_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_expiry_otm_hold4_stale_srch5_fb_cap3.log`
