# NIFTY Intraday ATM Straddle — 40% Independent SL, Expiry Day Included

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `40%` above entry price, **independent per leg**
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
| Winning days | `973` |
| Losing days | `600` |
| Win rate | `61.9%` |
| Days CE SL hit | `697` |
| Days PE SL hit | `773` |
| Days both SL hit | `200` |
| Days neither SL hit | `303` |
| Gross P/L | `₹1221610.25` |
| Total Brokerage | `₹157300.00` |
| **Net P/L** | **`₹1064310.25`** |
| Peak cumulative profit | `₹1429909.40` |
| Max drawdown | `₹388167.90` |
| Best day | `2025-04-09` (Wednesday) `₹75725.00` qty=300 |
| Worst day | `2026-06-03` (Wednesday) `₹-52698.00` qty=325 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 314 | 181 | 133 | 124 | 131 | `₹-67747.10` | `₹-215.76` |
| Tuesday | 316 | 192 | 124 | 144 | 156 | `₹-98241.95` | `₹-310.89` |
| Wednesday | 318 | 190 | 128 | 160 | 164 | `₹218877.45` | `₹688.29` |
| Thursday | 316 | 206 | 110 | 182 | 202 | `₹665377.60` | `₹2105.63` |
| Friday | 309 | 204 | 105 | 87 | 120 | `₹346044.25` | `₹1119.88` |

### Day-of-Week Detail

#### Monday
- Trades: `314`  Win: `181`  Loss: `133`  CE-SL: `124`  PE-SL: `131`
- Total Net P/L: `₹-67747.10`  **Avg Net/Day: `₹-215.76`**
- Gross: `₹-36347.10`  Brokerage: `₹31400.00`
- Best: `2020-03-30` `₹44330.00`  Worst: `2026-03-16` `₹-46068.00`

#### Tuesday
- Trades: `316`  Win: `192`  Loss: `124`  CE-SL: `144`  PE-SL: `156`
- Total Net P/L: `₹-98241.95`  **Avg Net/Day: `₹-310.89`**
- Gross: `₹-66641.95`  Brokerage: `₹31600.00`
- Best: `2024-06-04` `₹37202.00`  Worst: `2025-05-27` `₹-51754.00`

#### Wednesday
- Trades: `318`  Win: `190`  Loss: `128`  CE-SL: `160`  PE-SL: `164`
- Total Net P/L: `₹218877.45`  **Avg Net/Day: `₹688.29`**
- Gross: `₹250677.45`  Brokerage: `₹31800.00`
- Best: `2025-04-09` `₹75725.00`  Worst: `2026-06-03` `₹-52698.00`

#### Thursday
- Trades: `316`  Win: `206`  Loss: `110`  CE-SL: `182`  PE-SL: `202`
- Total Net P/L: `₹665377.60`  **Avg Net/Day: `₹2105.63`**
- Gross: `₹696977.60`  Brokerage: `₹31600.00`
- Best: `2024-11-21` `₹55970.00`  Worst: `2026-04-30` `₹-48382.00`

#### Friday
- Trades: `309`  Win: `204`  Loss: `105`  CE-SL: `87`  PE-SL: `120`
- Total Net P/L: `₹346044.25`  **Avg Net/Day: `₹1119.88`**
- Gross: `₹376944.25`  Brokerage: `₹30900.00`
- Best: `2024-12-06` `₹32675.00`  Worst: `2024-12-20` `₹-49582.00`

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

- SL is 40% above entry price per leg. Each leg is managed independently.
- Gap SL: if option opens ≥ SL price, fill at candle open.
- Intrabar SL: if high ≥ SL price, fill at SL price.
- SL monitoring uses the option contract's 1-minute candles.
- No balance filter applied — all days with valid entry candles are traded.
- On expiry day, the expiring contract itself is traded (not next week).
- Strike interval: 50 points.
- NIFTY lot sizing is applied per the expiry date of the traded contract.
