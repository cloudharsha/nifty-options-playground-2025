# NIFTY Intraday ATM Straddle — 50% Independent SL, Expiry Day Included

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `50%` above entry price, **independent per leg**
- Expiry: always current-week expiry, **including on expiry day itself**
- Balance filter: **disabled** (no CE/PE ratio check)
- Lot sizing (expiry-aware, targeting ~300 quantity):
  - Until 2021-10-06 expiry  : 75 × 4 = **300**
  - 2021-10-07 – 2024-04-25  : 50 × 6 = **300**
  - 2024-04-26 – 2024-11-21  : 25 × 12 = **300**
  - 2024-11-22 – 2025-12-30  : 75 × 4 = **300**
  - 2026+ expiry              : 65 × 5 = **325**
- Slippage: 0.50 pt/order (2 × per leg, applied to points P&L)
- Brokerage: ₹25.00/order → ₹100.00/straddle

## Overall Results

| Metric | Value |
|--------|-------|
| Traded days | `1573` |
| Skipped days | `153` |
| Winning days | `979` |
| Losing days | `594` |
| Win rate | `62.2%` |
| Days CE SL hit | `586` |
| Days PE SL hit | `656` |
| Days both SL hit | `128` |
| Days neither SL hit | `459` |
| Gross P/L | `₹1714657.03` |
| Total Brokerage | `₹157300.00` |
| **Net P/L** | **`₹1557357.03`** |
| Peak cumulative profit | `₹1879143.25` |
| Max drawdown | `₹350852.47` |
| Best day | `2026-02-03` (Tuesday) `₹76551.25` qty=325 |
| Worst day | `2026-06-03` (Wednesday) `₹-65685.00` qty=325 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 314 | 179 | 135 | 97 | 108 | `₹-13346.73` | `₹-42.51` |
| Tuesday | 316 | 197 | 119 | 120 | 128 | `₹216172.39` | `₹684.09` |
| Wednesday | 318 | 199 | 119 | 133 | 133 | `₹429971.37` | `₹1352.11` |
| Thursday | 316 | 215 | 101 | 168 | 188 | `₹601547.76` | `₹1903.63` |
| Friday | 309 | 189 | 120 | 68 | 99 | `₹323012.24` | `₹1045.35` |

### Day-of-Week Detail

#### Monday
- Trades: `314`  Win: `179`  Loss: `135`  CE-SL: `97`  PE-SL: `108`
- Total Net P/L: `₹-13346.73`  **Avg Net/Day: `₹-42.51`**
- Gross: `₹18053.27`  Brokerage: `₹31400.00`
- Best: `2020-03-30` `₹44330.00`  Worst: `2026-03-16` `₹-57397.50`

#### Tuesday
- Trades: `316`  Win: `197`  Loss: `119`  CE-SL: `120`  PE-SL: `128`
- Total Net P/L: `₹216172.39`  **Avg Net/Day: `₹684.09`**
- Gross: `₹247772.39`  Brokerage: `₹31600.00`
- Best: `2026-02-03` `₹76551.25`  Worst: `2025-04-08` `₹-52795.00`

#### Wednesday
- Trades: `318`  Win: `199`  Loss: `119`  CE-SL: `133`  PE-SL: `133`
- Total Net P/L: `₹429971.37`  **Avg Net/Day: `₹1352.11`**
- Gross: `₹461771.37`  Brokerage: `₹31800.00`
- Best: `2025-04-09` `₹75725.00`  Worst: `2026-06-03` `₹-65685.00`

#### Thursday
- Trades: `316`  Win: `215`  Loss: `101`  CE-SL: `168`  PE-SL: `188`
- Total Net P/L: `₹601547.76`  **Avg Net/Day: `₹1903.63`**
- Gross: `₹633147.76`  Brokerage: `₹31600.00`
- Best: `2024-02-01` `₹71795.00`  Worst: `2026-04-30` `₹-60289.99`

#### Friday
- Trades: `309`  Win: `189`  Loss: `120`  CE-SL: `68`  PE-SL: `99`
- Total Net P/L: `₹323012.24`  **Avg Net/Day: `₹1045.35`**
- Gross: `₹353912.24`  Brokerage: `₹30900.00`
- Best: `2024-12-06` `₹32675.00`  Worst: `2025-05-02` `₹-61480.00`

## Skip Reason Summary

- `missing_entry_candle`: 106
- `missing_contract_file`: 43
- `missing_spot_entry`: 4

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
- No balance filter applied — all days with valid entry candles are traded.
- On expiry day, the expiring contract itself is traded (not next week).
- Strike interval: 50 points.
- NIFTY lot sizing is applied per the expiry date of the traded contract.
