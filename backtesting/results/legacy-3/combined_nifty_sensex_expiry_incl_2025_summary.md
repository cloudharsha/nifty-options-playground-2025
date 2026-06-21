# Combined NIFTY + SENSEX Intraday ATM Straddle — Expiry Day Included (Sep 2025+)

## Strategy Details

- Period: `2025-09-01` → latest available data
- Entry: `09:20` | Exit: `15:20`
- Stop loss: `20%` above entry price, **independent per leg**
- Expiry: current-week expiry, **traded even on expiry day itself** (no roll)
- Balance filter: **disabled**
- **Monday / Tuesday / Friday** → NIFTY weekly options (~300 qty, strike rounding 50)
- **Wednesday / Thursday**       → SENSEX weekly options (~100 qty, strike rounding 100)
- NIFTY lot sizing (expiry-aware):
  - Until 2025-12-30 : 75 × 4 = **300**
  - 2026+ expiry      : 65 × 5 = **325**
- SENSEX lot sizing: 10 × 10 = **100** (fixed)
- Slippage: 0.50 pt/order (2× per leg)
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Notional capital for CAGR: ₹500,000

---

## Overall Combined Results

### Combined (NIFTY + SENSEX)

| Metric | Value |
|--------|-------|
| Traded days | `165` |
| Winning days | `80` |
| Losing days | `85` |
| Win rate | `48.5%` |
| Days CE SL hit | `120` |
| Days PE SL hit | `120` |
| Days both SL hit | `79` |
| Days neither SL hit | `4` |
| Gross P/L | `₹43512.25` |
| Total Brokerage | `₹16500.00` |
| **Net P/L** | **`₹27012.25`** |
| Max cumulative profit | `₹82492.75` |
| Max drawdown | `₹132820.50` |
| **CAGR** (on ₹500,000 capital) | **`6.90%`** |
| Best day | `2026-02-03` (Tuesday) `₹38708.25` |
| Worst day | `2026-04-20` (Monday) `₹-29951.25` |

## Per-Index Results

### NIFTY (Mon / Tue / Fri)

| Metric | Value |
|--------|-------|
| Traded days | `110` |
| Winning days | `54` |
| Losing days | `56` |
| Win rate | `49.1%` |
| Days CE SL hit | `76` |
| Days PE SL hit | `80` |
| Days both SL hit | `50` |
| Days neither SL hit | `4` |
| Gross P/L | `₹8814.05` |
| Total Brokerage | `₹11000.00` |
| **Net P/L** | **`₹-2185.95`** |
| Max cumulative profit | `₹38173.55` |
| Max drawdown | `₹66840.00` |
| **CAGR** (on ₹500,000 capital) | **`-0.55%`** |
| Best day | `2026-02-03` (Tuesday) `₹38708.25` |
| Worst day | `2026-04-20` (Monday) `₹-29951.25` |

### SENSEX (Wed / Thu)

| Metric | Value |
|--------|-------|
| Traded days | `55` |
| Winning days | `26` |
| Losing days | `29` |
| Win rate | `47.3%` |
| Days CE SL hit | `44` |
| Days PE SL hit | `40` |
| Days both SL hit | `29` |
| Days neither SL hit | `0` |
| Gross P/L | `₹34698.20` |
| Total Brokerage | `₹5500.00` |
| **Net P/L** | **`₹29198.20`** |
| Max cumulative profit | `₹57120.00` |
| Max drawdown | `₹86167.80` |
| **CAGR** (on ₹500,000 capital) | **`7.89%`** |
| Best day | `2026-03-11` (Wednesday) `₹28024.00` |
| Worst day | `2026-06-03` (Wednesday) `₹-15121.00` |

---

## Results by Day of Week

| Day | Index | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|-------|--------|-----|------|-------|-------|---------------|-------------|
| Monday | NIFTY | 38 | 21 | 17 | 29 | 22 | `₹34244.25` | `₹901.16` |
| Tuesday | NIFTY | 35 | 13 | 22 | 27 | 30 | `₹-7599.20` | `₹-217.12` |
| Wednesday | SENSEX | 29 | 17 | 12 | 24 | 17 | `₹42285.00` | `₹1458.10` |
| Thursday | SENSEX | 26 | 9 | 17 | 20 | 23 | `₹-13086.80` | `₹-503.34` |
| Friday | NIFTY | 37 | 20 | 17 | 20 | 28 | `₹-28831.00` | `₹-779.22` |

### Day-of-Week Detail

