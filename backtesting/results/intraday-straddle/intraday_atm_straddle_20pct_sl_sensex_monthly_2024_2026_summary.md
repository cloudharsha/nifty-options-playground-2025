# SENSEX Intraday ATM Straddle — 20% Independent SL — Monthly Options (2024–2026)

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 100 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `20%` above entry price, **independent per leg**
- Balance rule: skip if |CE − PE| / max(CE, PE) > 20%
- Contract: **monthly expiry** (last expiry of each calendar month)
- Expiry selection: on monthly expiry day → next month; otherwise current month
- Lot size: `10` × `10` lots = **100 quantity** (fixed)
- Slippage: 0.50 pt/order
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Spot data: `SENSEX_INDEX_5m_last_7y.csv`
- Options data: `SensexOptions_2024_2026/Options`

## Overall Results

| Metric | Value |
|--------|-------|
| Traded days | `109` |
| Skipped days | `1612` |
| Winning days | `69` |
| Losing days | `40` |
| Win rate | `63.3%` |
| Days CE SL hit | `58` |
| Days PE SL hit | `53` |
| Days both SL hit | `22` |
| Days neither SL hit | `20` |
| Gross P/L | `₹263745.20` |
| Total Brokerage | `₹10900.00` |
| **Net P/L** | **`₹252845.20`** |
| Peak cumulative profit | `₹357519.20` |
| Max drawdown | `₹112754.00` |
| Best day | `2026-04-01` (Wednesday) `₹36055.00` |
| Worst day | `2026-05-14` (Thursday) `₹-42860.00` |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 26 | 14 | 12 | 18 | 11 | `₹-10624.80` | `₹-408.65` |
| Tuesday | 22 | 17 | 5 | 10 | 11 | `₹134398.00` | `₹6109.00` |
| Wednesday | 21 | 9 | 12 | 10 | 12 | `₹-28998.00` | `₹-1380.86` |
| Thursday | 19 | 14 | 5 | 10 | 7 | `₹115258.00` | `₹6066.21` |
| Friday | 21 | 15 | 6 | 10 | 12 | `₹42812.00` | `₹2038.67` |

### Day-of-Week Detail

#### Monday
- Trades: `26`  Win: `14`  Loss: `12`  CE-SL: `18`  PE-SL: `11`
- Total Net P/L: `₹-10624.80`  **Avg Net/Day: `₹-408.65`**
- Gross: `₹-8024.80`  Brokerage: `₹2600.00`
- Best: `2024-12-23` `₹34830.00`  Worst: `2026-04-20` `₹-32683.00`

#### Tuesday
- Trades: `22`  Win: `17`  Loss: `5`  CE-SL: `10`  PE-SL: `11`
- Total Net P/L: `₹134398.00`  **Avg Net/Day: `₹6109.00`**
- Gross: `₹136598.00`  Brokerage: `₹2200.00`
- Best: `2025-05-13` `₹28535.00`  Worst: `2026-04-28` `₹-18838.00`

#### Wednesday
- Trades: `21`  Win: `9`  Loss: `12`  CE-SL: `10`  PE-SL: `12`
- Total Net P/L: `₹-28998.00`  **Avg Net/Day: `₹-1380.86`**
- Gross: `₹-26898.00`  Brokerage: `₹2100.00`
- Best: `2026-04-01` `₹36055.00`  Worst: `2025-06-18` `₹-21958.00`

#### Thursday
- Trades: `19`  Win: `14`  Loss: `5`  CE-SL: `10`  PE-SL: `7`
- Total Net P/L: `₹115258.00`  **Avg Net/Day: `₹6066.21`**
- Gross: `₹117158.00`  Brokerage: `₹1900.00`
- Best: `2026-02-19` `₹27100.00`  Worst: `2026-05-14` `₹-42860.00`

#### Friday
- Trades: `21`  Win: `15`  Loss: `6`  CE-SL: `10`  PE-SL: `12`
- Total Net P/L: `₹42812.00`  **Avg Net/Day: `₹2038.67`**
- Gross: `₹44912.00`  Brokerage: `₹2100.00`
- Best: `2025-04-25` `₹23622.00`  Worst: `2026-05-15` `₹-40240.00`

