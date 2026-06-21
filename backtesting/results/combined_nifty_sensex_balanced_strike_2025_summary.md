# Combined NIFTY + SENSEX — Balanced Strike Search (Sep 2025+)

## Strategy Details

- Period: `2025-09-01` → latest available data
- Entry: `09:20` | Exit: `15:20`
- Stop loss: `20%` above entry price, **independent per leg**
- Expiry: current-week expiry, **traded even on expiry day itself** (no roll)
- Balance filter: **disabled** (replaced by strike search)
- **Strike search**: start at ATM, try ±1, ±2 … ±5 strikes
  until `min(CE,PE)/max(CE,PE) >= 70%`.
  If no balanced strike found → day skipped.
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
| Traded days | `161` |
| Winning days | `77` |
| Losing days | `84` |
| Win rate | `47.8%` |
| Days CE SL hit | `118` |
| Days PE SL hit | `117` |
| Days both SL hit | `78` |
| Days neither SL hit | `4` |
| Traded at ATM | `133` |
| Traded at adjusted strike | `28` |
| Gross P/L | `₹-6853.25` |
| Total Brokerage | `₹16100.00` |
| **Net P/L** | **`₹-22953.25`** |
| Max cumulative profit | `₹81407.00` |
| Max drawdown | `₹179462.00` |
| **CAGR** (on ₹500,000 capital) | **`-5.79%`** |
| Best day | `2026-02-03` (Tuesday) `₹38708.25` |
| Worst day | `2026-04-20` (Monday) `₹-29951.25` |

## Per-Index Results

### NIFTY (Mon / Tue / Fri)

| Metric | Value |
|--------|-------|
| Traded days | `106` |
| Winning days | `51` |
| Losing days | `55` |
| Win rate | `48.1%` |
| Days CE SL hit | `74` |
| Days PE SL hit | `77` |
| Days both SL hit | `49` |
| Days neither SL hit | `4` |
| Traded at ATM | `84` |
| Traded at adjusted strike | `22` |
| Gross P/L | `₹-60067.45` |
| Total Brokerage | `₹10600.00` |
| **Net P/L** | **`₹-70667.45`** |
| Max cumulative profit | `₹17717.00` |
| Max drawdown | `₹106210.95` |
| **CAGR** (on ₹500,000 capital) | **`-17.57%`** |
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
| Traded at ATM | `49` |
| Traded at adjusted strike | `6` |
| Gross P/L | `₹53214.20` |
| Total Brokerage | `₹5500.00` |
| **Net P/L** | **`₹47714.20`** |
| Max cumulative profit | `₹75636.00` |
| Max drawdown | `₹86167.80` |
| **CAGR** (on ₹500,000 capital) | **`12.97%`** |
| Best day | `2026-03-11` (Wednesday) `₹28024.00` |
| Worst day | `2026-06-03` (Wednesday) `₹-15121.00` |

---

## Strike Offset Analysis

How often the strategy moved away from ATM to find a balanced pair:

| Offset (strikes from ATM) | Trades | Win | Loss | Total Net P/L | Avg Net/Day |
|--------------------------|--------|-----|------|---------------|-------------|
| ATM (0) | 133 | 66 | 67 | `₹45625.25` | `₹343.05` |
| ±1 | 26 | 10 | 16 | `₹-65047.50` | `₹-2501.83` |
| ±2 | 2 | 1 | 1 | `₹-3531.00` | `₹-1765.50` |

---

## Results by Day of Week

| Day | Index | Trades | Win | Loss | CE-SL | PE-SL | Total Net P/L | Avg Net/Day |
|-----|-------|--------|-----|------|-------|-------|---------------|-------------|
| Monday | NIFTY | 37 | 19 | 18 | 29 | 22 | `₹-7286.75` | `₹-196.94` |
| Tuesday | NIFTY | 32 | 13 | 19 | 24 | 27 | `₹13290.05` | `₹415.31` |
| Wednesday | SENSEX | 29 | 17 | 12 | 24 | 17 | `₹60634.00` | `₹2090.83` |
| Thursday | SENSEX | 26 | 9 | 17 | 20 | 23 | `₹-12919.80` | `₹-496.92` |
| Friday | NIFTY | 37 | 19 | 18 | 21 | 28 | `₹-76670.75` | `₹-2072.18` |

### Day-of-Week Detail

#### Monday (NIFTY)
- Trades: `37`  Win: `19`  Loss: `18`  CE-SL: `29`  PE-SL: `22`  At-ATM: `28`
- Total Net P/L: `₹-7286.75`  **Avg Net/Day: `₹-196.94`**
- Gross: `₹-3586.75`  Brokerage: `₹3700.00`
- Best: `2026-02-02` `₹38350.75`  Worst: `2026-04-20` `₹-29951.25`

