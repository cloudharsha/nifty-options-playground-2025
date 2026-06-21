# NIFTY Intraday ATM Straddle — 20% Independent SL — Monthly Options (2020–2026)

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `20%` above entry price, **independent per leg**
- Balance rule: skip if |CE − PE| / max(CE, PE) > 20%
- Contract: **monthly expiry** (last expiry of each calendar month)
- Expiry selection: on monthly expiry day → next month; otherwise current month
- Lot sizing (expiry-aware, targeting ~300 quantity):
  - Until 2021-10-06 expiry  : 75 × 4 = **300**
  - 2021-10-07 – 2024-04-25  : 50 × 6 = **300**
  - 2024-04-26 – 2024-11-21  : 25 × 12 = **300**
  - 2024-11-22 – 2025-12-30  : 75 × 4 = **300**
  - 2026+ expiry              : 65 × 5 = **325**
- Slippage: 0.50 pt/order
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Spot data: `NIFTY50_INDEX_5m_last_7y.csv`
- Options data: `NiftyOptions_2020_2026/Options`

## Overall Results

| Metric | Value |
|--------|-------|
| Traded days | `284` |
| Skipped days | `1442` |
| Winning days | `164` |
| Losing days | `120` |
| Win rate | `57.7%` |
| Days CE SL hit | `146` |
| Days PE SL hit | `173` |
| Days both SL hit | `71` |
| Days neither SL hit | `36` |
| Gross P/L | `₹-126301.15` |
| Total Brokerage | `₹28400.00` |
| **Net P/L** | **`₹-154701.15`** |
| Peak cumulative profit | `₹170970.60` |
| Max drawdown | `₹349482.50` |
| Best day | `2025-05-28` (Wednesday) `₹51905.00` qty=300 |
| Worst day | `2020-03-20` (Friday) `₹-51952.00` qty=300 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 65 | 41 | 24 | 35 | 39 | `₹88163.00` | `₹1356.35` |
| Tuesday | 70 | 49 | 21 | 32 | 39 | `₹280522.60` | `₹4007.47` |
| Wednesday | 61 | 28 | 33 | 40 | 34 | `₹-218081.25` | `₹-3575.10` |
| Thursday | 21 | 8 | 13 | 9 | 12 | `₹-180704.50` | `₹-8604.98` |
| Friday | 67 | 38 | 29 | 30 | 49 | `₹-124601.00` | `₹-1859.72` |

### Day-of-Week Detail

#### Monday
- Trades: `65`  Win: `41`  Loss: `24`  CE-SL: `35`  PE-SL: `39`
- Total Net P/L: `₹88163.00`  **Avg Net/Day: `₹1356.35`**
- Gross: `₹94663.00`  Brokerage: `₹6500.00`
- Best: `2020-03-23` `₹50213.00`  Worst: `2026-04-20` `₹-29951.25`

#### Tuesday
- Trades: `70`  Win: `49`  Loss: `21`  CE-SL: `32`  PE-SL: `39`
- Total Net P/L: `₹280522.60`  **Avg Net/Day: `₹4007.47`**
- Gross: `₹287522.60`  Brokerage: `₹7000.00`
- Best: `2022-01-25` `₹36227.00`  Worst: `2025-05-27` `₹-26227.00`

#### Wednesday
- Trades: `61`  Win: `28`  Loss: `33`  CE-SL: `40`  PE-SL: `34`
- Total Net P/L: `₹-218081.25`  **Avg Net/Day: `₹-3575.10`**
- Gross: `₹-211981.25`  Brokerage: `₹6100.00`
- Best: `2025-05-28` `₹51905.00`  Worst: `2026-06-03` `₹-51378.50`

#### Thursday
- Trades: `21`  Win: `8`  Loss: `13`  CE-SL: `9`  PE-SL: `12`
- Total Net P/L: `₹-180704.50`  **Avg Net/Day: `₹-8604.98`**
- Gross: `₹-178604.50`  Brokerage: `₹2100.00`
- Best: `2026-02-19` `₹20501.75`  Worst: `2026-04-30` `₹-49262.75`