#### Monday (NIFTY)
- Trades: `38`  Win: `21`  Loss: `17`  CE-SL: `29`  PE-SL: `22`
- Total Net P/L: `₹34244.25`  **Avg Net/Day: `₹901.16`**
- Gross: `₹38044.25`  Brokerage: `₹3800.00`
- Best: `2026-02-02` `₹38350.75`  Worst: `2026-04-20` `₹-29951.25`

#### Tuesday (NIFTY)
- Trades: `35`  Win: `13`  Loss: `22`  CE-SL: `27`  PE-SL: `30`
- Total Net P/L: `₹-7599.20`  **Avg Net/Day: `₹-217.12`**
- Gross: `₹-4099.20`  Brokerage: `₹3500.00`
- Best: `2026-02-03` `₹38708.25`  Worst: `2026-03-24` `₹-15765.00`

#### Wednesday (SENSEX)
- Trades: `29`  Win: `17`  Loss: `12`  CE-SL: `24`  PE-SL: `17`
- Total Net P/L: `₹42285.00`  **Avg Net/Day: `₹1458.10`**
- Gross: `₹45185.00`  Brokerage: `₹2900.00`
- Best: `2026-03-11` `₹28024.00`  Worst: `2026-06-03` `₹-15121.00`

#### Thursday (SENSEX)
- Trades: `26`  Win: `9`  Loss: `17`  CE-SL: `20`  PE-SL: `23`
- Total Net P/L: `₹-13086.80`  **Avg Net/Day: `₹-503.34`**
- Gross: `₹-10486.80`  Brokerage: `₹2600.00`
- Best: `2026-03-12` `₹18231.00`  Worst: `2026-03-05` `₹-11635.00`

#### Friday (NIFTY)
- Trades: `37`  Win: `20`  Loss: `17`  CE-SL: `20`  PE-SL: `28`
- Total Net P/L: `₹-28831.00`  **Avg Net/Day: `₹-779.22`**
- Gross: `₹-25131.00`  Brokerage: `₹3700.00`
- Best: `2026-01-23` `₹30271.25`  Worst: `2026-03-06` `₹-28901.50`

---

## Monthly Summary (Combined)

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |
|-------|--------|-----|------|---------------|-------------|----------------|
| 2025-09 | 22 | 11 | 11 | `₹1732.00` | `₹78.73` | `₹1732.00` |
| 2025-10 | 20 | 10 | 10 | `₹1109.00` | `₹55.45` | `₹2841.00` |
| 2025-11 | 19 | 10 | 9 | `₹14025.00` | `₹738.16` | `₹16866.00` |
| 2025-12 | 22 | 9 | 13 | `₹-32654.00` | `₹-1484.27` | `₹-15788.00` |
| 2026-01 | 20 | 7 | 13 | `₹-53417.50` | `₹-2670.88` | `₹-69205.50` |
| 2026-02 | 20 | 11 | 9 | `₹86471.00` | `₹4323.55` | `₹17265.50` |
| 2026-03 | 16 | 8 | 8 | `₹24287.25` | `₹1517.95` | `₹41552.75` |
| 2026-04 | 12 | 8 | 4 | `₹4779.50` | `₹398.29` | `₹46332.25` |
| 2026-05 | 8 | 4 | 4 | `₹-3933.00` | `₹-491.62` | `₹42399.25` |
| 2026-06 | 6 | 2 | 4 | `₹-15387.00` | `₹-2564.50` | `₹27012.25` |

## Yearly Summary (Combined)

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day | CAGR |
|------|--------|-----|------|---------------|-------------|------|
| 2025 | 83 | 40 | 43 | `₹-15788.00` | `₹-190.22` | `-9.2%` |
| 2026 | 82 | 40 | 42 | `₹42800.25` | `₹521.95` | `19.8%` |

## Monthly Summary — NIFTY only

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |
|-------|--------|-----|------|---------------|-------------|----------------|
| 2025-09 | 14 | 6 | 8 | `₹-13871.00` | `₹-990.79` | `₹-13871.00` |
| 2025-10 | 12 | 6 | 6 | `₹-3684.00` | `₹-307.00` | `₹-17555.00` |
| 2025-11 | 12 | 6 | 6 | `₹-5592.00` | `₹-466.00` | `₹-23147.00` |
| 2025-12 | 14 | 7 | 7 | `₹-1616.00` | `₹-115.43` | `₹-24763.00` |
| 2026-01 | 12 | 5 | 7 | `₹-15394.70` | `₹-1282.89` | `₹-40157.70` |
| 2026-02 | 12 | 7 | 5 | `₹74343.00` | `₹6195.25` | `₹34185.30` |
| 2026-03 | 12 | 5 | 7 | `₹-14495.75` | `₹-1207.98` | `₹19689.55` |
| 2026-04 | 10 | 7 | 3 | `₹5922.50` | `₹592.25` | `₹25612.05` |
| 2026-05 | 7 | 3 | 4 | `₹-27532.00` | `₹-3933.14` | `₹-1919.95` |
| 2026-06 | 5 | 2 | 3 | `₹-266.00` | `₹-53.20` | `₹-2185.95` |

