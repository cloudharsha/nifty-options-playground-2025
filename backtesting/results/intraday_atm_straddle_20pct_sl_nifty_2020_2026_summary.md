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
