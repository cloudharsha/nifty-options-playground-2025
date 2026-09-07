# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (EXPIRY)

## Strategy

- Mode: Held to expiry — enter 09:20 the first session after the previous expiry, adjust through every session, close 15:20 on expiry day.
- Entry: sell 1 lot ATM straddle at `09:20` (ATM = spot rounded to nearest 50)
- Balance filter: skip unless `min(CE,PE)/max(CE,PE) >= 80%` (CE/PE within 20%)
- Add trigger: weaker side total `<= 50%` of stronger side total
- Add size: new short on the weaker side targeting `25%` of the stronger side, accepted in band `20%-30%`
- Add strike: strictly further OTM than every existing leg on that side
- Adds repeat without limit; 3rd, 4th legs use the same rule
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
- Total adds: `2788`, total unwinds: `2407`
- Add trigger fired but **no strike existed in the target band**: `95623` times
- Add strike rule: `otm-spot`
- Orders executed: `6556`
- Max legs open at once: `12`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 1,199,692.65 |
| Costs | Rs 196,680.00 |
| **Net P/L** | **Rs 1,003,012.65** |
| CAGR | 25.65% |
| Max drawdown | Rs 91,539.00 |
| Win rate | 72.24% (177W / 68L) |
| Profit factor | 3.17 |
| Best cycle | Rs 33,851.25 |
| Worst cycle | Rs -81,567.75 |
| Final equity | Rs 1,303,012.65 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 41 | Rs 223,102.50 | 73.2% |
| 2021 | 48 | Rs 290,977.50 | 79.2% |
| 2022 | 42 | Rs 115,502.50 | 69.0% |
| 2023 | 29 | Rs 17,142.50 | 58.6% |
| 2024 | 40 | Rs 97,988.75 | 72.5% |
| 2025 | 31 | Rs 153,132.00 | 80.6% |
| 2026 | 14 | Rs 105,166.90 | 64.3% |

## Skips

| Reason | Count |
|---|---:|
| `balance_check_failed` | 82 |
| `missing_entry_bar` | 3 |
| `no_spot_at_entry` | 3 |
| `missing_atm_contract` | 1 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 27953).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_expiry_otm_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_expiry_otm_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_expiry_otm_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_expiry_otm.log`
