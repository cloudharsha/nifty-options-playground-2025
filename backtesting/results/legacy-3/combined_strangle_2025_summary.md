# Combined Short Strangle — NIFTY Mon/Tue/Fri + SENSEX Wed/Thu (Sep 2025+)

## Strategy Details

- Period: `2025-09-01` → latest available data
- Entry: `09:20` — sell OTM CE + OTM PE
- Exit: `15:20` — day close if SL not hit
- Expiry: current-week, traded even on expiry day (no roll)
- No balance filter — pair selected by minimum price difference

| Day | Index | OTM Price Range | Qty |
|-----|-------|-----------------|-----|
| Monday    | NIFTY  | ₹7 – ₹15  | ~300 |
| Tuesday   | NIFTY  | ₹5 – ₹10  | ~300 |
| Wednesday | SENSEX | ₹30 – ₹50 | 100  |
| Thursday  | SENSEX | ₹15 – ₹40 | 100  |
| Friday    | NIFTY  | ₹10 – ₹20 | ~300 |

**Pair selection:** among all OTM CE (above ATM) and OTM PE (below ATM) with entry price in the day's range, choose the pair with minimum |CE_price − PE_price|. On ties, prefer lowest total premium.

- Slippage: 0.50 pt/order (2× per leg)
- Brokerage: ₹25.00/order → ₹100.00/straddle
- Notional capital for CAGR: ₹500,000
- Traded days found: `153`  Skipped: `44`

---

## SL Level Comparison

| SL % | NIFTY Net P/L | NIFTY Win% | NIFTY Drawdown | SENSEX Net P/L | SENSEX Win% | SENSEX Drawdown | Combined Net P/L | Combined Win% | Combined CAGR |
|------|---------------|------------|----------------|----------------|-------------|----------------|------------------|---------------|---------------|
| **20%** | `₹-29348.75` | `47.5%` | `₹36662.25` | `₹4776.00` | `51.9%` | `₹12376.00` | `₹-24572.75` | `49.0%` | `-6.2%` |
| 30% | `₹-47342.44` | `44.4%` | `₹51981.19` | `₹18266.50` | `68.5%` | `₹7041.50` | `₹-29075.94` | `52.9%` | `-7.3%` |
| 40% | `₹-40928.00` | `50.5%` | `₹45566.75` | `₹14450.00` | `68.5%` | `₹9823.00` | `₹-26478.00` | `56.9%` | `-6.7%` |
| 50% | `₹-37758.13` | `47.5%` | `₹42396.88` | `₹10402.50` | `64.8%` | `₹9992.50` | `₹-27355.63` | `53.6%` | `-6.9%` |
| **60%** | `₹-37884.50` | `48.5%` | `₹42523.25` | `₹14525.00` | `61.1%` | `₹8100.00` | `₹-23359.50` | `52.9%` | `-5.9%` |
| 70% | `₹-45581.74` | `38.4%` | `₹50220.49` | `₹21874.50` | `57.4%` | `₹9303.50` | `₹-23707.24` | `45.1%` | `-6.0%` |
| **80%** | `₹-36420.25` | `38.4%` | `₹47022.00` | `₹13448.00` | `53.7%` | `₹11664.00` | `₹-22972.25` | `43.8%` | `-5.8%` |
| **90%** | `₹-31545.23` | `42.4%` | `₹49424.98` | `₹10535.50` | `38.9%` | `₹14996.50` | `₹-21009.73` | `41.2%` | `-5.3%` |
| 100% | `₹-29100.00` | `44.4%` | `₹52611.25` | `₹5350.00` | `33.3%` | `₹16755.00` | `₹-23750.00` | `40.5%` | `-6.0%` |

_Bold row = best combined Net P/L (SL 90%)_

---

## Day-of-Week P&L by SL Level

