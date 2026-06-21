# Combined NIFTY + SENSEX — Balanced-Strike ATM Straddle, Multi-SL (Sep 2025+)

## Strategy Details

- Period: `2025-09-01` → latest available data
- Entry: `09:20` | Exit: `15:20`
- Stop loss: tested from 20% to 100% in 10% steps (independent per leg)
- Expiry: current-week, **traded even on expiry day itself** (no roll)
- Balanced-strike search: ATM → ATM±1 … ±5
  until `min(CE,PE)/max(CE,PE) ≥ 70%`.
  If none found → day skipped.
- **Monday / Tuesday / Friday** → NIFTY weekly options (~300 qty)
- **Wednesday / Thursday**       → SENSEX weekly options (100 qty)
- Slippage: 0.50 pt/order (2× per leg)
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Notional capital for CAGR: ₹500,000
- Traded days: `161` (at ATM: `133` | adjusted strike: `28`) | Skipped: `36`

---

## SL Level Comparison

| SL % | NIFTY Net P/L | NIFTY Win% | NIFTY Drawdown | SENSEX Net P/L | SENSEX Win% | SENSEX Drawdown | Combined Net P/L | Combined Win% | Combined CAGR |
|------|---------------|------------|----------------|----------------|-------------|----------------|------------------|---------------|---------------|
| **20%** | `₹-70667.45` | `48.1%` | `₹106210.95` | `₹47714.20` | `47.3%` | `₹86167.80` | `₹-22953.25` | `47.8%` | `-5.8%` |
| 30% | `₹-116377.49` | `53.8%` | `₹188258.03` | `₹-60747.70` | `52.7%` | `₹137070.20` | `₹-177125.19` | `53.4%` | `-42.6%` |
| 40% | `₹-93994.65` | `60.4%` | `₹148886.50` | `₹-34025.00` | `60.0%` | `₹117455.00` | `₹-128019.65` | `60.2%` | `-31.3%` |
| **50%** | `₹23702.01` | `61.3%` | `₹157613.13` | `₹-13341.00` | `65.5%` | `₹101031.00` | `₹10361.01` | `62.7%` | `2.6%` |
| 60% | `₹14031.15` | `61.3%` | `₹207271.75` | `₹-78863.00` | `63.6%` | `₹120646.00` | `₹-64831.85` | `62.1%` | `-16.1%` |
| 70% | `₹-94988.91` | `58.5%` | `₹185208.73` | `₹-110764.00` | `63.6%` | `₹168929.50` | `₹-205752.91` | `60.2%` | `-49.0%` |
| 80% | `₹-51335.40` | `55.7%` | `₹229810.00` | `₹-169078.00` | `61.8%` | `₹229452.00` | `₹-220413.40` | `57.8%` | `-52.2%` |
| 90% | `₹-35313.95` | `54.7%` | `₹190707.62` | `₹-138019.00` | `49.1%` | `₹217131.50` | `₹-173332.95` | `52.8%` | `-41.7%` |
| 100% | `₹-33838.75` | `52.8%` | `₹131495.00` | `₹-113186.00` | `45.5%` | `₹175720.00` | `₹-147024.75` | `50.3%` | `-35.7%` |

_Bold = best combined Net P/L (SL 50%)_

---

## Day-of-Week Avg Net P/L by SL Level

