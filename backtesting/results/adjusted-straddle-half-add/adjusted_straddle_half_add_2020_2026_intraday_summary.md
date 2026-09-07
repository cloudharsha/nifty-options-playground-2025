# Adjusted ATM Straddle — Half-Trigger / 25% Add — NIFTY Weekly (INTRADAY)

## Strategy

- Mode: Intraday — enter 09:20, close all legs 15:20 same session.
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

- Period: `2020-01-06` to `2026-06-16` (6.44 years)
- Cycles traded: `893` (skipped `713`)
- Total adds: `1246`, total unwinds: `698`
- Orders executed: `6064`
- Max legs open at once: `4`

| Metric | Value |
|---|---:|
| Gross P/L | Rs 248,404.75 |
| Costs | Rs 181,920.00 |
| **Net P/L** | **Rs 66,484.75** |
| CAGR | 3.16% |
| Max drawdown | Rs 127,548.00 |
| Win rate | 60.47% (540W / 353L) |
| Profit factor | 1.09 |
| Best cycle | Rs 14,100.00 |
| Worst cycle | Rs -20,752.50 |
| Final equity | Rs 366,484.75 |

## Yearly

| Year | Cycles | Net P/L | Win % |
|---|---:|---:|---:|
| 2020 | 123 | Rs 63,498.75 | 68.3% |
| 2021 | 153 | Rs 33,057.50 | 64.7% |
| 2022 | 154 | Rs 4,585.00 | 62.3% |
| 2023 | 96 | Rs -37,355.00 | 47.9% |
| 2024 | 147 | Rs -55,388.75 | 59.9% |
| 2025 | 143 | Rs 76,971.75 | 60.8% |
| 2026 | 77 | Rs -18,884.50 | 51.9% |

## Skips

| Reason | Count |
|---|---:|
| `balance_check_failed` | 427 |
| `missing_entry_bar` | 277 |
| `no_spot_at_entry` | 6 |
| `missing_atm_contract` | 3 |

## Notes

- Options data: `NiftyOptions_2020_2026/Options` (1-minute bars). Spot for ATM: 5-minute index file.
- Leg prices use the last traded bar at or before the check minute; `stale_prices` in the cycle CSV counts how often a carried-forward bar was used (total 2206).
- Candidate strikes for an add must have an exact bar at the check minute, so illiquid strikes are never selected on a stale quote.
- Weekly expiry is taken from the options folder structure (Thursday to Aug 2025, Tuesday from Sep 2025, holiday-shifted).
- Intraday mode rolls to the next weekly on expiry day to avoid same-day-expiry pin behaviour.

## Files

- Cycles: `adjusted_straddle_half_add_2020_2026_intraday_cycles.csv`
- Legs: `adjusted_straddle_half_add_2020_2026_intraday_legs.csv`
- Equity: `adjusted_straddle_half_add_2020_2026_intraday_equity.csv`
- Log: `adjusted_straddle_half_add_2020_2026_intraday.log`