| SL % | Monday (N) | Tuesday (N) | Wednesday (S) | Thursday (S) | Friday (N) |
|------|------------|-------------|---------------|--------------|------------|
| 20% | `₹-362.49` | `₹202.88` | `₹161.04` | `₹10.27` | `₹-729.74` |
| 30% | `₹-445.03` | `₹81.95` | `₹234.61` | `₹449.90` | `₹-1071.54` |
| 40% | `₹-404.22` | `₹400.30` | `₹122.04` | `₹424.35` | `₹-1236.33` |
| 50% | `₹-377.27` | `₹562.52` | `₹86.52` | `₹306.92` | `₹-1329.43` |
| 60% | `₹-375.30` | `₹356.67` | `₹92.71` | `₹458.81` | `₹-1129.39` |
| 70% | `₹-596.90` | `₹489.55` | `₹101.32` | `₹732.21` | `₹-1273.92` |
| 80% | `₹-698.50` | `₹837.89` | `₹-28.61` | `₹548.04` | `₹-1243.04` |
| 90% | `₹-726.57` | `₹1259.74` | `₹-205.34` | `₹626.35` | `₹-1489.09` |
| 100% | `₹-698.22` | `₹1438.86` | `₹-468.93` | `₹710.77` | `₹-1622.46` |

_(N) = NIFTY  (S) = SENSEX  Values are avg net P/L per traded day_

---

## Monthly P&L by SL Level (Combined)

| Month | SL 20% | SL 30% | SL 40% | SL 50% | SL 60% | SL 70% | SL 80% | SL 90% | SL 100% |
|-------|------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | -------|
| 2025-09 | `₹-1370.00` | `₹3154.50` | `₹3754.00` | `₹3817.50` | `₹2575.00` | `₹1635.00` | `₹1872.00` | `₹1134.00` | `₹4125.00` |
| 2025-10 | `₹-3664.00` | `₹-2070.50` | `₹-1334.00` | `₹-4462.50` | `₹-3988.00` | `₹-4149.00` | `₹-1849.00` | `₹1759.00` | `₹1840.00` |
| 2025-11 | `₹5111.00` | `₹98.00` | `₹683.00` | `₹-2230.00` | `₹6168.00` | `₹5708.00` | `₹6999.00` | `₹11868.00` | `₹16635.00` |
| 2025-12 | `₹-3352.00` | `₹-1603.50` | `₹8395.00` | `₹10837.50` | `₹6509.00` | `₹13480.00` | `₹14786.00` | `₹11283.00` | `₹7780.00` |
| 2026-01 | `₹-13289.75` | `₹-5899.76` | `₹-6414.50` | `₹-3375.00` | `₹-7696.75` | `₹-14334.13` | `₹-14699.75` | `₹-16547.74` | `₹-22081.25` |
| 2026-02 | `₹-4527.50` | `₹-8673.52` | `₹-13595.00` | `₹-12225.01` | `₹-10081.00` | `₹-7858.13` | `₹-8474.75` | `₹-9670.74` | `₹-13298.75` |
| 2026-03 | `₹-4706.50` | `₹-10037.27` | `₹-9052.50` | `₹-5683.75` | `₹-5760.75` | `₹-5784.50` | `₹-9328.00` | `₹-9795.37` | `₹-8875.00` |
| 2026-04 | `₹-1358.75` | `₹-3080.00` | `₹-4801.25` | `₹-6522.50` | `₹-8243.75` | `₹-6019.50` | `₹-2349.00` | `₹-669.50` | `₹-1715.00` |
| 2026-05 | `₹-429.75` | `₹-1408.76` | `₹-1988.00` | `₹-2817.50` | `₹649.50` | `₹-734.11` | `₹-2117.75` | `₹-399.25` | `₹3971.25` |
| 2026-06 | `₹3014.50` | `₹444.87` | `₹-2124.75` | `₹-4694.37` | `₹-3490.75` | `₹-5650.87` | `₹-7811.00` | `₹-9971.13` | `₹-12131.25` |

---

## Detailed Monthly Breakdown — Best SL (90%)

### Combined (All 5 days)

| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |
|-------|--------|-----|------|---------|---------|------------|
| 2025-09 | 22 | 9 | 13 | `₹1134.00` | `₹51.55` | `₹1134.00` |
| 2025-10 | 20 | 10 | 10 | `₹1759.00` | `₹87.95` | `₹2893.00` |
| 2025-11 | 19 | 9 | 10 | `₹11868.00` | `₹624.63` | `₹14761.00` |
| 2025-12 | 22 | 11 | 11 | `₹11283.00` | `₹512.86` | `₹26044.00` |
| 2026-01 | 20 | 8 | 12 | `₹-16547.74` | `₹-827.39` | `₹9496.26` |
| 2026-02 | 20 | 7 | 13 | `₹-9670.74` | `₹-483.54` | `₹-174.48` |
| 2026-03 | 11 | 2 | 9 | `₹-9795.37` | `₹-890.49` | `₹-9969.85` |
| 2026-04 | 5 | 2 | 3 | `₹-669.50` | `₹-133.90` | `₹-10639.35` |
| 2026-05 | 8 | 4 | 4 | `₹-399.25` | `₹-49.91` | `₹-11038.60` |
| 2026-06 | 6 | 1 | 5 | `₹-9971.13` | `₹-1661.86` | `₹-21009.73` |