| SL % | Monday (N) | Tuesday (N) | Wednesday (S) | Thursday (S) | Friday (N) |
|------|------------|-------------|---------------|--------------|------------|
| 20% | `₹-196.94` | `₹415.31` | `₹2090.83` | `₹-496.92` | `₹-2072.18` |
| 30% | `₹-667.43` | `₹-654.65` | `₹-1063.31` | `₹-1150.45` | `₹-1911.73` |
| 40% | `₹-610.89` | `₹301.33` | `₹-846.83` | `₹-364.12` | `₹-2190.11` |
| 50% | `₹-36.89` | `₹3149.75` | `₹-77.76` | `₹-426.38` | `₹-2046.62` |
| 60% | `₹-1319.33` | `₹3247.89` | `₹-1045.52` | `₹-1867.04` | `₹-1110.43` |
| 70% | `₹-816.34` | `₹1279.91` | `₹-2567.34` | `₹-1396.58` | `₹-2857.88` |
| 80% | `₹-1016.63` | `₹3157.17` | `₹-2722.83` | `₹-3466.00` | `₹-3101.34` |
| 90% | `₹-1500.78` | `₹5724.93` | `₹-3195.74` | `₹-1743.94` | `₹-4404.94` |
| 100% | `₹91.32` | `₹5055.08` | `₹-677.41` | `₹-3597.73` | `₹-5377.84` |

_(N)=NIFTY  (S)=SENSEX  avg net P/L per traded day_

---

## Monthly Net P/L by SL Level (Combined)

| Month | SL 20% | SL 30% | SL 40% | SL 50% | SL 60% | SL 70% | SL 80% | SL 90% | SL 100% |
|-------|------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | -------|
| 2025-09 | `₹18135.00` | `₹2891.00` | `₹-9214.00` | `₹10615.00` | `₹1551.00` | `₹5852.50` | `₹60653.00` | `₹74794.50` | `₹60565.00` |
| 2025-10 | `₹-1179.00` | `₹-45805.50` | `₹-14021.00` | `₹-7435.00` | `₹-10497.00` | `₹-35317.00` | `₹-35117.00` | `₹-30068.00` | `₹-46220.00` |
| 2025-11 | `₹23478.00` | `₹62249.00` | `₹52838.00` | `₹20255.00` | `₹26651.00` | `₹27558.00` | `₹43020.00` | `₹56184.00` | `₹35620.00` |
| 2025-12 | `₹-38057.00` | `₹-25069.50` | `₹9815.00` | `₹18420.00` | `₹30969.00` | `₹14051.00` | `₹-14589.00` | `₹1757.50` | `₹1110.00` |
| 2026-01 | `₹-100432.00` | `₹-102625.27` | `₹-105800.65` | `₹-73091.50` | `₹-90481.35` | `₹-134076.19` | `₹-126094.40` | `₹-98829.71` | `₹-117727.25` |
| 2026-02 | `₹93789.25` | `₹47240.12` | `₹42258.00` | `₹188223.76` | `₹151184.00` | `₹114144.26` | `₹114441.75` | `₹85300.88` | `₹75791.25` |
| 2026-03 | `₹24287.25` | `₹-47031.39` | `₹-57513.25` | `₹-107379.38` | `₹-164797.75` | `₹-138538.37` | `₹-190233.50` | `₹-144301.88` | `₹-43087.50` |
| 2026-04 | `₹-17535.00` | `₹-67630.13` | `₹-36270.50` | `₹-52216.26` | `₹-68162.00` | `₹-84107.74` | `₹-69841.50` | `₹-84106.99` | `₹-98372.50` |
| 2026-05 | `₹-10052.75` | `₹18697.99` | `₹31033.00` | `₹41908.76` | `₹57172.00` | `₹40024.63` | `₹29614.50` | `₹15127.25` | `₹640.00` |
| 2026-06 | `₹-15387.00` | `₹-20041.51` | `₹-41144.25` | `₹-28939.37` | `₹1579.25` | `₹-15344.00` | `₹-32267.25` | `₹-49190.50` | `₹-15343.75` |

---

## Detailed Breakdown — Best SL (50%)

### Combined (NIFTY + SENSEX)

| Metric | Value |
|--------|-------|
| Traded days | `161` |
| Win / Loss | `101` / `60` |
| Win rate | `62.7%` |
| CE SL hit | `72` | PE SL hit | `79` | Both | `26` |
| **Net P/L** | **`₹10361.01`** |
| Max cumulative profit | `₹156987.26` |
| Max drawdown | `₹175692.50` |
| **CAGR** (on ₹500,000) | **`2.64%`** |
| Best day  | `2026-02-03` (Tuesday) `₹76551.25` |
| Worst day | `2026-03-16` (Monday) `₹-57397.50` |

| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |
|-------|--------|-----|------|---------|---------|------------|
| 2025-09 | 20 | 12 | 8 | `₹10615.00` | `₹530.75` | `₹10615.00` |
| 2025-10 | 19 | 11 | 8 | `₹-7435.00` | `₹-391.32` | `₹3180.00` |
| 2025-11 | 19 | 12 | 7 | `₹20255.00` | `₹1066.05` | `₹23435.00` |
| 2025-12 | 22 | 15 | 7 | `₹18420.00` | `₹837.27` | `₹41855.00` |
| 2026-01 | 20 | 11 | 9 | `₹-73091.50` | `₹-3654.57` | `₹-31236.50` |
| 2026-02 | 19 | 16 | 3 | `₹188223.76` | `₹9906.51` | `₹156987.26` |
| 2026-03 | 16 | 8 | 8 | `₹-107379.38` | `₹-6711.21` | `₹49607.88` |
| 2026-04 | 12 | 5 | 7 | `₹-52216.26` | `₹-4351.36` | `₹-2608.38` |
| 2026-05 | 8 | 7 | 1 | `₹41908.76` | `₹5238.60` | `₹39300.38` |
| 2026-06 | 6 | 4 | 2 | `₹-28939.37` | `₹-4823.23` | `₹10361.01` |

### NIFTY only (Mon/Tue/Fri)

| Metric | Value |
|--------|-------|
| Traded days | `106` |
| Win / Loss | `65` / `41` |
| Win rate | `61.3%` |
| CE SL hit | `43` | PE SL hit | `47` | Both | `15` |
| **Net P/L** | **`₹23702.01`** |
| Max cumulative profit | `₹142200.76` |
| Max drawdown | `₹157613.13` |
| **CAGR** (on ₹500,000) | **`6.05%`** |
| Best day  | `2026-02-03` (Tuesday) `₹76551.25` |
| Worst day | `2026-03-16` (Monday) `₹-57397.50` |

| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |
|-------|--------|-----|------|---------|---------|------------|
| 2025-09 | 12 | 6 | 6 | `₹-18847.50` | `₹-1570.62` | `₹-18847.50` |
| 2025-10 | 11 | 4 | 7 | `₹-22055.00` | `₹-2005.00` | `₹-40902.50` |
| 2025-11 | 12 | 7 | 5 | `₹20250.00` | `₹1687.50` | `₹-20652.50` |
| 2025-12 | 14 | 11 | 3 | `₹30827.50` | `₹2201.96` | `₹10175.00` |
| 2026-01 | 12 | 8 | 4 | `₹-9208.00` | `₹-767.33` | `₹967.00` |
| 2026-02 | 11 | 9 | 2 | `₹141233.76` | `₹12839.43` | `₹142200.76` |
| 2026-03 | 12 | 5 | 7 | `₹-127746.88` | `₹-10645.57` | `₹14453.88` |
| 2026-04 | 10 | 5 | 5 | `₹-29551.26` | `₹-2955.13` | `₹-15097.38` |
| 2026-05 | 7 | 6 | 1 | `₹30386.26` | `₹4340.89` | `₹15288.88` |
| 2026-06 | 5 | 4 | 1 | `₹8413.13` | `₹1682.63` | `₹23702.01` |

### SENSEX only (Wed/Thu)

| Metric | Value |
|--------|-------|
| Traded days | `55` |
| Win / Loss | `36` / `19` |
| Win rate | `65.5%` |
| CE SL hit | `29` | PE SL hit | `32` | Both | `11` |
| **Net P/L** | **`₹-13341.00`** |
| Max cumulative profit | `₹68827.50` |
| Max drawdown | `₹101031.00` |
| **CAGR** (on ₹500,000) | **`-3.55%`** |
| Best day  | `2025-09-11` (Thursday) `₹25060.00` |
| Worst day | `2026-06-03` (Wednesday) `₹-37352.50` |

| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |
|-------|--------|-----|------|---------|---------|------------|
| 2025-09 | 8 | 6 | 2 | `₹29462.50` | `₹3682.81` | `₹29462.50` |
| 2025-10 | 8 | 7 | 1 | `₹14620.00` | `₹1827.50` | `₹44082.50` |
| 2025-11 | 7 | 5 | 2 | `₹5.00` | `₹0.71` | `₹44087.50` |
| 2025-12 | 8 | 4 | 4 | `₹-12407.50` | `₹-1550.94` | `₹31680.00` |
| 2026-01 | 8 | 3 | 5 | `₹-63883.50` | `₹-7985.44` | `₹-32203.50` |
| 2026-02 | 8 | 7 | 1 | `₹46990.00` | `₹5873.75` | `₹14786.50` |
| 2026-03 | 4 | 3 | 1 | `₹20367.50` | `₹5091.88` | `₹35154.00` |
| 2026-04 | 2 | 0 | 2 | `₹-22665.00` | `₹-11332.50` | `₹12489.00` |
| 2026-05 | 1 | 1 | 0 | `₹11522.50` | `₹11522.50` | `₹24011.50` |
| 2026-06 | 1 | 0 | 1 | `₹-37352.50` | `₹-37352.50` | `₹-13341.00` |

---

## Strike Offset Analysis (entry data — SL-independent)

| Offset | Trades | Index breakdown |
|--------|--------|-----------------|
| ATM (0) | 133 | NIFTY: 84  SENSEX: 49 |
| ±1 | 26 | NIFTY: 21  SENSEX: 5 |
| ±2 | 2 | NIFTY: 1  SENSEX: 1 |

---

## Skip Reason Summary

- `SENSEX:no_balanced_strike`: 22
- `NIFTY:no_balanced_strike`: 13
- `NIFTY:missing_spot_entry`: 1

## First 30 Skipped Days

- `2025-09-02` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24650 passes 70% balance rule.
- `2025-09-30` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24700 passes 70% balance rule.
- `2025-10-20` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=25900 passes 70% balance rule.
- `2025-10-21` (Tuesday) [NIFTY]: `missing_spot_entry` — No NIFTY spot at 2025-10-21T09:20:00+05:30.
- `2026-02-10` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=25900 passes 70% balance rule.
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
- `2026-05-04` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24200 passes 70% balance rule.
- `2026-05-05` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24050 passes 70% balance rule.
- `2026-05-06` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77400 passes 70% balance rule.
- `2026-05-07` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=77900 passes 70% balance rule.
- `2026-05-08` (Friday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=24200 passes 70% balance rule.
- `2026-05-11` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23900 passes 70% balance rule.
- `2026-05-12` (Tuesday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23750 passes 70% balance rule.
- `2026-05-13` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=74600 passes 70% balance rule.
- `2026-05-14` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=75000 passes 70% balance rule.
- `2026-05-21` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=75600 passes 70% balance rule.
- `2026-05-27` (Wednesday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=76000 passes 70% balance rule.
- `2026-06-04` (Thursday) [SENSEX]: `no_balanced_strike` — No strike within 5 of ATM=74100 passes 70% balance rule.
- `2026-06-05` (Friday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23450 passes 70% balance rule.
- `2026-06-08` (Monday) [NIFTY]: `no_balanced_strike` — No strike within 5 of ATM=23150 passes 70% balance rule.

## Remarks

- Strike search: ATM first, then ATM±1, ±2… until balance ratio ≥ threshold.
- Both legs managed independently; one SL hit does not exit the other.
- gap_sl  : option opens at/above SL → filled at candle open.
- sl      : option high touches SL → filled at SL price.
- SL monitoring uses 1-minute option candles.
- All 9 SL scenarios share the same entry; only the exit logic differs.
- CSV column sl_pct identifies the scenario for each row.
- CAGR computed on notional capital via --capital arg.
- Max drawdown = largest peak-to-trough drop in running cumulative equity.