## Yearly Summary

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|------|--------|-----|------|---------------|-------------|
| 2024 | 10 | 6 | 4 | `₹20218.20` | `₹2021.82` |
| 2025 | 59 | 38 | 21 | `₹214984.00` | `₹3643.80` |
| 2026 | 40 | 25 | 15 | `₹17643.00` | `₹441.07` |

## Monthly Summary

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|-------|--------|-----|------|---------------|-------------|
| 2024-10 | 3 | 1 | 2 | `₹-16643.00` | `₹-5547.67` |
| 2024-11 | 3 | 3 | 0 | `₹36853.20` | `₹12284.40` |
| 2024-12 | 4 | 2 | 2 | `₹8.00` | `₹2.00` |
| 2025-01 | 5 | 3 | 2 | `₹424.00` | `₹84.80` |
| 2025-02 | 4 | 3 | 1 | `₹21435.00` | `₹5358.75` |
| 2025-03 | 5 | 4 | 1 | `₹23744.00` | `₹4748.80` |
| 2025-04 | 8 | 5 | 3 | `₹55192.00` | `₹6899.00` |
| 2025-05 | 9 | 7 | 2 | `₹96493.00` | `₹10721.44` |
| 2025-06 | 10 | 6 | 4 | `₹42420.00` | `₹4242.00` |
| 2025-07 | 6 | 2 | 4 | `₹-37255.00` | `₹-6209.17` |
| 2025-08 | 4 | 3 | 1 | `₹22428.00` | `₹5607.00` |
| 2025-09 | 2 | 1 | 1 | `₹-5922.00` | `₹-2961.00` |
| 2025-10 | 2 | 1 | 1 | `₹-13759.00` | `₹-6879.50` |
| 2025-11 | 2 | 2 | 0 | `₹9341.00` | `₹4670.50` |
| 2025-12 | 2 | 1 | 1 | `₹443.00` | `₹221.50` |
| 2026-01 | 2 | 1 | 1 | `₹1570.00` | `₹785.00` |
| 2026-02 | 6 | 3 | 3 | `₹-4638.00` | `₹-773.00` |
| 2026-03 | 7 | 6 | 1 | `₹70358.00` | `₹10051.14` |
| 2026-04 | 11 | 8 | 3 | `₹43023.00` | `₹3911.18` |
| 2026-05 | 10 | 6 | 4 | `₹-30195.00` | `₹-3019.50` |
| 2026-06 | 4 | 1 | 3 | `₹-62475.00` | `₹-15618.75` |

## Skip Reason Summary

- `missing_contract_file`: 1212
- `missing_entry_candle`: 260
- `balance_check_failed`: 134
- `missing_spot_entry`: 6
  _(balance check failures: 134)_

## Exceptions (first 30)