## Monthly Summary — SENSEX only

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |
|-------|--------|-----|------|---------------|-------------|----------------|
| 2025-09 | 8 | 5 | 3 | `₹15603.00` | `₹1950.38` | `₹15603.00` |
| 2025-10 | 8 | 4 | 4 | `₹4793.00` | `₹599.12` | `₹20396.00` |
| 2025-11 | 7 | 4 | 3 | `₹19617.00` | `₹2802.43` | `₹40013.00` |
| 2025-12 | 8 | 2 | 6 | `₹-31038.00` | `₹-3879.75` | `₹8975.00` |
| 2026-01 | 8 | 2 | 6 | `₹-38022.80` | `₹-4752.85` | `₹-29047.80` |
| 2026-02 | 8 | 4 | 4 | `₹12128.00` | `₹1516.00` | `₹-16919.80` |
| 2026-03 | 4 | 3 | 1 | `₹38783.00` | `₹9695.75` | `₹21863.20` |
| 2026-04 | 2 | 1 | 1 | `₹-1143.00` | `₹-571.50` | `₹20720.20` |
| 2026-05 | 1 | 1 | 0 | `₹23599.00` | `₹23599.00` | `₹44319.20` |
| 2026-06 | 1 | 0 | 1 | `₹-15121.00` | `₹-15121.00` | `₹29198.20` |

---

## Skip Reason Summary

- `SENSEX:missing_entry_candle`: 13
- `SENSEX:missing_contract_file`: 9
- `NIFTY:missing_entry_candle`: 9
- `NIFTY:missing_spot_entry`: 1

## First 30 Skipped Days

