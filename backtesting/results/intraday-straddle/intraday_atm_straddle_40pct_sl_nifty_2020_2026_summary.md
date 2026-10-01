# NIFTY Intraday ATM Straddle — 40% Independent SL (2020–2026)

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `40%` above entry price, **independent per leg**
- Balance rule: skip if |CE − PE| / max(CE, PE) > 20%
  (e.g. CE=100 → PE must be in [80, 120])
- Expiry: current week; on expiry day → next week
- Lot sizing (expiry-aware, targeting ~300 quantity):
  - Until 2021-10-06 expiry  : 75 × 4 = **300**
  - 2021-10-07 – 2024-04-25  : 50 × 6 = **300**
  - 2024-04-26 – 2024-11-21  : 25 × 12 = **300**
  - 2024-11-22 – 2025-12-30  : 75 × 4 = **300**
  - 2026+ expiry              : 65 × 5 = **325**
- Slippage: 0.50 pt/order (2 × per leg, applied to points P&L)
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Spot data: `NIFTY50_INDEX_5m_last_7y.csv` (5-minute candles)
- Options data: `NiftyOptions_2020_2026/Options` (1-minute candles)

## Overall Results

| Metric | Value |
|--------|-------|
| Traded days | `888` |
| Skipped days | `838` |
| Winning days | `558` |
| Losing days | `330` |
| Win rate | `62.8%` |
| Days CE SL hit | `343` |
| Days PE SL hit | `381` |
| Days both SL hit | `73` |
| Days neither SL hit | `237` |
| Gross P/L | `₹239063.05` |
| Total Brokerage | `₹88800.00` |
| **Net P/L** | **`₹150263.05`** |
| Peak cumulative profit | `₹493168.00` |
| Max drawdown | `₹352538.70` |
| Best day | `2025-05-28` (Wednesday) `₹51905.00` qty=300 |
| Worst day | `2026-06-03` (Wednesday) `₹-52698.00` qty=325 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 211 | 128 | 83 | 77 | 91 | `₹75615.15` | `₹358.37` |
| Tuesday | 211 | 131 | 80 | 86 | 95 | `₹-63311.30` | `₹-300.05` |
| Wednesday | 194 | 119 | 75 | 102 | 99 | `₹-71037.30` | `₹-366.17` |
| Thursday | 37 | 17 | 20 | 16 | 9 | `₹-95067.75` | `₹-2569.40` |
| Friday | 235 | 163 | 72 | 62 | 87 | `₹304064.25` | `₹1293.89` |

### Day-of-Week Detail

#### Monday
- Trades: `211`  Win: `128`  Loss: `83`  CE-SL: `77`  PE-SL: `91`
- Total Net P/L: `₹75615.15`  **Avg Net/Day: `₹358.37`**
- Gross: `₹96715.15`  Brokerage: `₹21100.00`
- Best: `2020-03-30` `₹44330.00`  Worst: `2024-02-05` `₹-37888.00`

#### Tuesday
- Trades: `211`  Win: `131`  Loss: `80`  CE-SL: `86`  PE-SL: `95`
- Total Net P/L: `₹-63311.30`  **Avg Net/Day: `₹-300.05`**
- Gross: `₹-42211.30`  Brokerage: `₹21100.00`
- Best: `2024-06-04` `₹37202.00`  Worst: `2025-05-27` `₹-51754.00`

#### Wednesday
- Trades: `194`  Win: `119`  Loss: `75`  CE-SL: `102`  PE-SL: `99`
- Total Net P/L: `₹-71037.30`  **Avg Net/Day: `₹-366.17`**
- Gross: `₹-51637.30`  Brokerage: `₹19400.00`
- Best: `2025-05-28` `₹51905.00`  Worst: `2026-06-03` `₹-52698.00`

#### Thursday
- Trades: `37`  Win: `17`  Loss: `20`  CE-SL: `16`  PE-SL: `9`
- Total Net P/L: `₹-95067.75`  **Avg Net/Day: `₹-2569.40`**
- Gross: `₹-91367.75`  Brokerage: `₹3700.00`
- Best: `2025-01-02` `₹19604.00`  Worst: `2026-04-30` `₹-48382.00`