- `2019-06-21` (Friday): `missing_contract_file` — Missing: SENSEX_39400_CE_31_OCT_24.csv, SENSEX_39400_PE_31_OCT_24.csv
- `2019-06-24` (Monday): `missing_contract_file` — Missing: SENSEX_39200_CE_31_OCT_24.csv, SENSEX_39200_PE_31_OCT_24.csv
- `2019-06-25` (Tuesday): `missing_contract_file` — Missing: SENSEX_39000_CE_31_OCT_24.csv, SENSEX_39000_PE_31_OCT_24.csv
- `2019-06-26` (Wednesday): `missing_contract_file` — Missing: SENSEX_39400_CE_31_OCT_24.csv, SENSEX_39400_PE_31_OCT_24.csv
- `2019-06-27` (Thursday): `missing_contract_file` — Missing: SENSEX_39700_CE_31_OCT_24.csv, SENSEX_39700_PE_31_OCT_24.csv
- `2019-06-28` (Friday): `missing_contract_file` — Missing: SENSEX_39700_CE_31_OCT_24.csv, SENSEX_39700_PE_31_OCT_24.csv
- `2019-07-01` (Monday): `missing_contract_file` — Missing: SENSEX_39600_CE_31_OCT_24.csv, SENSEX_39600_PE_31_OCT_24.csv
- `2019-07-02` (Tuesday): `missing_contract_file` — Missing: SENSEX_39700_CE_31_OCT_24.csv, SENSEX_39700_PE_31_OCT_24.csv
- `2019-07-03` (Wednesday): `missing_contract_file` — Missing: SENSEX_39700_CE_31_OCT_24.csv, SENSEX_39700_PE_31_OCT_24.csv
- `2019-07-04` (Thursday): `missing_contract_file` — Missing: SENSEX_39900_CE_31_OCT_24.csv, SENSEX_39900_PE_31_OCT_24.csv
- `2019-07-05` (Friday): `missing_contract_file` — Missing: SENSEX_40000_CE_31_OCT_24.csv, SENSEX_40000_PE_31_OCT_24.csv
- `2019-07-08` (Monday): `missing_contract_file` — Missing: SENSEX_39100_CE_31_OCT_24.csv, SENSEX_39100_PE_31_OCT_24.csv
- `2019-07-09` (Tuesday): `missing_contract_file` — Missing: SENSEX_38500_CE_31_OCT_24.csv, SENSEX_38500_PE_31_OCT_24.csv
- `2019-07-10` (Wednesday): `missing_contract_file` — Missing: SENSEX_38800_CE_31_OCT_24.csv, SENSEX_38800_PE_31_OCT_24.csv
- `2019-07-11` (Thursday): `missing_contract_file` — Missing: SENSEX_38700_CE_31_OCT_24.csv, SENSEX_38700_PE_31_OCT_24.csv
- `2019-07-12` (Friday): `missing_contract_file` — Missing: SENSEX_38800_CE_31_OCT_24.csv, SENSEX_38800_PE_31_OCT_24.csv
- `2019-07-15` (Monday): `missing_contract_file` — Missing: SENSEX_38900_CE_31_OCT_24.csv, SENSEX_38900_PE_31_OCT_24.csv
- `2019-07-16` (Tuesday): `missing_contract_file` — Missing: SENSEX_38900_CE_31_OCT_24.csv, SENSEX_38900_PE_31_OCT_24.csv
- `2019-07-17` (Wednesday): `missing_contract_file` — Missing: SENSEX_39200_CE_31_OCT_24.csv, SENSEX_39200_PE_31_OCT_24.csv
- `2019-07-18` (Thursday): `missing_contract_file` — Missing: SENSEX_39200_CE_31_OCT_24.csv, SENSEX_39200_PE_31_OCT_24.csv
- `2019-07-19` (Friday): `missing_contract_file` — Missing: SENSEX_39000_CE_31_OCT_24.csv, SENSEX_39000_PE_31_OCT_24.csv
- `2019-07-22` (Monday): `missing_contract_file` — Missing: SENSEX_38100_CE_31_OCT_24.csv, SENSEX_38100_PE_31_OCT_24.csv
- `2019-07-23` (Tuesday): `missing_contract_file` — Missing: SENSEX_38000_CE_31_OCT_24.csv, SENSEX_38000_PE_31_OCT_24.csv
- `2019-07-24` (Wednesday): `missing_contract_file` — Missing: SENSEX_38100_CE_31_OCT_24.csv, SENSEX_38100_PE_31_OCT_24.csv
- `2019-07-25` (Thursday): `missing_contract_file` — Missing: SENSEX_38000_CE_31_OCT_24.csv, SENSEX_38000_PE_31_OCT_24.csv
- `2019-07-26` (Friday): `missing_contract_file` — Missing: SENSEX_37700_CE_31_OCT_24.csv, SENSEX_37700_PE_31_OCT_24.csv
- `2019-07-29` (Monday): `missing_contract_file` — Missing: SENSEX_37900_CE_31_OCT_24.csv, SENSEX_37900_PE_31_OCT_24.csv
- `2019-07-30` (Tuesday): `missing_contract_file` — Missing: SENSEX_37800_CE_31_OCT_24.csv, SENSEX_37800_PE_31_OCT_24.csv
- `2019-07-31` (Wednesday): `missing_contract_file` — Missing: SENSEX_37300_CE_31_OCT_24.csv, SENSEX_37300_PE_31_OCT_24.csv
- `2019-08-01` (Thursday): `missing_contract_file` — Missing: SENSEX_37300_CE_31_OCT_24.csv, SENSEX_37300_PE_31_OCT_24.csv

## Remarks

- Uses monthly contracts (last expiry of each calendar month).
- Monthly options carry significantly higher premium than weekly options.
- SL is 20% above entry price per leg; each leg exits independently.
- SL monitoring uses the option contract's 1-minute candles.
- Balance check: skip if min(CE,PE)/max(CE,PE) < 0.80 at entry.
- Sensex lot size is fixed at 10 throughout the dataset.
- Strike interval: 100 points (nearest 100 to spot open).