### NIFTY only (Mon/Tue/Fri)

| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |
|-------|--------|-----|------|---------|---------|------------|
| 2025-09 | 14 | 5 | 9 | `₹-9728.00` | `₹-694.86` | `₹-9728.00` |
| 2025-10 | 12 | 5 | 7 | `₹-7578.00` | `₹-631.50` | `₹-17306.00` |
| 2025-11 | 12 | 9 | 3 | `₹19510.50` | `₹1625.88` | `₹2204.50` |
| 2025-12 | 14 | 8 | 6 | `₹8822.50` | `₹630.18` | `₹11027.00` |
| 2026-01 | 12 | 3 | 9 | `₹-17199.74` | `₹-1433.31` | `₹-6172.74` |
| 2026-02 | 12 | 4 | 8 | `₹-11044.24` | `₹-920.35` | `₹-17216.98` |
| 2026-03 | 8 | 1 | 7 | `₹-12946.87` | `₹-1618.36` | `₹-30163.85` |
| 2026-04 | 3 | 2 | 1 | `₹1955.50` | `₹651.83` | `₹-28208.35` |
| 2026-05 | 7 | 4 | 3 | `₹362.75` | `₹51.82` | `₹-27845.60` |
| 2026-06 | 5 | 1 | 4 | `₹-3699.63` | `₹-739.93` | `₹-31545.23` |

### SENSEX only (Wed/Thu)

| Month | Trades | Win | Loss | Net P/L | Avg/Day | Cumulative |
|-------|--------|-----|------|---------|---------|------------|
| 2025-09 | 8 | 4 | 4 | `₹10862.00` | `₹1357.75` | `₹10862.00` |
| 2025-10 | 8 | 5 | 3 | `₹9337.00` | `₹1167.12` | `₹20199.00` |
| 2025-11 | 7 | 0 | 7 | `₹-7642.50` | `₹-1091.79` | `₹12556.50` |
| 2025-12 | 8 | 3 | 5 | `₹2460.50` | `₹307.56` | `₹15017.00` |
| 2026-01 | 8 | 5 | 3 | `₹652.00` | `₹81.50` | `₹15669.00` |
| 2026-02 | 8 | 3 | 5 | `₹1373.50` | `₹171.69` | `₹17042.50` |
| 2026-03 | 3 | 1 | 2 | `₹3151.50` | `₹1050.50` | `₹20194.00` |
| 2026-04 | 2 | 0 | 2 | `₹-2625.00` | `₹-1312.50` | `₹17569.00` |
| 2026-05 | 1 | 0 | 1 | `₹-762.00` | `₹-762.00` | `₹16807.00` |
| 2026-06 | 1 | 0 | 1 | `₹-6271.50` | `₹-6271.50` | `₹10535.50` |

---

## Entry Price Overview (Sample — first 20 trades)

