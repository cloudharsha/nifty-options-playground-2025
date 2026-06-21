# SENSEX Intraday ATM Straddle — 20% Independent SL (2024–2026)

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 100 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `20%` above entry price, **independent per leg**
- Balance rule: skip if |CE − PE| / max(CE, PE) > 20%
  (e.g. CE=100 → PE must be in [80, 120])
- Expiry: current week; on expiry day → next week
- Lot size: `10` × `10` lots = **100 quantity** (fixed)
- Slippage: 0.50 pt/order (2 × per leg)
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Spot data: `SENSEX_INDEX_5m_last_7y.csv` (5-minute candles)
- Options data: `SensexOptions_2024_2026/Options` (1-minute candles)

## Overall Results

| Metric | Value |
|--------|-------|
| Traded days | `246` |
| Skipped days | `1475` |
| Winning days | `134` |
| Losing days | `112` |
| Win rate | `54.5%` |
| Days CE SL hit | `150` |
| Days PE SL hit | `158` |
| Days both SL hit | `82` |
| Days neither SL hit | `20` |
| Gross P/L | `₹169362.40` |
| Total Brokerage | `₹24600.00` |
| **Net P/L** | **`₹144762.40`** |
| Peak cumulative profit | `₹247039.40` |
| Max drawdown | `₹172031.00` |
| Best day | `2024-09-23` (Monday) `₹80190.00` |
| Worst day | `2025-01-29` (Wednesday) `₹-38087.00` |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 52 | 25 | 27 | 37 | 35 | `₹-9721.40` | `₹-186.95` |
| Tuesday | 53 | 34 | 19 | 26 | 36 | `₹189311.20` | `₹3571.91` |
| Wednesday | 53 | 25 | 28 | 36 | 30 | `₹-107975.60` | `₹-2037.28` |
| Thursday | 46 | 24 | 22 | 29 | 28 | `₹-23435.80` | `₹-509.47` |
| Friday | 42 | 26 | 16 | 22 | 29 | `₹96584.00` | `₹2299.62` |

### Day-of-Week Detail

#### Monday
- Trades: `52`  Win: `25`  Loss: `27`  CE-SL: `37`  PE-SL: `35`
- Total Net P/L: `₹-9721.40`  **Avg Net/Day: `₹-186.95`**
- Gross: `₹-4521.40`  Brokerage: `₹5200.00`
- Best: `2024-09-23` `₹80190.00`  Worst: `2026-03-02` `₹-26535.00`

#### Tuesday
- Trades: `53`  Win: `34`  Loss: `19`  CE-SL: `26`  PE-SL: `36`
- Total Net P/L: `₹189311.20`  **Avg Net/Day: `₹3571.91`**
- Gross: `₹194611.20`  Brokerage: `₹5300.00`
- Best: `2025-04-15` `₹34765.00`  Worst: `2025-05-27` `₹-36993.00`

#### Wednesday
- Trades: `53`  Win: `25`  Loss: `28`  CE-SL: `36`  PE-SL: `30`
- Total Net P/L: `₹-107975.60`  **Avg Net/Day: `₹-2037.28`**
- Gross: `₹-102675.60`  Brokerage: `₹5300.00`
- Best: `2025-05-28` `₹33655.00`  Worst: `2025-01-29` `₹-38087.00`

#### Thursday
- Trades: `46`  Win: `24`  Loss: `22`  CE-SL: `29`  PE-SL: `28`
- Total Net P/L: `₹-23435.80`  **Avg Net/Day: `₹-509.47`**
- Gross: `₹-18835.80`  Brokerage: `₹4600.00`
- Best: `2025-01-02` `₹37460.00`  Worst: `2026-05-14` `₹-32050.00`

#### Friday
- Trades: `42`  Win: `26`  Loss: `16`  CE-SL: `22`  PE-SL: `29`
- Total Net P/L: `₹96584.00`  **Avg Net/Day: `₹2299.62`**
- Gross: `₹100784.00`  Brokerage: `₹4200.00`
- Best: `2024-12-06` `₹39770.00`  Worst: `2024-12-20` `₹-30337.00`

## Yearly Summary

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|------|--------|-----|------|---------------|-------------|
| 2024 | 46 | 25 | 21 | `₹75383.20` | `₹1638.77` |
| 2025 | 146 | 78 | 68 | `₹59124.20` | `₹404.96` |
| 2026 | 54 | 31 | 23 | `₹10255.00` | `₹189.91` |

