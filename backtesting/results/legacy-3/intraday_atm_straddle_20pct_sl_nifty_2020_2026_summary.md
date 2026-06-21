# NIFTY Intraday ATM Straddle — 20% Independent SL (2020–2026)

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `20%` above entry price, **independent per leg**
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
| Winning days | `485` |
| Losing days | `403` |
| Win rate | `54.6%` |
| Days CE SL hit | `539` |
| Days PE SL hit | `571` |
| Days both SL hit | `271` |
| Days neither SL hit | `49` |
| Gross P/L | `₹305183.50` |
| Total Brokerage | `₹88800.00` |
| **Net P/L** | **`₹216383.50`** |
| Peak cumulative profit | `₹440223.00` |
| Max drawdown | `₹260277.00` |
| Best day | `2024-06-04` (Tuesday) `₹59966.00` qty=300 |
| Worst day | `2020-03-20` (Friday) `₹-51952.00` qty=300 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 211 | 128 | 83 | 127 | 129 | `₹287774.70` | `₹1363.86` |
| Tuesday | 211 | 115 | 96 | 129 | 144 | `₹106703.35` | `₹505.70` |
| Wednesday | 194 | 101 | 93 | 137 | 125 | `₹46746.70` | `₹240.96` |
| Thursday | 37 | 18 | 19 | 24 | 21 | `₹-94341.75` | `₹-2549.78` |
| Friday | 235 | 123 | 112 | 122 | 152 | `₹-130499.50` | `₹-555.32` |

### Day-of-Week Detail

#### Monday
- Trades: `211`  Win: `128`  Loss: `83`  CE-SL: `127`  PE-SL: `129`
- Total Net P/L: `₹287774.70`  **Avg Net/Day: `₹1363.86`**
- Gross: `₹308874.70`  Brokerage: `₹21100.00`
- Best: `2021-02-01` `₹51188.00`  Worst: `2026-04-20` `₹-29951.25`

#### Tuesday
- Trades: `211`  Win: `115`  Loss: `96`  CE-SL: `129`  PE-SL: `144`
- Total Net P/L: `₹106703.35`  **Avg Net/Day: `₹505.70`**
- Gross: `₹127803.35`  Brokerage: `₹21100.00`
- Best: `2024-06-04` `₹59966.00`  Worst: `2026-02-03` `₹-35180.50`

#### Wednesday
- Trades: `194`  Win: `101`  Loss: `93`  CE-SL: `137`  PE-SL: `125`
- Total Net P/L: `₹46746.70`  **Avg Net/Day: `₹240.96`**
- Gross: `₹66146.70`  Brokerage: `₹19400.00`
- Best: `2025-05-28` `₹51905.00`  Worst: `2020-03-25` `₹-37990.00`

#### Thursday
- Trades: `37`  Win: `18`  Loss: `19`  CE-SL: `24`  PE-SL: `21`
- Total Net P/L: `₹-94341.75`  **Avg Net/Day: `₹-2549.78`**
- Gross: `₹-90641.75`  Brokerage: `₹3700.00`
- Best: `2025-01-02` `₹33632.00`  Worst: `2026-01-29` `₹-26997.00`

#### Friday
- Trades: `235`  Win: `123`  Loss: `112`  CE-SL: `122`  PE-SL: `152`
- Total Net P/L: `₹-130499.50`  **Avg Net/Day: `₹-555.32`**
- Gross: `₹-106999.50`  Brokerage: `₹23500.00`
- Best: `2024-12-06` `₹32675.00`  Worst: `2020-03-20` `₹-51952.00`

## Yearly Summary

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|------|--------|-----|------|---------------|-------------|
| 2020 | 122 | 64 | 58 | `₹-72983.00` | `₹-598.22` |
| 2021 | 153 | 87 | 66 | `₹233952.00` | `₹1529.10` |
| 2022 | 154 | 82 | 72 | `₹-10693.00` | `₹-69.44` |
| 2023 | 96 | 52 | 44 | `₹-26271.00` | `₹-273.66` |
| 2024 | 145 | 84 | 61 | `₹243977.60` | `₹1682.60` |
| 2025 | 142 | 73 | 69 | `₹-78628.60` | `₹-553.72` |
| 2026 | 76 | 43 | 33 | `₹-72970.50` | `₹-960.14` |

