# Weekly Short Strangle — Nifty + Sensex (2024–2026) Backtest

## Strategy Details

- **Structure**: Short strangle — sell CE and PE independently each day
- **Nifty offset**: 200 points from spot (rounded to nearest 50)
- **Sensex offset**: 600 points from spot (rounded to nearest 100)
- **Entry**: 09:30 open candle
- **Exit**: 15:20 open candle, or 2× stop-loss per leg (whichever first)
- **Stop-loss multiple**: 2.0×
- **Lots**: 1 per side
- **Slippage**: 1.00 pt per order (2.00 pts round-trip per leg)
- **Brokerage**: Rs 25.00 per order, Rs 100.00 per day (4 orders: 2 entries + 2 exits)
- **Scheduling**: Closest upcoming expiry wins; tie → continue current index; switch index after each expiry day
- **Nifty spot**: 15m file, 09:15 bar open (rounded to nearest 50)
- **Sensex spot**: Synthetic — strike where CE ≈ PE at entry time (≥80% ratio preferred; min |CE−PE| fallback)
- **Start date**: 2024-10-01
- **Nifty options**: `Options`
- **Sensex options**: `Options`

## Results Summary

- Days processed         : `393`
- Trades executed        : `367`
  - Nifty trades         : `204`
  - Sensex trades        : `163`
- Days skipped           : `26`
- Winning days           : `158`
- Losing days            : `209`
- Days with SL hit       : `206`
- Gross P&L              : `Rs -12253.35`
- Total Brokerage        : `Rs 36700.00`
- **Net P&L**            : **`Rs -48953.35`**
  - Nifty net P&L        : `Rs -42977.75`
  - Sensex net P&L       : `Rs -5975.60`
- Max Drawdown           : `Rs 66566.90`

## Skip Reason Summary

- `sensex_spot_not_found`: 10
- `missing_contract_file`: 9
- `leg_failure`: 6
- `missing_nifty_spot`: 1

## Notes

- The Sensex synthetic spot is the strike with the smallest |CE−PE| price difference at the entry candle, subject to both prices being within 80% of each other. If no strike meets the ratio threshold, the closest pair is used as fallback.
- Missing monitoring candles (common for illiquid Sensex strikes) are skipped; the stop-loss check resumes on the next available candle.
- Nifty lot sizes are expiry-aware: 25 (May–Nov 2024), 75 (Nov 2024–Dec 2025), 65 (Jan 2026+). Sensex lot size is fixed at 10.
- Days where the entry or exit candle is missing from the option file are skipped.