## Monthly Summary

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|-------|--------|-----|------|---------------|-------------|
| 2024-09 | 2 | 2 | 0 | `₹97290.00` | `₹48645.00` |
| 2024-10 | 12 | 6 | 6 | `₹5274.20` | `₹439.52` |
| 2024-11 | 14 | 11 | 3 | `₹88989.40` | `₹6356.39` |
| 2024-12 | 18 | 6 | 12 | `₹-116170.40` | `₹-6453.91` |
| 2025-01 | 21 | 10 | 11 | `₹-9082.00` | `₹-432.48` |
| 2025-02 | 9 | 7 | 2 | `₹55631.00` | `₹6181.22` |
| 2025-03 | 9 | 5 | 4 | `₹5255.20` | `₹583.91` |
| 2025-04 | 15 | 7 | 8 | `₹-5286.00` | `₹-352.40` |
| 2025-05 | 19 | 11 | 8 | `₹26287.00` | `₹1383.53` |
| 2025-06 | 20 | 12 | 8 | `₹64576.00` | `₹3228.80` |
| 2025-07 | 14 | 6 | 8 | `₹-19992.00` | `₹-1428.00` |
| 2025-08 | 12 | 6 | 6 | `₹-14433.00` | `₹-1202.75` |
| 2025-09 | 7 | 4 | 3 | `₹-835.00` | `₹-119.29` |
| 2025-10 | 4 | 1 | 3 | `₹-29426.00` | `₹-7356.50` |
| 2025-11 | 6 | 4 | 2 | `₹9673.00` | `₹1612.17` |
| 2025-12 | 10 | 5 | 5 | `₹-23244.00` | `₹-2324.40` |
| 2026-01 | 10 | 4 | 6 | `₹-59499.00` | `₹-5949.90` |
| 2026-02 | 14 | 9 | 5 | `₹67214.00` | `₹4801.00` |
| 2026-03 | 7 | 6 | 1 | `₹48181.00` | `₹6883.00` |
| 2026-04 | 7 | 5 | 2 | `₹5496.00` | `₹785.14` |
| 2026-05 | 9 | 4 | 5 | `₹-41347.00` | `₹-4594.11` |
| 2026-06 | 7 | 3 | 4 | `₹-9790.00` | `₹-1398.57` |

## Skip Reason Summary

- `missing_contract_file`: 1227
- `balance_check_failed`: 130
- `missing_entry_candle`: 112
- `missing_spot_entry`: 6
  _(balance check failures counted above: 130)_

## Exceptions (first 30)