## Monthly Summary

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|-------|--------|-----|------|---------------|-------------|
| 2020-01 | 7 | 4 | 3 | `₹-2602.00` | `₹-371.71` |
| 2020-02 | 7 | 5 | 2 | `₹20615.00` | `₹2945.00` |
| 2020-03 | 11 | 4 | 7 | `₹-63767.00` | `₹-5797.00` |
| 2020-04 | 11 | 6 | 5 | `₹25846.00` | `₹2349.64` |
| 2020-05 | 10 | 7 | 3 | `₹30716.00` | `₹3071.60` |
| 2020-06 | 10 | 7 | 3 | `₹21002.00` | `₹2100.20` |
| 2020-07 | 8 | 4 | 4 | `₹6097.00` | `₹762.12` |
| 2020-08 | 12 | 9 | 3 | `₹19623.00` | `₹1635.25` |
| 2020-09 | 11 | 5 | 6 | `₹-17021.00` | `₹-1547.36` |
| 2020-10 | 10 | 5 | 5 | `₹-20761.00` | `₹-2076.10` |
| 2020-11 | 13 | 5 | 8 | `₹-54274.00` | `₹-4174.92` |
| 2020-12 | 12 | 3 | 9 | `₹-38457.00` | `₹-3204.75` |
| 2021-01 | 13 | 10 | 3 | `₹87185.00` | `₹6706.54` |
| 2021-02 | 12 | 4 | 8 | `₹-41754.00` | `₹-3479.50` |
| 2021-03 | 15 | 5 | 10 | `₹-86337.00` | `₹-5755.80` |
| 2021-04 | 13 | 9 | 4 | `₹60818.00` | `₹4678.31` |
| 2021-05 | 11 | 8 | 3 | `₹58999.00` | `₹5363.55` |
| 2021-06 | 13 | 4 | 9 | `₹-15133.00` | `₹-1164.08` |
| 2021-07 | 10 | 5 | 5 | `₹-1156.00` | `₹-115.60` |
| 2021-08 | 11 | 7 | 4 | `₹-9128.00` | `₹-829.82` |
| 2021-09 | 13 | 5 | 8 | `₹-32170.00` | `₹-2474.62` |
| 2021-10 | 13 | 9 | 4 | `₹63764.00` | `₹4904.92` |
| 2021-11 | 12 | 7 | 5 | `₹31482.00` | `₹2623.50` |
| 2021-12 | 17 | 14 | 3 | `₹117382.00` | `₹6904.82` |
| 2022-01 | 15 | 7 | 8 | `₹11064.00` | `₹737.60` |
| 2022-02 | 15 | 8 | 7 | `₹-1632.00` | `₹-108.80` |
| 2022-03 | 13 | 5 | 8 | `₹-56104.00` | `₹-4315.69` |
| 2022-04 | 14 | 5 | 9 | `₹-60557.00` | `₹-4325.50` |
| 2022-05 | 14 | 9 | 5 | `₹43069.00` | `₹3076.36` |
| 2022-06 | 14 | 5 | 9 | `₹-78530.00` | `₹-5609.29` |
| 2022-07 | 14 | 8 | 6 | `₹-16412.00` | `₹-1172.29` |
| 2022-08 | 14 | 11 | 3 | `₹86767.00` | `₹6197.64` |
| 2022-09 | 16 | 11 | 5 | `₹52145.00` | `₹3259.06` |
| 2022-10 | 13 | 9 | 4 | `₹67598.00` | `₹5199.85` |
| 2022-11 | 7 | 3 | 4 | `₹-25723.00` | `₹-3674.71` |
| 2022-12 | 5 | 1 | 4 | `₹-32378.00` | `₹-6475.60` |
| 2023-01 | 6 | 3 | 3 | `₹-4314.00` | `₹-719.00` |
| 2023-02 | 10 | 4 | 6 | `₹-24037.00` | `₹-2403.70` |
| 2023-03 | 12 | 8 | 4 | `₹48129.00` | `₹4010.75` |
| 2023-04 | 9 | 5 | 4 | `₹-1752.00` | `₹-194.67` |
| 2023-05 | 6 | 3 | 3 | `₹-357.00` | `₹-59.50` |
| 2023-06 | 4 | 3 | 1 | `₹9932.00` | `₹2483.00` |
| 2023-07 | 7 | 3 | 4 | `₹-27112.00` | `₹-3873.14` |
| 2023-08 | 11 | 5 | 6 | `₹-28871.00` | `₹-2624.64` |
| 2023-09 | 8 | 5 | 3 | `₹13474.00` | `₹1684.25` |
| 2023-10 | 12 | 7 | 5 | `₹-4242.00` | `₹-353.50` |
| 2023-11 | 6 | 3 | 3 | `₹-1476.00` | `₹-246.00` |
| 2023-12 | 5 | 3 | 2 | `₹-5645.00` | `₹-1129.00` |
| 2024-01 | 14 | 8 | 6 | `₹71485.00` | `₹5106.07` |
| 2024-02 | 14 | 8 | 6 | `₹7708.00` | `₹550.57` |
| 2024-03 | 7 | 5 | 2 | `₹10271.00` | `₹1467.29` |
| 2024-04 | 12 | 8 | 4 | `₹6339.00` | `₹528.25` |
| 2024-05 | 6 | 3 | 3 | `₹-2409.00` | `₹-401.50` |
| 2024-06 | 13 | 8 | 5 | `₹96005.00` | `₹7385.00` |
| 2024-07 | 15 | 10 | 5 | `₹49008.00` | `₹3267.20` |
| 2024-08 | 12 | 6 | 6 | `₹-16371.00` | `₹-1364.25` |
| 2024-09 | 13 | 4 | 9 | `₹-67651.00` | `₹-5203.92` |
| 2024-10 | 14 | 9 | 5 | `₹70579.00` | `₹5041.36` |
| 2024-11 | 12 | 9 | 3 | `₹52719.00` | `₹4393.25` |
| 2024-12 | 13 | 6 | 7 | `₹-33705.40` | `₹-2592.72` |
| 2025-01 | 21 | 10 | 11 | `₹-11386.20` | `₹-542.20` |
| 2025-02 | 11 | 8 | 3 | `₹34462.00` | `₹3132.91` |
| 2025-03 | 10 | 3 | 7 | `₹-88741.00` | `₹-8874.10` |
| 2025-04 | 15 | 7 | 8 | `₹-839.40` | `₹-55.96` |
| 2025-05 | 20 | 11 | 9 | `₹39004.00` | `₹1950.20` |
| 2025-06 | 17 | 10 | 7 | `₹38182.00` | `₹2246.00` |
| 2025-07 | 17 | 6 | 11 | `₹-60152.00` | `₹-3538.35` |
| 2025-08 | 11 | 7 | 4 | `₹-18353.00` | `₹-1668.45` |
| 2025-09 | 5 | 4 | 1 | `₹23482.00` | `₹4696.40` |
| 2025-10 | 2 | 1 | 1 | `₹-2354.00` | `₹-1177.00` |
| 2025-11 | 6 | 3 | 3 | `₹-5262.00` | `₹-877.00` |
| 2025-12 | 7 | 3 | 4 | `₹-26671.00` | `₹-3810.14` |
| 2026-01 | 10 | 3 | 7 | `₹-59321.25` | `₹-5932.12` |
| 2026-02 | 12 | 7 | 5 | `₹-8161.50` | `₹-680.12` |
| 2026-03 | 17 | 12 | 5 | `₹102595.75` | `₹6035.04` |
| 2026-04 | 17 | 10 | 7 | `₹-50950.50` | `₹-2997.09` |
| 2026-05 | 11 | 7 | 4 | `₹-9455.75` | `₹-859.61` |
| 2026-06 | 9 | 4 | 5 | `₹-47677.25` | `₹-5297.47` |

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

- SL is 20% above entry price per leg. Each leg is managed independently.
- Gap SL: if option opens ≥ SL price, fill at candle open.
- Intrabar SL: if high ≥ SL price, fill at SL price.
- SL monitoring uses the option contract's 1-minute candles.
- Balance check: if min(CE,PE)/max(CE,PE) < 0.80, the day is skipped.
- Lot sizing is applied per the expiry date of the traded contract.
