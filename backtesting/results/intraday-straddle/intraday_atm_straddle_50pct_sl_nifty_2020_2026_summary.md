# NIFTY Intraday ATM Straddle — 50% Independent SL (2020–2026)

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `50%` above entry price, **independent per leg**
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
| Winning days | `553` |
| Losing days | `335` |
| Win rate | `62.3%` |
| Days CE SL hit | `283` |
| Days PE SL hit | `311` |
| Days both SL hit | `39` |
| Days neither SL hit | `333` |
| Gross P/L | `₹573010.78` |
| Total Brokerage | `₹88800.00` |
| **Net P/L** | **`₹484210.78`** |
| Peak cumulative profit | `₹678915.00` |
| Max drawdown | `₹230816.00` |
| Best day | `2025-05-28` (Wednesday) `₹51905.00` qty=300 |
| Worst day | `2026-06-03` (Wednesday) `₹-65685.00` qty=325 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 211 | 127 | 84 | 61 | 76 | `₹86481.01` | `₹409.86` |
| Tuesday | 211 | 132 | 79 | 72 | 77 | `₹216483.51` | `₹1025.99` |
| Wednesday | 194 | 129 | 65 | 85 | 78 | `₹140647.13` | `₹724.99` |
| Thursday | 37 | 18 | 19 | 14 | 8 | `₹-171864.36` | `₹-4644.98` |
| Friday | 235 | 147 | 88 | 51 | 72 | `₹212463.49` | `₹904.10` |

### Day-of-Week Detail

#### Monday
- Trades: `211`  Win: `127`  Loss: `84`  CE-SL: `61`  PE-SL: `76`
- Total Net P/L: `₹86481.01`  **Avg Net/Day: `₹409.86`**
- Gross: `₹107581.01`  Brokerage: `₹21100.00`
- Best: `2020-03-30` `₹44330.00`  Worst: `2025-06-23` `₹-43450.00`

#### Tuesday
- Trades: `211`  Win: `132`  Loss: `79`  CE-SL: `72`  PE-SL: `77`
- Total Net P/L: `₹216483.51`  **Avg Net/Day: `₹1025.99`**
- Gross: `₹237583.51`  Brokerage: `₹21100.00`
- Best: `2022-02-01` `₹48140.00`  Worst: `2025-04-08` `₹-52795.00`

#### Wednesday
- Trades: `194`  Win: `129`  Loss: `65`  CE-SL: `85`  PE-SL: `78`
- Total Net P/L: `₹140647.13`  **Avg Net/Day: `₹724.99`**
- Gross: `₹160047.13`  Brokerage: `₹19400.00`
- Best: `2025-05-28` `₹51905.00`  Worst: `2026-06-03` `₹-65685.00`

#### Thursday
- Trades: `37`  Win: `18`  Loss: `19`  CE-SL: `14`  PE-SL: `8`
- Total Net P/L: `₹-171864.36`  **Avg Net/Day: `₹-4644.98`**
- Gross: `₹-168164.36`  Brokerage: `₹3700.00`
- Best: `2026-03-12` `₹19513.75`  Worst: `2026-04-30` `₹-60289.99`

#### Friday
- Trades: `235`  Win: `147`  Loss: `88`  CE-SL: `51`  PE-SL: `72`
- Total Net P/L: `₹212463.49`  **Avg Net/Day: `₹904.10`**
- Gross: `₹235963.49`  Brokerage: `₹23500.00`
- Best: `2024-12-06` `₹32675.00`  Worst: `2025-05-02` `₹-61480.00`

## Yearly Summary

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|------|--------|-----|------|---------------|-------------|
| 2020 | 122 | 73 | 49 | `₹77560.00` | `₹635.74` |
| 2021 | 153 | 102 | 51 | `₹130237.50` | `₹851.23` |
| 2022 | 154 | 105 | 49 | `₹409602.50` | `₹2659.76` |
| 2023 | 96 | 55 | 41 | `₹-57480.00` | `₹-598.75` |
| 2024 | 145 | 94 | 51 | `₹-96473.50` | `₹-665.33` |
| 2025 | 142 | 79 | 63 | `₹80348.00` | `₹565.83` |
| 2026 | 76 | 45 | 31 | `₹-59583.72` | `₹-784.00` |

