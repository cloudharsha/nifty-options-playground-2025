# NIFTY Intraday ATM Straddle — 20% Independent SL, Expiry Day Included

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 50 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `20%` above entry price, **independent per leg**
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
| Winning days | `840` |
| Losing days | `733` |
| Win rate | `53.4%` |
| Days CE SL hit | `1012` |
| Days PE SL hit | `1076` |
| Days both SL hit | `567` |
| Days neither SL hit | `52` |
| Gross P/L | `₹1205626.15` |
| Total Brokerage | `₹157300.00` |
| **Net P/L** | **`₹1048326.15`** |
| Peak cumulative profit | `₹1324006.60` |
| Max drawdown | `₹293982.70` |
| Best day | `2025-04-09` (Wednesday) `₹75725.00` qty=300 |
| Worst day | `2020-03-20` (Friday) `₹-51952.00` qty=300 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 314 | 183 | 131 | 199 | 194 | `₹158380.65` | `₹504.40` |
| Tuesday | 316 | 159 | 157 | 211 | 225 | `₹22294.40` | `₹70.55` |
| Wednesday | 318 | 166 | 152 | 220 | 214 | `₹232540.95` | `₹731.26` |
| Thursday | 316 | 164 | 152 | 217 | 243 | `₹659593.15` | `₹2087.32` |
| Friday | 309 | 168 | 141 | 165 | 200 | `₹-24483.00` | `₹-79.23` |

### Day-of-Week Detail

#### Monday
- Trades: `314`  Win: `183`  Loss: `131`  CE-SL: `199`  PE-SL: `194`
- Total Net P/L: `₹158380.65`  **Avg Net/Day: `₹504.40`**
- Gross: `₹189780.65`  Brokerage: `₹31400.00`
- Best: `2021-02-01` `₹51188.00`  Worst: `2026-04-20` `₹-29951.25`

#### Tuesday
- Trades: `316`  Win: `159`  Loss: `157`  CE-SL: `211`  PE-SL: `225`
- Total Net P/L: `₹22294.40`  **Avg Net/Day: `₹70.55`**
- Gross: `₹53894.40`  Brokerage: `₹31600.00`
- Best: `2024-06-04` `₹59966.00`  Worst: `2022-02-01` `₹-27241.00`

#### Wednesday
- Trades: `318`  Win: `166`  Loss: `152`  CE-SL: `220`  PE-SL: `214`
- Total Net P/L: `₹232540.95`  **Avg Net/Day: `₹731.26`**
- Gross: `₹264340.95`  Brokerage: `₹31800.00`
- Best: `2025-04-09` `₹75725.00`  Worst: `2020-03-25` `₹-37990.00`

#### Thursday
- Trades: `316`  Win: `164`  Loss: `152`  CE-SL: `217`  PE-SL: `243`
- Total Net P/L: `₹659593.15`  **Avg Net/Day: `₹2087.32`**
- Gross: `₹691193.15`  Brokerage: `₹31600.00`
- Best: `2020-03-26` `₹40592.00`  Worst: `2026-01-29` `₹-26997.00`

#### Friday
- Trades: `309`  Win: `168`  Loss: `141`  CE-SL: `165`  PE-SL: `200`
- Total Net P/L: `₹-24483.00`  **Avg Net/Day: `₹-79.23`**
- Gross: `₹6417.00`  Brokerage: `₹30900.00`
- Best: `2024-12-06` `₹32675.00`  Worst: `2020-03-20` `₹-51952.00`

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

- SL is 20% above entry price per leg. Each leg is managed independently.
- Gap SL: if option opens ≥ SL price, fill at candle open.
- Intrabar SL: if high ≥ SL price, fill at SL price.
- SL monitoring uses the option contract's 1-minute candles.
- No balance filter applied — all days with valid entry candles are traded.
- On expiry day, the expiring contract itself is traded (not next week).
- Strike interval: 50 points.
- NIFTY lot sizing is applied per the expiry date of the traded contract.