#### Friday
- Trades: `235`  Win: `163`  Loss: `72`  CE-SL: `62`  PE-SL: `87`
- Total Net P/L: `₹304064.25`  **Avg Net/Day: `₹1293.89`**
- Gross: `₹327564.25`  Brokerage: `₹23500.00`
- Best: `2024-12-06` `₹32675.00`  Worst: `2024-12-20` `₹-49582.00`

## Yearly Summary

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|------|--------|-----|------|---------------|-------------|
| 2020 | 122 | 69 | 53 | `₹26887.00` | `₹220.39` |
| 2021 | 153 | 107 | 46 | `₹256959.00` | `₹1679.47` |
| 2022 | 154 | 103 | 51 | `₹165374.00` | `₹1073.86` |
| 2023 | 96 | 63 | 33 | `₹-27846.00` | `₹-290.06` |
| 2024 | 145 | 85 | 60 | `₹-208379.80` | `₹-1437.10` |
| 2025 | 142 | 92 | 50 | `₹159755.60` | `₹1125.04` |
| 2026 | 76 | 39 | 37 | `₹-222486.75` | `₹-2927.46` |

## Monthly Summary

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|-------|--------|-----|------|---------------|-------------|
| 2020-01 | 7 | 3 | 4 | `₹-15442.00` | `₹-2206.00` |
| 2020-02 | 7 | 5 | 2 | `₹4652.00` | `₹664.57` |
| 2020-03 | 11 | 5 | 6 | `₹46348.00` | `₹4213.45` |
| 2020-04 | 11 | 6 | 5 | `₹5527.00` | `₹502.45` |
| 2020-05 | 10 | 7 | 3 | `₹22457.00` | `₹2245.70` |
| 2020-06 | 10 | 7 | 3 | `₹42098.00` | `₹4209.80` |
| 2020-07 | 8 | 4 | 4 | `₹5473.00` | `₹684.12` |
| 2020-08 | 12 | 7 | 5 | `₹18483.00` | `₹1540.25` |
| 2020-09 | 11 | 8 | 3 | `₹14656.00` | `₹1332.36` |
| 2020-10 | 10 | 5 | 5 | `₹-18976.00` | `₹-1897.60` |
| 2020-11 | 13 | 6 | 7 | `₹-58750.00` | `₹-4519.23` |
| 2020-12 | 12 | 6 | 6 | `₹-39639.00` | `₹-3303.25` |
| 2021-01 | 13 | 11 | 2 | `₹40136.00` | `₹3087.38` |
| 2021-02 | 12 | 6 | 6 | `₹-15930.00` | `₹-1327.50` |
| 2021-03 | 15 | 13 | 2 | `₹138405.00` | `₹9227.00` |
| 2021-04 | 13 | 13 | 0 | `₹100442.00` | `₹7726.31` |
| 2021-05 | 11 | 9 | 2 | `₹37018.00` | `₹3365.27` |
| 2021-06 | 13 | 7 | 6 | `₹-27538.00` | `₹-2118.31` |
| 2021-07 | 10 | 7 | 3 | `₹11312.00` | `₹1131.20` |
| 2021-08 | 11 | 4 | 7 | `₹-12875.00` | `₹-1170.45` |
| 2021-09 | 13 | 9 | 4 | `₹-52918.00` | `₹-4070.62` |
| 2021-10 | 13 | 9 | 4 | `₹22838.00` | `₹1756.77` |
| 2021-11 | 12 | 7 | 5 | `₹-49500.00` | `₹-4125.00` |
| 2021-12 | 17 | 12 | 5 | `₹65569.00` | `₹3857.00` |
| 2022-01 | 15 | 10 | 5 | `₹24915.00` | `₹1661.00` |
| 2022-02 | 15 | 10 | 5 | `₹14613.00` | `₹974.20` |
| 2022-03 | 13 | 8 | 5 | `₹31004.00` | `₹2384.92` |
| 2022-04 | 14 | 12 | 2 | `₹71152.00` | `₹5082.29` |
| 2022-05 | 14 | 11 | 3 | `₹37222.00` | `₹2658.71` |
| 2022-06 | 14 | 8 | 6 | `₹-35486.00` | `₹-2534.71` |
| 2022-07 | 14 | 10 | 4 | `₹-14549.00` | `₹-1039.21` |
| 2022-08 | 14 | 9 | 5 | `₹12589.00` | `₹899.21` |
| 2022-09 | 16 | 9 | 7 | `₹21113.00` | `₹1319.56` |
| 2022-10 | 13 | 12 | 1 | `₹41282.00` | `₹3175.54` |
| 2022-11 | 7 | 2 | 5 | `₹-13609.00` | `₹-1944.14` |
| 2022-12 | 5 | 2 | 3 | `₹-24872.00` | `₹-4974.40` |
| 2023-01 | 6 | 5 | 1 | `₹7197.00` | `₹1199.50` |
| 2023-02 | 10 | 7 | 3 | `₹-42658.00` | `₹-4265.80` |
| 2023-03 | 12 | 8 | 4 | `₹23064.00` | `₹1922.00` |
| 2023-04 | 9 | 7 | 2 | `₹-2808.00` | `₹-312.00` |
| 2023-05 | 6 | 4 | 2 | `₹-2088.00` | `₹-348.00` |
| 2023-06 | 4 | 3 | 1 | `₹977.00` | `₹244.25` |
| 2023-07 | 7 | 3 | 4 | `₹-17032.00` | `₹-2433.14` |
| 2023-08 | 11 | 8 | 3 | `₹22714.00` | `₹2064.91` |
| 2023-09 | 8 | 6 | 2 | `₹10828.00` | `₹1353.50` |
| 2023-10 | 12 | 6 | 6 | `₹-13851.00` | `₹-1154.25` |
| 2023-11 | 6 | 3 | 3 | `₹-3057.00` | `₹-509.50` |
| 2023-12 | 5 | 3 | 2 | `₹-11132.00` | `₹-2226.40` |
| 2024-01 | 14 | 9 | 5 | `₹35776.00` | `₹2555.43` |
| 2024-02 | 14 | 9 | 5 | `₹-25052.00` | `₹-1789.43` |
| 2024-03 | 7 | 2 | 5 | `₹-26443.00` | `₹-3777.57` |
| 2024-04 | 12 | 7 | 5 | `₹-2841.00` | `₹-236.75` |
| 2024-05 | 6 | 3 | 3 | `₹-26970.00` | `₹-4495.00` |
| 2024-06 | 13 | 10 | 3 | `₹54452.00` | `₹4188.62` |
| 2024-07 | 15 | 8 | 7 | `₹513.00` | `₹34.20` |
| 2024-08 | 12 | 7 | 5 | `₹-50178.00` | `₹-4181.50` |
| 2024-09 | 13 | 10 | 3 | `₹2942.00` | `₹226.31` |
| 2024-10 | 14 | 9 | 5 | `₹-29639.00` | `₹-2117.07` |
| 2024-11 | 12 | 5 | 7 | `₹-34413.00` | `₹-2867.75` |
| 2024-12 | 13 | 6 | 7 | `₹-106526.80` | `₹-8194.37` |
| 2025-01 | 21 | 15 | 6 | `₹28997.40` | `₹1380.83` |
| 2025-02 | 11 | 9 | 2 | `₹56248.00` | `₹5113.45` |
| 2025-03 | 10 | 5 | 5 | `₹-52339.00` | `₹-5233.90` |
| 2025-04 | 15 | 11 | 4 | `₹51955.20` | `₹3463.68` |
| 2025-05 | 20 | 11 | 9 | `₹11275.00` | `₹563.75` |
| 2025-06 | 17 | 13 | 4 | `₹37120.00` | `₹2183.53` |
| 2025-07 | 17 | 8 | 9 | `₹-18140.00` | `₹-1067.06` |
| 2025-08 | 11 | 9 | 2 | `₹42919.00` | `₹3901.73` |
| 2025-09 | 5 | 2 | 3 | `₹1024.00` | `₹204.80` |
| 2025-10 | 2 | 2 | 0 | `₹3916.00` | `₹1958.00` |
| 2025-11 | 6 | 3 | 3 | `₹-6666.00` | `₹-1111.00` |
| 2025-12 | 7 | 4 | 3 | `₹3446.00` | `₹492.29` |
| 2026-01 | 10 | 5 | 5 | `₹-12459.50` | `₹-1245.95` |
| 2026-02 | 12 | 5 | 7 | `₹-57451.00` | `₹-4787.58` |
| 2026-03 | 17 | 8 | 9 | `₹-33579.25` | `₹-1975.25` |
| 2026-04 | 17 | 8 | 9 | `₹-69283.75` | `₹-4075.51` |
| 2026-05 | 11 | 8 | 3 | `₹18799.75` | `₹1709.07` |
| 2026-06 | 9 | 5 | 4 | `₹-68513.00` | `₹-7612.56` |