#### Tuesday (NIFTY)
- Trades: `32`  Win: `13`  Loss: `19`  CE-SL: `24`  PE-SL: `27`  At-ATM: `29`
- Total Net P/L: `₹13290.05`  **Avg Net/Day: `₹415.31`**
- Gross: `₹16490.05`  Brokerage: `₹3200.00`
- Best: `2026-02-03` `₹38708.25`  Worst: `2026-03-24` `₹-15765.00`

#### Wednesday (SENSEX)
- Trades: `29`  Win: `17`  Loss: `12`  CE-SL: `24`  PE-SL: `17`  At-ATM: `24`
- Total Net P/L: `₹60634.00`  **Avg Net/Day: `₹2090.83`**
- Gross: `₹63534.00`  Brokerage: `₹2900.00`
- Best: `2026-03-11` `₹28024.00`  Worst: `2026-06-03` `₹-15121.00`

#### Thursday (SENSEX)
- Trades: `26`  Win: `9`  Loss: `17`  CE-SL: `20`  PE-SL: `23`  At-ATM: `25`
- Total Net P/L: `₹-12919.80`  **Avg Net/Day: `₹-496.92`**
- Gross: `₹-10319.80`  Brokerage: `₹2600.00`
- Best: `2026-03-12` `₹18231.00`  Worst: `2026-03-05` `₹-11635.00`

#### Friday (NIFTY)
- Trades: `37`  Win: `19`  Loss: `18`  CE-SL: `21`  PE-SL: `28`  At-ATM: `27`
- Total Net P/L: `₹-76670.75`  **Avg Net/Day: `₹-2072.18`**
- Gross: `₹-72970.75`  Brokerage: `₹3700.00`
- Best: `2026-03-13` `₹23618.50`  Worst: `2026-03-06` `₹-28901.50`

---

## Monthly Summary (Combined)

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |
|-------|--------|-----|------|---------------|-------------|----------------|
| 2025-09 | 20 | 11 | 9 | `₹18135.00` | `₹906.75` | `₹18135.00` |
| 2025-10 | 19 | 9 | 10 | `₹-1179.00` | `₹-62.05` | `₹16956.00` |
| 2025-11 | 19 | 10 | 9 | `₹23478.00` | `₹1235.68` | `₹40434.00` |
| 2025-12 | 22 | 9 | 13 | `₹-38057.00` | `₹-1729.86` | `₹2377.00` |
| 2026-01 | 20 | 6 | 14 | `₹-100432.00` | `₹-5021.60` | `₹-98055.00` |
| 2026-02 | 19 | 11 | 8 | `₹93789.25` | `₹4936.28` | `₹-4265.75` |
| 2026-03 | 16 | 8 | 8 | `₹24287.25` | `₹1517.95` | `₹20021.50` |
| 2026-04 | 12 | 7 | 5 | `₹-17535.00` | `₹-1461.25` | `₹2486.50` |
| 2026-05 | 8 | 4 | 4 | `₹-10052.75` | `₹-1256.59` | `₹-7566.25` |
| 2026-06 | 6 | 2 | 4 | `₹-15387.00` | `₹-2564.50` | `₹-22953.25` |

## Yearly Summary (Combined)

| Year | Trades | Win | Loss | Total Net P/L | Avg Net/Day | CAGR |
|------|--------|-----|------|---------------|-------------|------|
| 2025 | 80 | 39 | 41 | `₹2377.00` | `₹29.71` | `1.4%` |
| 2026 | 81 | 38 | 43 | `₹-25330.25` | `₹-312.72` | `-10.8%` |

## Monthly Summary — NIFTY only

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |
|-------|--------|-----|------|---------------|-------------|----------------|
| 2025-09 | 12 | 6 | 6 | `₹-2058.00` | `₹-171.50` | `₹-2058.00` |
| 2025-10 | 11 | 5 | 6 | `₹-11279.00` | `₹-1025.36` | `₹-13337.00` |
| 2025-11 | 12 | 6 | 6 | `₹-4758.00` | `₹-396.50` | `₹-18095.00` |
| 2025-12 | 14 | 7 | 7 | `₹-7019.00` | `₹-501.36` | `₹-25114.00` |
| 2026-01 | 12 | 4 | 8 | `₹-62409.20` | `₹-5200.77` | `₹-87523.20` |
| 2026-02 | 11 | 7 | 4 | `₹81661.25` | `₹7423.75` | `₹-5861.95` |
| 2026-03 | 12 | 5 | 7 | `₹-14495.75` | `₹-1207.98` | `₹-20357.70` |
| 2026-04 | 10 | 6 | 4 | `₹-16392.00` | `₹-1639.20` | `₹-36749.70` |
| 2026-05 | 7 | 3 | 4 | `₹-33651.75` | `₹-4807.39` | `₹-70401.45` |
| 2026-06 | 5 | 2 | 3 | `₹-266.00` | `₹-53.20` | `₹-70667.45` |