| Date | Day | Index | ATM | CE Strike | CE Price | PE Strike | PE Price | Diff |
|------|-----|-------|-----|-----------|----------|-----------|----------|------|
| 2025-09-01 | Mon | NIFTY | 24500 | 24800 | `8.85` | 24250 | `7.55` | `1.30` |
| 2025-09-02 | Tue | NIFTY | 24650 | 24800 | `6.60` | 24500 | `6.20` | `0.40` |
| 2025-09-03 | Wed | SENSEX | 80000 | 80900 | `33.05` | 79300 | `36.30` | `3.25` |
| 2025-09-04 | Thu | SENSEX | 81100 | 82000 | `16.90` | 80300 | `16.35` | `0.55` |
| 2025-09-05 | Fri | NIFTY | 24850 | 25150 | `10.90` | 24500 | `10.65` | `0.25` |
| 2025-09-08 | Mon | NIFTY | 24800 | 25050 | `7.90` | 24500 | `8.40` | `0.50` |
| 2025-09-09 | Tue | NIFTY | 24850 | 25000 | `8.40` | 24700 | `9.25` | `0.85` |
| 2025-09-10 | Wed | SENSEX | 81400 | 82000 | `40.30` | 80700 | `37.05` | `3.25` |
| 2025-09-11 | Thu | SENSEX | 81500 | 82100 | `19.45` | 80900 | `19.20` | `0.25` |
| 2025-09-12 | Fri | NIFTY | 25050 | 25350 | `10.70` | 24750 | `10.15` | `0.55` |
| 2025-09-15 | Mon | NIFTY | 25100 | 25300 | `9.10` | 24850 | `8.45` | `0.65` |
| 2025-09-16 | Tue | NIFTY | 25100 | 25250 | `5.05` | 24950 | `6.15` | `1.10` |
| 2025-09-17 | Wed | SENSEX | 82600 | 83200 | `38.45` | 81900 | `40.95` | `2.50` |
| 2025-09-18 | Thu | SENSEX | 83000 | 83400 | `24.65` | 82600 | `24.15` | `0.50` |
| 2025-09-19 | Fri | NIFTY | 25400 | 25600 | `13.50` | 25150 | `14.90` | `1.40` |
| 2025-09-22 | Mon | NIFTY | 25250 | 25500 | `8.20` | 25050 | `9.60` | `1.40` |
| 2025-09-23 | Tue | NIFTY | 25200 | 25400 | `6.05` | 25100 | `7.20` | `1.15` |
| 2025-09-24 | Wed | SENSEX | 81900 | 82500 | `44.90` | 81300 | `44.60` | `0.30` |
| 2025-09-25 | Thu | SENSEX | 81700 | 82300 | `20.00` | 81100 | `17.35` | `2.65` |
| 2025-09-26 | Fri | NIFTY | 24800 | 25200 | `11.80` | 24500 | `11.10` | `0.70` |

---

## Skip Reason Summary

- `SENSEX:no_strangle_pair`: 23
- `NIFTY:no_strangle_pair`: 20
- `NIFTY:missing_spot_entry`: 1

## First 20 Skipped Days

- `2025-10-21` (Tuesday) [NIFTY]: `missing_spot_entry` — No NIFTY spot at 2025-10-21T09:20:00+05:30.
- `2026-03-04` (Wednesday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [30,50] within 25 strikes of ATM=78700.
- `2026-03-09` (Monday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [7,15] within 25 strikes of ATM=23800.
- `2026-03-18` (Wednesday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [30,50] within 25 strikes of ATM=76500.
- `2026-03-19` (Thursday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [15,40] within 25 strikes of ATM=75100.
- `2026-03-20` (Friday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [10,20] within 25 strikes of ATM=23300.
- `2026-03-25` (Wednesday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [30,50] within 25 strikes of ATM=74800.
- `2026-03-27` (Friday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [10,20] within 25 strikes of ATM=23050.
- `2026-03-30` (Monday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [7,15] within 25 strikes of ATM=22500.
- `2026-04-01` (Wednesday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [30,50] within 25 strikes of ATM=73800.
- `2026-04-02` (Thursday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [15,40] within 25 strikes of ATM=71700.
- `2026-04-06` (Monday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [7,15] within 25 strikes of ATM=22650.
- `2026-04-07` (Tuesday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [5,10] within 25 strikes of ATM=22750.
- `2026-04-08` (Wednesday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [30,50] within 25 strikes of ATM=77300.
- `2026-04-09` (Thursday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [15,40] within 25 strikes of ATM=77300.
- `2026-04-10` (Friday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [10,20] within 25 strikes of ATM=23950.
- `2026-04-13` (Monday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [7,15] within 25 strikes of ATM=23600.
- `2026-04-15` (Wednesday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [30,50] within 25 strikes of ATM=78100.
- `2026-04-16` (Thursday) [SENSEX]: `no_strangle_pair` — No balanced OTM pair found in [15,40] within 25 strikes of ATM=78700.
- `2026-04-17` (Friday) [NIFTY]: `no_strangle_pair` — No balanced OTM pair found in [10,20] within 25 strikes of ATM=24200.

## Remarks

- Strangle: sell OTM CE (above ATM) + OTM PE (below ATM), independent SL per leg.
- Pair chosen to minimise |CE_price − PE_price|; cheapest total on ties.
- Early stop in OTM scan: if price drops below range floor, scan stops (cheaper strikes skipped).
- gap_sl  : option opens at/above SL → filled at candle open.
- sl      : option high touches SL → filled at SL price.
- SL monitoring uses 1-minute option candles.
- All 9 SL scenarios share the same entry; only exit differs.
- CAGR computed on notional capital via --capital arg.