- `2019-06-21` (Friday): `missing_contract_file` — Missing: SENSEX_39400_CE_04_OCT_24.csv, SENSEX_39400_PE_04_OCT_24.csv
- `2019-06-24` (Monday): `missing_contract_file` — Missing: SENSEX_39200_CE_04_OCT_24.csv, SENSEX_39200_PE_04_OCT_24.csv
- `2019-06-25` (Tuesday): `missing_contract_file` — Missing: SENSEX_39000_CE_04_OCT_24.csv, SENSEX_39000_PE_04_OCT_24.csv
- `2019-06-26` (Wednesday): `missing_contract_file` — Missing: SENSEX_39400_CE_04_OCT_24.csv, SENSEX_39400_PE_04_OCT_24.csv
- `2019-06-27` (Thursday): `missing_contract_file` — Missing: SENSEX_39700_CE_04_OCT_24.csv, SENSEX_39700_PE_04_OCT_24.csv
- `2019-06-28` (Friday): `missing_contract_file` — Missing: SENSEX_39700_CE_04_OCT_24.csv, SENSEX_39700_PE_04_OCT_24.csv
- `2019-07-01` (Monday): `missing_contract_file` — Missing: SENSEX_39600_CE_04_OCT_24.csv, SENSEX_39600_PE_04_OCT_24.csv
- `2019-07-02` (Tuesday): `missing_contract_file` — Missing: SENSEX_39700_CE_04_OCT_24.csv, SENSEX_39700_PE_04_OCT_24.csv
- `2019-07-03` (Wednesday): `missing_contract_file` — Missing: SENSEX_39700_CE_04_OCT_24.csv, SENSEX_39700_PE_04_OCT_24.csv
- `2019-07-04` (Thursday): `missing_contract_file` — Missing: SENSEX_39900_CE_04_OCT_24.csv, SENSEX_39900_PE_04_OCT_24.csv
- `2019-07-05` (Friday): `missing_contract_file` — Missing: SENSEX_40000_CE_04_OCT_24.csv, SENSEX_40000_PE_04_OCT_24.csv
- `2019-07-08` (Monday): `missing_contract_file` — Missing: SENSEX_39100_CE_04_OCT_24.csv, SENSEX_39100_PE_04_OCT_24.csv
- `2019-07-09` (Tuesday): `missing_contract_file` — Missing: SENSEX_38500_CE_04_OCT_24.csv, SENSEX_38500_PE_04_OCT_24.csv
- `2019-07-10` (Wednesday): `missing_contract_file` — Missing: SENSEX_38800_CE_04_OCT_24.csv, SENSEX_38800_PE_04_OCT_24.csv
- `2019-07-11` (Thursday): `missing_contract_file` — Missing: SENSEX_38700_CE_04_OCT_24.csv, SENSEX_38700_PE_04_OCT_24.csv
- `2019-07-12` (Friday): `missing_contract_file` — Missing: SENSEX_38800_CE_04_OCT_24.csv, SENSEX_38800_PE_04_OCT_24.csv
- `2019-07-15` (Monday): `missing_contract_file` — Missing: SENSEX_38900_CE_04_OCT_24.csv, SENSEX_38900_PE_04_OCT_24.csv
- `2019-07-16` (Tuesday): `missing_contract_file` — Missing: SENSEX_38900_CE_04_OCT_24.csv, SENSEX_38900_PE_04_OCT_24.csv
- `2019-07-17` (Wednesday): `missing_contract_file` — Missing: SENSEX_39200_CE_04_OCT_24.csv, SENSEX_39200_PE_04_OCT_24.csv
- `2019-07-18` (Thursday): `missing_contract_file` — Missing: SENSEX_39200_CE_04_OCT_24.csv, SENSEX_39200_PE_04_OCT_24.csv
- `2019-07-19` (Friday): `missing_contract_file` — Missing: SENSEX_39000_CE_04_OCT_24.csv, SENSEX_39000_PE_04_OCT_24.csv
- `2019-07-22` (Monday): `missing_contract_file` — Missing: SENSEX_38100_CE_04_OCT_24.csv, SENSEX_38100_PE_04_OCT_24.csv
- `2019-07-23` (Tuesday): `missing_contract_file` — Missing: SENSEX_38000_CE_04_OCT_24.csv, SENSEX_38000_PE_04_OCT_24.csv
- `2019-07-24` (Wednesday): `missing_contract_file` — Missing: SENSEX_38100_CE_04_OCT_24.csv, SENSEX_38100_PE_04_OCT_24.csv
- `2019-07-25` (Thursday): `missing_contract_file` — Missing: SENSEX_38000_CE_04_OCT_24.csv, SENSEX_38000_PE_04_OCT_24.csv
- `2019-07-26` (Friday): `missing_contract_file` — Missing: SENSEX_37700_CE_04_OCT_24.csv, SENSEX_37700_PE_04_OCT_24.csv
- `2019-07-29` (Monday): `missing_contract_file` — Missing: SENSEX_37900_CE_04_OCT_24.csv, SENSEX_37900_PE_04_OCT_24.csv
- `2019-07-30` (Tuesday): `missing_contract_file` — Missing: SENSEX_37800_CE_04_OCT_24.csv, SENSEX_37800_PE_04_OCT_24.csv
- `2019-07-31` (Wednesday): `missing_contract_file` — Missing: SENSEX_37300_CE_04_OCT_24.csv, SENSEX_37300_PE_04_OCT_24.csv
- `2019-08-01` (Thursday): `missing_contract_file` — Missing: SENSEX_37300_CE_04_OCT_24.csv, SENSEX_37300_PE_04_OCT_24.csv

## Remarks

- SL is 20% above entry price per leg. Each leg is managed independently.
- Gap SL: if option opens ≥ SL price, fill at candle open.
- Intrabar SL: if high ≥ SL price, fill at SL price.
- SL monitoring uses the option contract's 1-minute candles.
- Balance check: if min(CE,PE)/max(CE,PE) < 0.80, the day is skipped.
- Sensex lot size is fixed at 10 throughout the dataset.
- Early data (Oct–Dec 2024) may have many skips due to low Sensex options liquidity.
- Strike interval: 100 points (nearest 100 to spot open).