## Monthly Summary

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|-------|--------|-----|------|---------------|-------------|
| 2020-01 | 7 | 3 | 4 | `₹-10210.00` | `₹-1458.57` |
| 2020-02 | 7 | 1 | 6 | `₹-9520.00` | `₹-1360.00` |
| 2020-03 | 11 | 7 | 4 | `₹87295.00` | `₹7935.91` |
| 2020-04 | 11 | 8 | 3 | `₹28667.50` | `₹2606.14` |
| 2020-05 | 10 | 8 | 2 | `₹33507.50` | `₹3350.75` |
| 2020-06 | 10 | 6 | 4 | `₹37662.50` | `₹3766.25` |
| 2020-07 | 8 | 5 | 3 | `₹11387.50` | `₹1423.44` |
| 2020-08 | 12 | 9 | 3 | `₹10582.50` | `₹881.88` |
| 2020-09 | 11 | 7 | 4 | `₹-7062.50` | `₹-642.05` |
| 2020-10 | 10 | 6 | 4 | `₹-19817.50` | `₹-1981.75` |
| 2020-11 | 13 | 7 | 6 | `₹-22862.50` | `₹-1758.65` |
| 2020-12 | 12 | 6 | 6 | `₹-62070.00` | `₹-5172.50` |
| 2021-01 | 13 | 7 | 6 | `₹3215.00` | `₹247.31` |
| 2021-02 | 12 | 4 | 8 | `₹-1207.50` | `₹-100.62` |
| 2021-03 | 15 | 13 | 2 | `₹117667.50` | `₹7844.50` |
| 2021-04 | 13 | 13 | 0 | `₹75102.50` | `₹5777.12` |
| 2021-05 | 11 | 8 | 3 | `₹13810.00` | `₹1255.45` |
| 2021-06 | 13 | 9 | 4 | `₹-17912.50` | `₹-1377.88` |
| 2021-07 | 10 | 6 | 4 | `₹-550.00` | `₹-55.00` |
| 2021-08 | 11 | 3 | 8 | `₹-28332.50` | `₹-2575.68` |
| 2021-09 | 13 | 7 | 6 | `₹-47027.50` | `₹-3617.50` |
| 2021-10 | 13 | 10 | 3 | `₹31010.00` | `₹2385.38` |
| 2021-11 | 12 | 8 | 4 | `₹-70035.00` | `₹-5836.25` |
| 2021-12 | 17 | 14 | 3 | `₹54497.50` | `₹3205.74` |
| 2022-01 | 15 | 10 | 5 | `₹38445.00` | `₹2563.00` |
| 2022-02 | 15 | 12 | 3 | `₹155355.00` | `₹10357.00` |
| 2022-03 | 13 | 8 | 5 | `₹19827.50` | `₹1525.19` |
| 2022-04 | 14 | 11 | 3 | `₹69100.00` | `₹4935.71` |
| 2022-05 | 14 | 11 | 3 | `₹69490.00` | `₹4963.57` |
| 2022-06 | 14 | 10 | 4 | `₹32837.50` | `₹2345.54` |
| 2022-07 | 14 | 13 | 1 | `₹49097.50` | `₹3506.96` |
| 2022-08 | 14 | 9 | 5 | `₹28300.00` | `₹2021.43` |
| 2022-09 | 16 | 7 | 9 | `₹-22382.50` | `₹-1398.91` |
| 2022-10 | 13 | 9 | 4 | `₹9792.50` | `₹753.27` |
| 2022-11 | 7 | 3 | 4 | `₹-5650.00` | `₹-807.14` |
| 2022-12 | 5 | 2 | 3 | `₹-34610.00` | `₹-6922.00` |
| 2023-01 | 6 | 4 | 2 | `₹-8377.50` | `₹-1396.25` |
| 2023-02 | 10 | 7 | 3 | `₹-60017.50` | `₹-6001.75` |
| 2023-03 | 12 | 7 | 5 | `₹-1125.00` | `₹-93.75` |
| 2023-04 | 9 | 5 | 4 | `₹5475.00` | `₹608.33` |
| 2023-05 | 6 | 3 | 3 | `₹-5430.00` | `₹-905.00` |
| 2023-06 | 4 | 1 | 3 | `₹-3977.50` | `₹-994.38` |
| 2023-07 | 7 | 4 | 3 | `₹-347.50` | `₹-49.64` |
| 2023-08 | 11 | 9 | 2 | `₹18872.50` | `₹1715.68` |
| 2023-09 | 8 | 5 | 3 | `₹13967.50` | `₹1745.94` |
| 2023-10 | 12 | 7 | 5 | `₹-13942.50` | `₹-1161.88` |
| 2023-11 | 6 | 2 | 4 | `₹-390.00` | `₹-65.00` |
| 2023-12 | 5 | 1 | 4 | `₹-2187.50` | `₹-437.50` |
| 2024-01 | 14 | 9 | 5 | `₹-7557.50` | `₹-539.82` |
| 2024-02 | 14 | 11 | 3 | `₹20110.00` | `₹1436.43` |
| 2024-03 | 7 | 5 | 2 | `₹25340.00` | `₹3620.00` |
| 2024-04 | 12 | 8 | 4 | `₹26302.50` | `₹2191.88` |
| 2024-05 | 6 | 4 | 2 | `₹-922.50` | `₹-153.75` |
| 2024-06 | 13 | 9 | 4 | `₹16850.00` | `₹1296.15` |
| 2024-07 | 15 | 8 | 7 | `₹2812.50` | `₹187.50` |
| 2024-08 | 12 | 6 | 6 | `₹-54757.50` | `₹-4563.12` |
| 2024-09 | 13 | 10 | 3 | `₹-17665.00` | `₹-1358.85` |
| 2024-10 | 14 | 10 | 4 | `₹-85302.50` | `₹-6093.04` |
| 2024-11 | 12 | 6 | 6 | `₹-2805.00` | `₹-233.75` |
| 2024-12 | 13 | 8 | 5 | `₹-18878.50` | `₹-1452.19` |
| 2025-01 | 21 | 12 | 9 | `₹58300.50` | `₹2776.21` |
| 2025-02 | 11 | 7 | 4 | `₹27647.50` | `₹2513.41` |
| 2025-03 | 10 | 5 | 5 | `₹-33446.50` | `₹-3344.65` |
| 2025-04 | 15 | 10 | 5 | `₹-6369.00` | `₹-424.60` |
| 2025-05 | 20 | 10 | 10 | `₹27973.00` | `₹1398.65` |
| 2025-06 | 17 | 10 | 7 | `₹15812.50` | `₹930.15` |
| 2025-07 | 17 | 10 | 7 | `₹12565.00` | `₹739.12` |
| 2025-08 | 11 | 7 | 4 | `₹20830.00` | `₹1893.64` |
| 2025-09 | 5 | 2 | 3 | `₹-10205.00` | `₹-2041.00` |
| 2025-10 | 2 | 0 | 2 | `₹-1880.00` | `₹-940.00` |
| 2025-11 | 6 | 3 | 3 | `₹-13567.50` | `₹-2261.25` |
| 2025-12 | 7 | 3 | 4 | `₹-17312.50` | `₹-2473.21` |
| 2026-01 | 10 | 7 | 3 | `₹13421.87` | `₹1342.19` |
| 2026-02 | 12 | 9 | 3 | `₹87866.25` | `₹7322.19` |
| 2026-03 | 17 | 8 | 9 | `₹-41398.75` | `₹-2435.22` |
| 2026-04 | 17 | 8 | 9 | `₹-97298.73` | `₹-5723.45` |
| 2026-05 | 11 | 8 | 3 | `₹50891.88` | `₹4626.53` |
| 2026-06 | 9 | 5 | 4 | `₹-73066.24` | `₹-8118.47` |

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

- SL is 50% above entry price per leg. Each leg is managed independently.
- Gap SL: if option opens ≥ SL price, fill at candle open.
- Intrabar SL: if high ≥ SL price, fill at SL price.
- SL monitoring uses the option contract's 1-minute candles.
- Balance check: if min(CE,PE)/max(CE,PE) < 0.80, the day is skipped.
- Lot sizing is applied per the expiry date of the traded contract.