## Monthly Summary — SENSEX only

| Month | Trades | Win | Loss | Total Net P/L | Avg Net/Day | Cumulative P/L |
|-------|--------|-----|------|---------------|-------------|----------------|
| 2025-09 | 8 | 5 | 3 | `₹20193.00` | `₹2524.12` | `₹20193.00` |
| 2025-10 | 8 | 4 | 4 | `₹10100.00` | `₹1262.50` | `₹30293.00` |
| 2025-11 | 7 | 4 | 3 | `₹28236.00` | `₹4033.71` | `₹58529.00` |
| 2025-12 | 8 | 2 | 6 | `₹-31038.00` | `₹-3879.75` | `₹27491.00` |
| 2026-01 | 8 | 2 | 6 | `₹-38022.80` | `₹-4752.85` | `₹-10531.80` |
| 2026-02 | 8 | 4 | 4 | `₹12128.00` | `₹1516.00` | `₹1596.20` |
| 2026-03 | 4 | 3 | 1 | `₹38783.00` | `₹9695.75` | `₹40379.20` |
| 2026-04 | 2 | 1 | 1 | `₹-1143.00` | `₹-571.50` | `₹39236.20` |
| 2026-05 | 1 | 1 | 0 | `₹23599.00` | `₹23599.00` | `₹62835.20` |
| 2026-06 | 1 | 0 | 1 | `₹-15121.00` | `₹-15121.00` | `₹47714.20` |

---

## Skip Reason Summary

- `SENSEX:no_balanced_strike`: 22
- `NIFTY:no_balanced_strike`: 13
- `NIFTY:missing_spot_entry`: 1

## First 30 Skipped Days

- `2025-09-02` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24650 passes 70% balance rule.
- `2025-09-30` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24700 passes 70% balance rule.
- `2025-10-20` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=25900 passes 70% balance rule.
- `2025-10-21` (Tuesday) [NIFTY]: `missing_spot_entry` — No NIFTY spot candle at 2025-10-21T09:20:00+05:30.
- `2026-02-10` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=25900 passes 70% balance rule.
- `2026-05-04` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24200 passes 70% balance rule.
- `2026-05-05` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24050 passes 70% balance rule.
- `2026-05-08` (Friday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24200 passes 70% balance rule.
- `2026-05-11` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23900 passes 70% balance rule.
- `2026-05-12` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23750 passes 70% balance rule.
- `2026-06-05` (Friday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23450 passes 70% balance rule.
- `2026-06-08` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23150 passes 70% balance rule.
- `2026-06-09` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23250 passes 70% balance rule.
- `2026-06-19` (Friday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24000 passes 70% balance rule.
- `2026-03-18` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=76500 passes 70% balance rule.
- `2026-03-19` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=75100 passes 70% balance rule.
- `2026-03-25` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=74800 passes 70% balance rule.
- `2026-04-01` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=73800 passes 70% balance rule.
- `2026-04-02` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=71700 passes 70% balance rule.
- `2026-04-08` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77300 passes 70% balance rule.
- `2026-04-09` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77300 passes 70% balance rule.
- `2026-04-15` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=78100 passes 70% balance rule.
- `2026-04-16` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=78700 passes 70% balance rule.
- `2026-04-22` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=78900 passes 70% balance rule.
- `2026-04-23` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77900 passes 70% balance rule.
- `2026-05-06` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77400 passes 70% balance rule.
- `2026-05-07` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77900 passes 70% balance rule.
- `2026-05-13` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=74600 passes 70% balance rule.
- `2026-05-14` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=75000 passes 70% balance rule.
- `2026-05-21` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=75600 passes 70% balance rule.

## Remarks

- Strike search: ATM first, then ATM±1, ATM±2, … until balance ratio ≥ threshold.
- Both legs managed independently; one SL hit does not exit the other.
- gap_sl  : option opens at/above SL → filled at candle open.
- sl      : option high touches SL price → filled at SL.
- SL monitoring uses 1-minute option candles.
- chosen_strike and strike_offset columns in the CSV show how far from ATM we went.
- CAGR computed on notional capital via --capital arg.
- Max drawdown = largest peak-to-trough drop in running cumulative equity.
