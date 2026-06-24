# NIFTY Weekly Iron Condor — Expiry Day Intraday (2020–2026)

## Strategy Details

- Structure: short CE/PE @ ATM ± 200pts, long wings ± 300pts
- Entry: `09:20` open on weekly expiry day
- Exit: `15:25` or SL trigger
- SL: liq cost ≥ `2.0×` entry credit (locks in 1× credit loss at 2×)
- Sizing: floor(₹1,000,000 / margin_per_condor); margin = wing×lot + 2×2%×spot×lot
- Brokerage: ₹20/order × 8 orders (4 legs × entry+exit)
- Slippage: 0.5 pt/order × 8 orders × units
- Capital reference (CAGR): ₹1,000,000
- Data range: `2020-01-02` to `2026-06-16`

## Results Summary

| Metric | Value |
|--------|-------|
| Total expiry days | `351` |
| Traded days | `328` |
| Skipped days | `23` |
| Win days | `86` |
| Loss days | `242` |
| Win rate | `26.2%` |
| EOD exits | `207` |
| SL hits | `121` |
| Avg entry credit | `8.20` pts |
| Avg condors/day | `21.6` |
| Avg net P/L/day | `₹-6785.29` |
| Best day | `2025-04-09` ₹36052.25 |
| Worst day | `2020-03-26` ₹-112125.00 |
| Max consec wins | `7` |
| Max consec losses | `40` |
| Max drawdown | `₹2255596.00` |
| Gross P/L | `₹486045.50` |
| Total brokerage + slippage | `₹2711620.00` |
| **Net P/L** | **`₹-2225574.50`** |
| **CAGR (on ₹1,000,000)** | **`-100.00%`** |

## Yearly Summary

| Year | Expiry Days | Wins | Losses | Win% | Net P/L |
|------|------------|------|--------|------|---------|
| 2020 | 51 | 5 | 46 | 9.8% | ₹-569671.25 |
| 2021 | 51 | 8 | 43 | 15.7% | ₹-436113.75 |
| 2022 | 52 | 12 | 40 | 23.1% | ₹-400382.50 |
| 2023 | 52 | 3 | 49 | 5.8% | ₹-424427.50 |
| 2024 | 52 | 24 | 28 | 46.2% | ₹-297141.25 |
| 2025 | 53 | 26 | 27 | 49.1% | ₹-73286.75 |
| 2026 | 17 | 8 | 9 | 47.1% | ₹-24551.50 |

## Skip Reason Summary

- `no_spot_data_for_expiry`: 17
- `missing_entry_candle`: 6

## Remarks

- SL is checked bar-by-bar using close prices of all 4 legs.
- Entry uses the open price of the 09:20 candle.
- Exit uses close price of the bar at or before the exit time.
- Lot sizing is dynamic per NIFTY lot schedule (75/50/25/75/65).
- Short distance: 200 pts each side; wing: 100 pts.