#### Friday
- Trades: `67`  Win: `38`  Loss: `29`  CE-SL: `30`  PE-SL: `49`
- Total Net P/L: `₹-124601.00`  **Avg Net/Day: `₹-1859.72`**
- Gross: `₹-117901.00`  Brokerage: `₹6700.00`
- Best: `2025-04-25` `₹24446.00`  Worst: `2020-03-20` `₹-51952.00`

## Yearly Summary

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|------|--------|-----|------|---------------|-------------|
| 2020 | 29 | 15 | 14 | `₹-78284.00` | `₹-2699.45` |
| 2021 | 34 | 19 | 15 | `₹5681.00` | `₹167.09` |
| 2022 | 33 | 20 | 13 | `₹76248.00` | `₹2310.55` |
| 2023 | 18 | 10 | 8 | `₹-7203.00` | `₹-400.17` |
| 2024 | 30 | 21 | 9 | `₹119124.00` | `₹3970.80` |
| 2025 | 76 | 42 | 34 | `₹-24228.40` | `₹-318.79` |
| 2026 | 64 | 37 | 27 | `₹-246038.75` | `₹-3844.36` |

## Monthly Summary

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|-------|--------|-----|------|---------------|-------------|
| 2020-01 | 1 | 0 | 1 | `₹-8071.00` | `₹-8071.00` |
| 2020-02 | 2 | 1 | 1 | `₹574.00` | `₹287.00` |
| 2020-03 | 4 | 1 | 3 | `₹-42145.00` | `₹-10536.25` |
| 2020-04 | 3 | 1 | 2 | `₹-5259.00` | `₹-1753.00` |
| 2020-05 | 2 | 1 | 1 | `₹-10307.00` | `₹-5153.50` |
| 2020-06 | 3 | 1 | 2 | `₹-29541.00` | `₹-9847.00` |
| 2020-07 | 1 | 1 | 0 | `₹4046.00` | `₹4046.00` |
| 2020-08 | 3 | 2 | 1 | `₹846.00` | `₹282.00` |
| 2020-09 | 3 | 3 | 0 | `₹22236.00` | `₹7412.00` |
| 2020-10 | 2 | 2 | 0 | `₹6649.00` | `₹3324.50` |
| 2020-11 | 3 | 1 | 2 | `₹-20142.00` | `₹-6714.00` |
| 2020-12 | 2 | 1 | 1 | `₹2830.00` | `₹1415.00` |
| 2021-01 | 2 | 2 | 0 | `₹35179.00` | `₹17589.50` |
| 2021-02 | 4 | 0 | 4 | `₹-53752.00` | `₹-13438.00` |
| 2021-03 | 2 | 0 | 2 | `₹-41585.00` | `₹-20792.50` |
| 2021-04 | 3 | 1 | 2 | `₹-13341.00` | `₹-4447.00` |
| 2021-05 | 3 | 3 | 0 | `₹19989.00` | `₹6663.00` |
| 2021-06 | 2 | 1 | 1 | `₹16855.00` | `₹8427.50` |
| 2021-07 | 2 | 1 | 1 | `₹-2.00` | `₹-1.00` |
| 2021-08 | 3 | 1 | 2 | `₹-16362.00` | `₹-5454.00` |
| 2021-09 | 4 | 4 | 0 | `₹26891.00` | `₹6722.75` |
| 2021-10 | 3 | 1 | 2 | `₹-13764.00` | `₹-4588.00` |
| 2021-11 | 2 | 1 | 1 | `₹12157.00` | `₹6078.50` |
| 2021-12 | 4 | 4 | 0 | `₹33416.00` | `₹8354.00` |
| 2022-01 | 3 | 3 | 0 | `₹64833.00` | `₹21611.00` |
| 2022-02 | 4 | 3 | 1 | `₹21137.00` | `₹5284.25` |
| 2022-03 | 2 | 0 | 2 | `₹-23753.00` | `₹-11876.50` |
| 2022-04 | 4 | 1 | 3 | `₹-42622.00` | `₹-10655.50` |
| 2022-05 | 3 | 2 | 1 | `₹21012.00` | `₹7004.00` |
| 2022-06 | 4 | 1 | 3 | `₹-21514.00` | `₹-5378.50` |
| 2022-07 | 3 | 2 | 1 | `₹300.00` | `₹100.00` |
| 2022-08 | 3 | 3 | 0 | `₹45390.00` | `₹15130.00` |
| 2022-09 | 4 | 3 | 1 | `₹3644.00` | `₹911.00` |
| 2022-10 | 1 | 1 | 0 | `₹6890.00` | `₹6890.00` |
| 2022-12 | 2 | 1 | 1 | `₹931.00` | `₹465.50` |
| 2023-01 | 1 | 0 | 1 | `₹-12868.00` | `₹-12868.00` |
| 2023-02 | 2 | 1 | 1 | `₹739.00` | `₹369.50` |
| 2023-03 | 1 | 1 | 0 | `₹9743.00` | `₹9743.00` |
| 2023-04 | 3 | 2 | 1 | `₹-2133.00` | `₹-711.00` |
| 2023-05 | 1 | 0 | 1 | `₹-7246.00` | `₹-7246.00` |
| 2023-06 | 1 | 0 | 1 | `₹-7546.00` | `₹-7546.00` |
| 2023-07 | 1 | 1 | 0 | `₹1352.00` | `₹1352.00` |
| 2023-08 | 2 | 1 | 1 | `₹-488.00` | `₹-244.00` |
| 2023-09 | 2 | 1 | 1 | `₹-1196.00` | `₹-598.00` |
| 2023-10 | 2 | 2 | 0 | `₹13582.00` | `₹6791.00` |
| 2023-11 | 2 | 1 | 1 | `₹-1142.00` | `₹-571.00` |
| 2024-01 | 3 | 2 | 1 | `₹40023.00` | `₹13341.00` |
| 2024-02 | 3 | 3 | 0 | `₹35511.00` | `₹11837.00` |
| 2024-04 | 3 | 2 | 1 | `₹-4977.00` | `₹-1659.00` |
| 2024-06 | 4 | 4 | 0 | `₹48341.00` | `₹12085.25` |
| 2024-07 | 4 | 3 | 1 | `₹25787.00` | `₹6446.75` |
| 2024-08 | 3 | 1 | 2 | `₹-1485.00` | `₹-495.00` |
| 2024-09 | 3 | 2 | 1 | `₹-17499.00` | `₹-5833.00` |
| 2024-10 | 3 | 1 | 2 | `₹-9897.00` | `₹-3299.00` |
| 2024-11 | 3 | 3 | 0 | `₹28461.00` | `₹9487.00` |
| 2024-12 | 1 | 0 | 1 | `₹-25141.00` | `₹-25141.00` |
| 2025-01 | 15 | 8 | 7 | `₹-42485.40` | `₹-2832.36` |
| 2025-02 | 4 | 4 | 0 | `₹54410.00` | `₹13602.50` |
| 2025-03 | 8 | 4 | 4 | `₹-20591.00` | `₹-2573.88` |
| 2025-04 | 7 | 4 | 3 | `₹21356.00` | `₹3050.86` |
| 2025-05 | 13 | 7 | 6 | `₹28010.00` | `₹2154.62` |
| 2025-06 | 11 | 5 | 6 | `₹-27545.00` | `₹-2504.09` |
| 2025-07 | 9 | 5 | 4 | `₹-37254.00` | `₹-4139.33` |
| 2025-08 | 4 | 4 | 0 | `₹25619.00` | `₹6404.75` |
| 2025-09 | 1 | 0 | 1 | `₹-6463.00` | `₹-6463.00` |
| 2025-11 | 3 | 1 | 2 | `₹-11727.00` | `₹-3909.00` |
| 2025-12 | 1 | 0 | 1 | `₹-7558.00` | `₹-7558.00` |
| 2026-01 | 2 | 0 | 2 | `₹-49349.75` | `₹-24674.88` |
| 2026-02 | 7 | 4 | 3 | `₹-1285.00` | `₹-183.57` |
| 2026-03 | 10 | 7 | 3 | `₹50795.25` | `₹5079.52` |
| 2026-04 | 17 | 9 | 8 | `₹-92742.25` | `₹-5455.43` |
| 2026-05 | 16 | 10 | 6 | `₹-104345.50` | `₹-6521.59` |
| 2026-06 | 12 | 7 | 5 | `₹-49111.50` | `₹-4092.62` |