- `2025-10-21` (Tuesday) [NIFTY]: `missing_spot_entry` — No NIFTY spot candle at 2025-10-21T09:20:00+05:30.
- `2026-05-04` (Monday) [NIFTY]: `missing_entry_candle` — No 2026-05-04T09:20:00+05:30 candle in: NIFTY_24200_CE_05_MAY_26.csv, NIFTY_24200_PE_05_MAY_26.csv
- `2026-05-05` (Tuesday) [NIFTY]: `missing_entry_candle` — No 2026-05-05T09:20:00+05:30 candle in: NIFTY_24050_CE_05_MAY_26.csv, NIFTY_24050_PE_05_MAY_26.csv
- `2026-05-08` (Friday) [NIFTY]: `missing_entry_candle` — No 2026-05-08T09:20:00+05:30 candle in: NIFTY_24200_CE_12_MAY_26.csv, NIFTY_24200_PE_12_MAY_26.csv
- `2026-05-11` (Monday) [NIFTY]: `missing_entry_candle` — No 2026-05-11T09:20:00+05:30 candle in: NIFTY_23900_CE_12_MAY_26.csv, NIFTY_23900_PE_12_MAY_26.csv
- `2026-05-12` (Tuesday) [NIFTY]: `missing_entry_candle` — No 2026-05-12T09:20:00+05:30 candle in: NIFTY_23750_CE_12_MAY_26.csv, NIFTY_23750_PE_12_MAY_26.csv
- `2026-06-05` (Friday) [NIFTY]: `missing_entry_candle` — No 2026-06-05T09:20:00+05:30 candle in: NIFTY_23450_CE_09_JUN_26.csv, NIFTY_23450_PE_09_JUN_26.csv
- `2026-06-08` (Monday) [NIFTY]: `missing_entry_candle` — No 2026-06-08T09:20:00+05:30 candle in: NIFTY_23150_CE_09_JUN_26.csv, NIFTY_23150_PE_09_JUN_26.csv
- `2026-06-09` (Tuesday) [NIFTY]: `missing_entry_candle` — No 2026-06-09T09:20:00+05:30 candle in: NIFTY_23250_CE_09_JUN_26.csv, NIFTY_23250_PE_09_JUN_26.csv
- `2026-06-19` (Friday) [NIFTY]: `missing_entry_candle` — No 2026-06-19T09:20:00+05:30 candle in: NIFTY_24000_CE_23_JUN_26.csv, NIFTY_24000_PE_23_JUN_26.csv
- `2026-03-18` (Wednesday) [SENSEX]: `missing_entry_candle` — No 2026-03-18T09:20:00+05:30 candle in: SENSEX_76500_CE_23_APR_26.csv, SENSEX_76500_PE_23_APR_26.csv
- `2026-03-19` (Thursday) [SENSEX]: `missing_entry_candle` — No 2026-03-19T09:20:00+05:30 candle in: SENSEX_75100_CE_23_APR_26.csv, SENSEX_75100_PE_23_APR_26.csv
- `2026-03-25` (Wednesday) [SENSEX]: `missing_entry_candle` — No 2026-03-25T09:20:00+05:30 candle in: SENSEX_74800_CE_23_APR_26.csv, SENSEX_74800_PE_23_APR_26.csv
- `2026-04-01` (Wednesday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_73800_CE_23_APR_26.csv
- `2026-04-02` (Thursday) [SENSEX]: `missing_entry_candle` — No 2026-04-02T09:20:00+05:30 candle in: SENSEX_71700_CE_23_APR_26.csv, SENSEX_71700_PE_23_APR_26.csv
- `2026-04-08` (Wednesday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_77300_CE_23_APR_26.csv, SENSEX_77300_PE_23_APR_26.csv
- `2026-04-09` (Thursday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_77300_CE_23_APR_26.csv, SENSEX_77300_PE_23_APR_26.csv
- `2026-04-15` (Wednesday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_78100_CE_23_APR_26.csv, SENSEX_78100_PE_23_APR_26.csv
- `2026-04-16` (Thursday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_78700_CE_23_APR_26.csv, SENSEX_78700_PE_23_APR_26.csv
- `2026-04-22` (Wednesday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_78900_CE_23_APR_26.csv, SENSEX_78900_PE_23_APR_26.csv
- `2026-04-23` (Thursday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_77900_CE_23_APR_26.csv, SENSEX_77900_PE_23_APR_26.csv
- `2026-05-06` (Wednesday) [SENSEX]: `missing_entry_candle` — No 2026-05-06T09:20:00+05:30 candle in: SENSEX_77400_CE_07_MAY_26.csv, SENSEX_77400_PE_07_MAY_26.csv
- `2026-05-07` (Thursday) [SENSEX]: `missing_entry_candle` — No 2026-05-07T09:20:00+05:30 candle in: SENSEX_77900_CE_07_MAY_26.csv, SENSEX_77900_PE_07_MAY_26.csv
- `2026-05-13` (Wednesday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_74600_CE_14_MAY_26.csv, SENSEX_74600_PE_14_MAY_26.csv
- `2026-05-14` (Thursday) [SENSEX]: `missing_contract_file` — Missing: SENSEX_75000_CE_14_MAY_26.csv
- `2026-05-21` (Thursday) [SENSEX]: `missing_entry_candle` — No 2026-05-21T09:20:00+05:30 candle in: SENSEX_75600_CE_21_MAY_26.csv, SENSEX_75600_PE_21_MAY_26.csv
- `2026-05-27` (Wednesday) [SENSEX]: `missing_entry_candle` — No 2026-05-27T09:20:00+05:30 candle in: SENSEX_76000_CE_27_MAY_26.csv, SENSEX_76000_PE_27_MAY_26.csv
- `2026-06-04` (Thursday) [SENSEX]: `missing_entry_candle` — No 2026-06-04T09:20:00+05:30 candle in: SENSEX_74100_CE_04_JUN_26.csv, SENSEX_74100_PE_04_JUN_26.csv
- `2026-06-10` (Wednesday) [SENSEX]: `missing_entry_candle` — No 2026-06-10T09:20:00+05:30 candle in: SENSEX_74300_CE_11_JUN_26.csv, SENSEX_74300_PE_11_JUN_26.csv
- `2026-06-11` (Thursday) [SENSEX]: `missing_entry_candle` — No 2026-06-11T09:20:00+05:30 candle in: SENSEX_73600_CE_11_JUN_26.csv, SENSEX_73600_PE_11_JUN_26.csv

## Remarks

- Both legs managed independently; one SL hit does not exit the other.
- gap_sl  : option opens at/above SL → filled at candle open.
- sl      : option high touches SL price → filled at SL.
- SL monitoring uses 1-minute option candles.
- No balance filter — all days with valid entry candles are traded.
- CAGR computed on notional capital via --capital arg.
- Max drawdown = largest peak-to-trough drop in running cumulative equity.
