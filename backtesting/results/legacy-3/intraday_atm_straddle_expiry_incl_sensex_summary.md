# SENSEX Intraday ATM Straddle — 20% Independent SL, Expiry Day Included

## Strategy Details

- Entry: `09:20` — sell ATM CE + PE (nearest 100 to spot open)
- Exit: `15:20` — day close if SL not hit
- Stop loss: `20%` above entry price, **independent per leg**
- Expiry: always current-week expiry, **including on expiry day itself**
- Balance filter: **disabled** (no CE/PE ratio check)
- Lot size: `10` × `10` lots = **100 quantity** (fixed)
- Slippage: 0.50 pt/order (2 × per leg, applied to points P&L)
- Brokerage: ₹25.00/order → ₹100.00/straddle

## Overall Results

| Metric | Value |
|--------|-------|
| Traded days | `376` |
| Skipped days | `1345` |
| Winning days | `197` |
| Losing days | `179` |
| Win rate | `52.4%` |
| Days CE SL hit | `244` |
| Days PE SL hit | `259` |
| Days both SL hit | `145` |
| Days neither SL hit | `18` |
| Gross P/L | `₹366640.00` |
| Total Brokerage | `₹37600.00` |
| **Net P/L** | **`₹329040.00`** |
| Peak cumulative profit | `₹395413.80` |
| Max drawdown | `₹170380.80` |
| Best day | `2024-12-06` (Friday) `₹80771.00` qty=100 |
| Worst day | `2025-01-29` (Wednesday) `₹-38087.00` qty=100 |

## Results by Day of Week

| Day | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|--------|-----|------|-------|-------|---------------|-------------|
| Monday | 77 | 43 | 34 | 51 | 48 | `₹72213.80` | `₹937.84` |
| Tuesday | 79 | 43 | 36 | 51 | 61 | `₹201418.40` | `₹2549.60` |
| Wednesday | 71 | 33 | 38 | 51 | 41 | `₹-122721.60` | `₹-1728.47` |
| Thursday | 73 | 34 | 39 | 49 | 53 | `₹-16278.20` | `₹-222.99` |
| Friday | 76 | 44 | 32 | 42 | 56 | `₹194407.60` | `₹2557.99` |

### Day-of-Week Detail

#### Monday
- Trades: `77`  Win: `43`  Loss: `34`  CE-SL: `51`  PE-SL: `48`
- Total Net P/L: `₹72213.80`  **Avg Net/Day: `₹937.84`**
- Gross: `₹79913.80`  Brokerage: `₹7700.00`
- Best: `2024-09-23` `₹80190.00`  Worst: `2026-03-02` `₹-26535.00`

#### Tuesday
- Trades: `79`  Win: `43`  Loss: `36`  CE-SL: `51`  PE-SL: `61`
- Total Net P/L: `₹201418.40`  **Avg Net/Day: `₹2549.60`**
- Gross: `₹209318.40`  Brokerage: `₹7900.00`
- Best: `2025-05-13` `₹30816.00`  Worst: `2024-11-05` `₹-27814.00`

#### Wednesday
- Trades: `71`  Win: `33`  Loss: `38`  CE-SL: `51`  PE-SL: `41`
- Total Net P/L: `₹-122721.60`  **Avg Net/Day: `₹-1728.47`**
- Gross: `₹-115621.60`  Brokerage: `₹7100.00`
- Best: `2025-05-28` `₹33655.00`  Worst: `2025-01-29` `₹-38087.00`

#### Thursday
- Trades: `73`  Win: `34`  Loss: `39`  CE-SL: `49`  PE-SL: `53`
- Total Net P/L: `₹-16278.20`  **Avg Net/Day: `₹-222.99`**
- Gross: `₹-8978.20`  Brokerage: `₹7300.00`
- Best: `2025-01-02` `₹37460.00`  Worst: `2025-05-15` `₹-24570.00`

#### Friday
- Trades: `76`  Win: `44`  Loss: `32`  CE-SL: `42`  PE-SL: `56`
- Total Net P/L: `₹194407.60`  **Avg Net/Day: `₹2557.99`**
- Gross: `₹202007.60`  Brokerage: `₹7600.00`
- Best: `2024-12-06` `₹80771.00`  Worst: `2026-05-15` `₹-29404.00`

## Skip Reason Summary

- `missing_contract_file`: 1229
- `missing_entry_candle`: 110
- `missing_spot_entry`: 6

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
- No balance filter applied — all days with valid entry candles are traded.
- On expiry day, the expiring contract itself is traded (not next week).
- Strike interval: 100 points.