## Skip Reason Summary

- `missing_entry_candle`: 1139
- `balance_check_failed`: 282
- `missing_contract_file`: 17
- `missing_spot_entry`: 4
  _(balance check failures: 282)_

## Exceptions (first 30)

- `2019-06-21` (Friday): `missing_entry_candle` — No 2019-06-21T09:20:00+05:30 candle in: NIFTY_11800_CE_30_JAN_20.csv, NIFTY_11800_PE_30_JAN_20.csv
- `2019-06-24` (Monday): `missing_entry_candle` — No 2019-06-24T09:20:00+05:30 candle in: NIFTY_11750_CE_30_JAN_20.csv, NIFTY_11750_PE_30_JAN_20.csv
- `2019-06-25` (Tuesday): `missing_entry_candle` — No 2019-06-25T09:20:00+05:30 candle in: NIFTY_11650_CE_30_JAN_20.csv, NIFTY_11650_PE_30_JAN_20.csv
- `2019-06-26` (Wednesday): `missing_entry_candle` — No 2019-06-26T09:20:00+05:30 candle in: NIFTY_11800_CE_30_JAN_20.csv, NIFTY_11800_PE_30_JAN_20.csv
- `2019-06-27` (Thursday): `missing_entry_candle` — No 2019-06-27T09:20:00+05:30 candle in: NIFTY_11900_CE_30_JAN_20.csv, NIFTY_11900_PE_30_JAN_20.csv
- `2019-06-28` (Friday): `missing_entry_candle` — No 2019-06-28T09:20:00+05:30 candle in: NIFTY_11850_CE_30_JAN_20.csv, NIFTY_11850_PE_30_JAN_20.csv
- `2019-07-01` (Monday): `missing_entry_candle` — No 2019-07-01T09:20:00+05:30 candle in: NIFTY_11850_CE_30_JAN_20.csv, NIFTY_11850_PE_30_JAN_20.csv
- `2019-07-02` (Tuesday): `missing_entry_candle` — No 2019-07-02T09:20:00+05:30 candle in: NIFTY_11900_CE_30_JAN_20.csv, NIFTY_11900_PE_30_JAN_20.csv
- `2019-07-03` (Wednesday): `missing_entry_candle` — No 2019-07-03T09:20:00+05:30 candle in: NIFTY_11900_CE_30_JAN_20.csv, NIFTY_11900_PE_30_JAN_20.csv
- `2019-07-04` (Thursday): `missing_entry_candle` — No 2019-07-04T09:20:00+05:30 candle in: NIFTY_11950_CE_30_JAN_20.csv, NIFTY_11950_PE_30_JAN_20.csv
- `2019-07-05` (Friday): `missing_entry_candle` — No 2019-07-05T09:20:00+05:30 candle in: NIFTY_11950_CE_30_JAN_20.csv, NIFTY_11950_PE_30_JAN_20.csv
- `2019-07-08` (Monday): `missing_entry_candle` — No 2019-07-08T09:20:00+05:30 candle in: NIFTY_11700_CE_30_JAN_20.csv, NIFTY_11700_PE_30_JAN_20.csv
- `2019-07-09` (Tuesday): `missing_entry_candle` — No 2019-07-09T09:20:00+05:30 candle in: NIFTY_11500_CE_30_JAN_20.csv, NIFTY_11500_PE_30_JAN_20.csv
- `2019-07-10` (Wednesday): `missing_entry_candle` — No 2019-07-10T09:20:00+05:30 candle in: NIFTY_11550_CE_30_JAN_20.csv, NIFTY_11550_PE_30_JAN_20.csv
- `2019-07-11` (Thursday): `missing_entry_candle` — No 2019-07-11T09:20:00+05:30 candle in: NIFTY_11550_CE_30_JAN_20.csv, NIFTY_11550_PE_30_JAN_20.csv
- `2019-07-12` (Friday): `missing_entry_candle` — No 2019-07-12T09:20:00+05:30 candle in: NIFTY_11600_CE_30_JAN_20.csv, NIFTY_11600_PE_30_JAN_20.csv
- `2019-07-15` (Monday): `missing_entry_candle` — No 2019-07-15T09:20:00+05:30 candle in: NIFTY_11600_CE_30_JAN_20.csv, NIFTY_11600_PE_30_JAN_20.csv
- `2019-07-16` (Tuesday): `missing_entry_candle` — No 2019-07-16T09:20:00+05:30 candle in: NIFTY_11600_CE_30_JAN_20.csv, NIFTY_11600_PE_30_JAN_20.csv
- `2019-07-17` (Wednesday): `missing_entry_candle` — No 2019-07-17T09:20:00+05:30 candle in: NIFTY_11700_CE_30_JAN_20.csv, NIFTY_11700_PE_30_JAN_20.csv
- `2019-07-18` (Thursday): `missing_entry_candle` — No 2019-07-18T09:20:00+05:30 candle in: NIFTY_11650_CE_30_JAN_20.csv, NIFTY_11650_PE_30_JAN_20.csv
- `2019-07-19` (Friday): `missing_entry_candle` — No 2019-07-19T09:20:00+05:30 candle in: NIFTY_11650_CE_30_JAN_20.csv, NIFTY_11650_PE_30_JAN_20.csv
- `2019-07-22` (Monday): `missing_entry_candle` — No 2019-07-22T09:20:00+05:30 candle in: NIFTY_11350_CE_30_JAN_20.csv, NIFTY_11350_PE_30_JAN_20.csv
- `2019-07-23` (Tuesday): `missing_entry_candle` — No 2019-07-23T09:20:00+05:30 candle in: NIFTY_11350_CE_30_JAN_20.csv, NIFTY_11350_PE_30_JAN_20.csv
- `2019-07-24` (Wednesday): `missing_entry_candle` — No 2019-07-24T09:20:00+05:30 candle in: NIFTY_11350_CE_30_JAN_20.csv, NIFTY_11350_PE_30_JAN_20.csv
- `2019-07-25` (Thursday): `missing_entry_candle` — No 2019-07-25T09:20:00+05:30 candle in: NIFTY_11300_CE_30_JAN_20.csv, NIFTY_11300_PE_30_JAN_20.csv
- `2019-07-26` (Friday): `missing_entry_candle` — No 2019-07-26T09:20:00+05:30 candle in: NIFTY_11200_CE_30_JAN_20.csv, NIFTY_11200_PE_30_JAN_20.csv
- `2019-07-29` (Monday): `missing_entry_candle` — No 2019-07-29T09:20:00+05:30 candle in: NIFTY_11250_CE_30_JAN_20.csv, NIFTY_11250_PE_30_JAN_20.csv
- `2019-07-30` (Tuesday): `missing_entry_candle` — No 2019-07-30T09:20:00+05:30 candle in: NIFTY_11250_CE_30_JAN_20.csv, NIFTY_11250_PE_30_JAN_20.csv
- `2019-07-31` (Wednesday): `missing_entry_candle` — No 2019-07-31T09:20:00+05:30 candle in: NIFTY_11050_CE_30_JAN_20.csv, NIFTY_11050_PE_30_JAN_20.csv
- `2019-08-01` (Thursday): `missing_entry_candle` — No 2019-08-01T09:20:00+05:30 candle in: NIFTY_11050_CE_30_JAN_20.csv, NIFTY_11050_PE_30_JAN_20.csv

## Remarks

- Uses monthly contracts (last expiry of each calendar month).
- Monthly options carry significantly higher premium than weekly options.
- SL is 20% above entry price per leg; each leg exits independently.
- SL monitoring uses the option contract's 1-minute candles.
- Balance check: skip if min(CE,PE)/max(CE,PE) < 0.80 at entry.
- Lot sizing is expiry-aware to maintain ~300 quantity.