## Skip Reason Summary

- `balance_check_failed`: 426
- `missing_entry_candle`: 365
- `missing_contract_file`: 43
- `missing_spot_entry`: 4
  _(balance check failures counted above: 426)_

## Exceptions (first 30)

- `2019-06-21` (Friday): `missing_entry_candle` — No 2019-06-21T09:20:00+05:30 candle in: NIFTY_11800_CE_02_JAN_20.csv, NIFTY_11800_PE_02_JAN_20.csv
- `2019-06-24` (Monday): `missing_entry_candle` — No 2019-06-24T09:20:00+05:30 candle in: NIFTY_11750_CE_02_JAN_20.csv, NIFTY_11750_PE_02_JAN_20.csv
- `2019-06-25` (Tuesday): `missing_contract_file` — Missing: NIFTY_11650_CE_02_JAN_20.csv
- `2019-06-26` (Wednesday): `missing_entry_candle` — No 2019-06-26T09:20:00+05:30 candle in: NIFTY_11800_CE_02_JAN_20.csv, NIFTY_11800_PE_02_JAN_20.csv
- `2019-06-27` (Thursday): `missing_entry_candle` — No 2019-06-27T09:20:00+05:30 candle in: NIFTY_11900_CE_02_JAN_20.csv, NIFTY_11900_PE_02_JAN_20.csv
- `2019-06-28` (Friday): `missing_entry_candle` — No 2019-06-28T09:20:00+05:30 candle in: NIFTY_11850_CE_02_JAN_20.csv, NIFTY_11850_PE_02_JAN_20.csv
- `2019-07-01` (Monday): `missing_entry_candle` — No 2019-07-01T09:20:00+05:30 candle in: NIFTY_11850_CE_02_JAN_20.csv, NIFTY_11850_PE_02_JAN_20.csv
- `2019-07-02` (Tuesday): `missing_entry_candle` — No 2019-07-02T09:20:00+05:30 candle in: NIFTY_11900_CE_02_JAN_20.csv, NIFTY_11900_PE_02_JAN_20.csv
- `2019-07-03` (Wednesday): `missing_entry_candle` — No 2019-07-03T09:20:00+05:30 candle in: NIFTY_11900_CE_02_JAN_20.csv, NIFTY_11900_PE_02_JAN_20.csv
- `2019-07-04` (Thursday): `missing_entry_candle` — No 2019-07-04T09:20:00+05:30 candle in: NIFTY_11950_CE_02_JAN_20.csv, NIFTY_11950_PE_02_JAN_20.csv
- `2019-07-05` (Friday): `missing_entry_candle` — No 2019-07-05T09:20:00+05:30 candle in: NIFTY_11950_CE_02_JAN_20.csv, NIFTY_11950_PE_02_JAN_20.csv
- `2019-07-08` (Monday): `missing_entry_candle` — No 2019-07-08T09:20:00+05:30 candle in: NIFTY_11700_CE_02_JAN_20.csv, NIFTY_11700_PE_02_JAN_20.csv
- `2019-07-09` (Tuesday): `missing_entry_candle` — No 2019-07-09T09:20:00+05:30 candle in: NIFTY_11500_CE_02_JAN_20.csv, NIFTY_11500_PE_02_JAN_20.csv
- `2019-07-10` (Wednesday): `missing_contract_file` — Missing: NIFTY_11550_CE_02_JAN_20.csv
- `2019-07-11` (Thursday): `missing_contract_file` — Missing: NIFTY_11550_CE_02_JAN_20.csv
- `2019-07-12` (Friday): `missing_entry_candle` — No 2019-07-12T09:20:00+05:30 candle in: NIFTY_11600_CE_02_JAN_20.csv, NIFTY_11600_PE_02_JAN_20.csv
- `2019-07-15` (Monday): `missing_entry_candle` — No 2019-07-15T09:20:00+05:30 candle in: NIFTY_11600_CE_02_JAN_20.csv, NIFTY_11600_PE_02_JAN_20.csv
- `2019-07-16` (Tuesday): `missing_entry_candle` — No 2019-07-16T09:20:00+05:30 candle in: NIFTY_11600_CE_02_JAN_20.csv, NIFTY_11600_PE_02_JAN_20.csv
- `2019-07-17` (Wednesday): `missing_entry_candle` — No 2019-07-17T09:20:00+05:30 candle in: NIFTY_11700_CE_02_JAN_20.csv, NIFTY_11700_PE_02_JAN_20.csv
- `2019-07-18` (Thursday): `missing_contract_file` — Missing: NIFTY_11650_CE_02_JAN_20.csv
- `2019-07-19` (Friday): `missing_contract_file` — Missing: NIFTY_11650_CE_02_JAN_20.csv
- `2019-07-22` (Monday): `missing_contract_file` — Missing: NIFTY_11350_CE_02_JAN_20.csv
- `2019-07-23` (Tuesday): `missing_contract_file` — Missing: NIFTY_11350_CE_02_JAN_20.csv
- `2019-07-24` (Wednesday): `missing_contract_file` — Missing: NIFTY_11350_CE_02_JAN_20.csv
- `2019-07-25` (Thursday): `missing_entry_candle` — No 2019-07-25T09:20:00+05:30 candle in: NIFTY_11300_CE_02_JAN_20.csv, NIFTY_11300_PE_02_JAN_20.csv
- `2019-07-26` (Friday): `missing_entry_candle` — No 2019-07-26T09:20:00+05:30 candle in: NIFTY_11200_CE_02_JAN_20.csv, NIFTY_11200_PE_02_JAN_20.csv
- `2019-07-29` (Monday): `missing_entry_candle` — No 2019-07-29T09:20:00+05:30 candle in: NIFTY_11250_CE_02_JAN_20.csv, NIFTY_11250_PE_02_JAN_20.csv
- `2019-07-30` (Tuesday): `missing_entry_candle` — No 2019-07-30T09:20:00+05:30 candle in: NIFTY_11250_CE_02_JAN_20.csv, NIFTY_11250_PE_02_JAN_20.csv
- `2019-07-31` (Wednesday): `missing_contract_file` — Missing: NIFTY_11050_CE_02_JAN_20.csv, NIFTY_11050_PE_02_JAN_20.csv
- `2019-08-01` (Thursday): `missing_contract_file` — Missing: NIFTY_11050_CE_02_JAN_20.csv, NIFTY_11050_PE_02_JAN_20.csv

## Remarks

- SL is 40% above entry price per leg. Each leg is managed independently.
- Gap SL: if option opens ≥ SL price, fill at candle open.
- Intrabar SL: if high ≥ SL price, fill at SL price.
- SL monitoring uses the option contract's 1-minute candles.
- Balance check: if min(CE,PE)/max(CE,PE) < 0.80, the day is skipped.
- Lot sizing is applied per the expiry date of the traded contract.
