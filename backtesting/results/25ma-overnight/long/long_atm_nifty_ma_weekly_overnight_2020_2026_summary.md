# Overnight Weekly Long ATM NIFTY 25-SMA Backtest (2020–2026)

## Strategy Details

- Signal source: NIFTY 15-minute close
- Signal bar time: `15:15` row as `15:30` close proxy
- MA rule: 25-SMA of spot closes including the signal bar
- Direction rule: above SMA -> buy ATM CE; below SMA -> buy ATM PE; equal -> no trade
- Entry execution time: `15:29` option open
- Exit execution time: next trading day `09:16` option open
- Expiry rule: first weekly expiry strictly after entry date
- ATM rule: nearest 50 using the spot signal close
- Quantity: ~300 per trade (dynamic lot sizing by expiry era)
  - pre-2021-10-07: 75 × 4 = 300 | 2021-10-07–2024-04-25: 50 × 6 = 300
  - 2024-04-26–2024-11-21: 25 × 12 = 300 | 2024-11-22–2025-12-30: 75 × 4 = 300
  - 2026+: 65 × 5 = 325
- Slippage: 1.00 pt/order
- Brokerage: Rs 25/order → Rs 50/trade
- Capital reference (CAGR): Rs 500,000

## Overall Results

- Traded days: `1312`
- Skipped days: `539`
- CE-buy count: `673`
- PE-buy count: `639`
- Winning days: `604`
- Losing days: `708`
- Win rate: `46.0%`
- Net P/L: `330944.00`
- Total Brokerage: `65600.00`
- Gross P/L: `396544.00`
- Max drawdown: `568615.00`
- CAGR (on Rs 500,000): `7.04%`
- Best day: `2026-02-02` net `172606.25`
- Worst day: `2020-03-20` net `-91325.00`
- Data range: `2019-01-01` to `2026-06-19`

## Yearly Summary

| Year | Traded | Wins | Losses | Win% | Net P/L |
|------|--------|------|--------|------|---------|
| 2020 | 195 | 87 | 108 | 44.6% | -277125.00 |
| 2021 | 194 | 89 | 105 | 45.9% | -157660.00 |
| 2022 | 194 | 94 | 100 | 48.5% | 179225.00 |
| 2023 | 189 | 88 | 101 | 46.6% | 675.00 |
| 2024 | 195 | 95 | 100 | 48.7% | -48015.00 |
| 2025 | 247 | 110 | 137 | 44.5% | 300516.50 |
| 2026 | 98 | 41 | 57 | 41.8% | 333327.50 |

## Monthly P/L

| Month | Traded | Win% | Net P/L |
|-------|--------|------|---------|
| 2020-01 | 18 | 44.4% | 18510.00 |
| 2020-02 | 16 | 56.2% | -8450.00 |
| 2020-03 | 16 | 18.8% | -285425.00 |
| 2020-04 | 12 | 33.3% | -53235.00 |
| 2020-05 | 15 | 40.0% | 19095.00 |
| 2020-06 | 18 | 38.9% | 15735.00 |
| 2020-07 | 18 | 50.0% | -3885.00 |
| 2020-08 | 17 | 52.9% | 21740.00 |
| 2020-09 | 18 | 50.0% | -10545.00 |
| 2020-10 | 16 | 56.2% | 15145.00 |
| 2020-11 | 14 | 57.1% | 58250.00 |
| 2020-12 | 17 | 35.3% | -64060.00 |
| 2021-01 | 16 | 37.5% | -36515.00 |
| 2021-02 | 15 | 40.0% | -54945.00 |
| 2021-03 | 17 | 52.9% | -56560.00 |
| 2021-04 | 14 | 50.0% | 125990.00 |
| 2021-05 | 16 | 31.2% | -51170.00 |
| 2021-06 | 18 | 44.4% | -41610.00 |
| 2021-07 | 16 | 50.0% | -35390.00 |
| 2021-08 | 17 | 52.9% | 980.00 |
| 2021-09 | 16 | 37.5% | -7640.00 |
| 2021-10 | 16 | 43.8% | -42860.00 |
| 2021-11 | 15 | 40.0% | -31755.00 |
| 2021-12 | 18 | 66.7% | 73815.00 |
| 2022-01 | 16 | 50.0% | -45680.00 |
| 2022-02 | 16 | 62.5% | 184525.00 |
| 2022-03 | 16 | 56.2% | 79510.00 |
| 2022-04 | 15 | 66.7% | 67710.00 |
| 2022-05 | 17 | 29.4% | -87280.00 |
| 2022-06 | 17 | 47.1% | 17045.00 |
| 2022-07 | 17 | 41.2% | -1885.00 |
| 2022-08 | 16 | 62.5% | 107800.00 |
| 2022-09 | 17 | 47.1% | -48535.00 |
| 2022-10 | 13 | 53.8% | -28400.00 |
| 2022-11 | 17 | 35.3% | -53800.00 |
| 2022-12 | 17 | 35.3% | -11785.00 |
| 2023-01 | 17 | 41.2% | 125.00 |
| 2023-02 | 16 | 31.2% | 5905.00 |
| 2023-03 | 16 | 50.0% | -21320.00 |
| 2023-04 | 13 | 53.8% | -2495.00 |
| 2023-05 | 18 | 55.6% | 42990.00 |
| 2023-06 | 13 | 61.5% | 9700.00 |
| 2023-07 | 17 | 35.3% | -23860.00 |
| 2023-08 | 17 | 41.2% | 3455.00 |
| 2023-09 | 16 | 68.8% | 76150.00 |
| 2023-10 | 16 | 50.0% | -8660.00 |
| 2023-11 | 14 | 21.4% | -84025.00 |
| 2023-12 | 16 | 50.0% | 2710.00 |
| 2024-01 | 18 | 55.6% | 7995.00 |
| 2024-02 | 16 | 43.8% | -40340.00 |
| 2024-03 | 14 | 28.6% | -36010.00 |
| 2024-04 | 16 | 56.2% | 19375.00 |
| 2024-05 | 16 | 50.0% | 75610.00 |
| 2024-06 | 15 | 33.3% | -96705.00 |
| 2024-07 | 18 | 55.6% | 5700.00 |
| 2024-08 | 16 | 37.5% | -38630.00 |
| 2024-09 | 17 | 52.9% | -63835.00 |
| 2024-10 | 17 | 58.8% | -23530.00 |
| 2024-11 | 14 | 57.1% | 102380.00 |
| 2024-12 | 18 | 50.0% | 39975.00 |
| 2025-01 | 23 | 26.1% | -58525.00 |
| 2025-02 | 20 | 55.0% | 74933.00 |
| 2025-03 | 19 | 57.9% | 33358.00 |
| 2025-04 | 19 | 42.1% | 192400.00 |
| 2025-05 | 21 | 28.6% | 38043.00 |
| 2025-06 | 21 | 42.9% | 60090.00 |
| 2025-07 | 23 | 43.5% | 31685.00 |
| 2025-08 | 19 | 26.3% | -94820.00 |
| 2025-09 | 22 | 50.0% | -2945.00 |
| 2025-10 | 19 | 52.6% | 28480.00 |
| 2025-11 | 19 | 52.6% | -11030.00 |
| 2025-12 | 22 | 59.1% | 8847.50 |
| 2026-01 | 20 | 40.0% | -24452.00 |
| 2026-02 | 21 | 42.9% | 217385.75 |
| 2026-03 | 18 | 55.6% | 99963.75 |
| 2026-04 | 19 | 26.3% | 20207.50 |
| 2026-05 | 13 | 46.2% | 1072.50 |
| 2026-06 | 7 | 42.9% | 19150.00 |

## Exceptions

- `2019-01-01`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-01-02`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-01-03`: `missing_option_file`. Missing: NIFTY_10650_PE_02_JAN_20.csv
- `2019-01-04`: `missing_option_file`. Missing: NIFTY_10750_CE_02_JAN_20.csv
- `2019-01-07`: `missing_option_file`. Missing: NIFTY_10750_PE_02_JAN_20.csv
- `2019-01-08`: `missing_option_file`. Missing: NIFTY_10800_CE_02_JAN_20.csv
- `2019-01-09`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-01-10`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-01-11`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-01-14`: `missing_option_file`. Missing: NIFTY_10750_CE_02_JAN_20.csv
- `2019-01-15`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-01-16`: `missing_option_file`. Missing: NIFTY_10900_PE_02_JAN_20.csv
- `2019-01-17`: `missing_option_file`. Missing: NIFTY_10900_PE_02_JAN_20.csv
- `2019-01-18`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-01-21`: `missing_option_file`. Missing: NIFTY_10950_PE_02_JAN_20.csv
- `2019-01-22`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-01-23`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-01-24`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-01-25`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-01-28`: `missing_option_file`. Missing: NIFTY_10700_PE_02_JAN_20.csv
- `2019-01-29`: `missing_option_file`. Missing: NIFTY_10700_CE_02_JAN_20.csv
- `2019-01-30`: `missing_option_file`. Missing: NIFTY_10650_PE_02_JAN_20.csv
- `2019-01-31`: `missing_option_file`. Missing: NIFTY_10800_CE_02_JAN_20.csv
- `2019-02-01`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-02-04`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-02-05`: `missing_option_file`. Missing: NIFTY_10950_CE_02_JAN_20.csv
- `2019-02-06`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-02-07`: `missing_option_file`. Missing: NIFTY_11050_PE_02_JAN_20.csv
- `2019-02-08`: `missing_option_file`. Missing: NIFTY_10950_PE_02_JAN_20.csv
- `2019-02-11`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-02-12`: `missing_option_file`. Missing: NIFTY_10850_PE_02_JAN_20.csv
- `2019-02-13`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-02-14`: `missing_option_file`. Missing: NIFTY_10750_CE_02_JAN_20.csv
- `2019-02-15`: `missing_option_file`. Missing: NIFTY_10750_CE_02_JAN_20.csv
- `2019-02-18`: `missing_option_file`. Missing: NIFTY_10650_PE_02_JAN_20.csv
- `2019-02-19`: `missing_option_file`. Missing: NIFTY_10600_PE_02_JAN_20.csv
- `2019-02-20`: `missing_option_file`. Missing: NIFTY_10750_CE_02_JAN_20.csv
- `2019-02-21`: `missing_option_file`. Missing: NIFTY_10800_CE_02_JAN_20.csv
- `2019-02-22`: `missing_option_file`. Missing: NIFTY_10800_CE_02_JAN_20.csv
- `2019-02-25`: `missing_option_file`. Missing: NIFTY_10900_CE_02_JAN_20.csv
- `2019-02-26`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-02-27`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-02-28`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-03-01`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-03-05`: `missing_entry_or_exit_timestamp`. NIFTY_11000_CE_02_JAN_20.csv missing entry 2019-03-05T15:29:00+05:30; NIFTY_11000_CE_02_JAN_20.csv missing exit 2019-03-06T09:16:00+05:30
- `2019-03-06`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-03-07`: `missing_option_file`. Missing: NIFTY_11050_PE_02_JAN_20.csv
- `2019-03-08`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-03-11`: `missing_entry_or_exit_timestamp`. NIFTY_11200_CE_02_JAN_20.csv missing entry 2019-03-11T15:29:00+05:30; NIFTY_11200_CE_02_JAN_20.csv missing exit 2019-03-12T09:16:00+05:30
- `2019-03-12`: `missing_entry_or_exit_timestamp`. NIFTY_11300_CE_02_JAN_20.csv missing entry 2019-03-12T15:29:00+05:30; NIFTY_11300_CE_02_JAN_20.csv missing exit 2019-03-13T09:16:00+05:30
- `2019-03-13`: `missing_option_file`. Missing: NIFTY_11350_CE_02_JAN_20.csv
- `2019-03-14`: `missing_option_file`. Missing: NIFTY_11350_CE_02_JAN_20.csv
- `2019-03-15`: `missing_option_file`. Missing: NIFTY_11450_PE_02_JAN_20.csv
- `2019-03-18`: `missing_entry_or_exit_timestamp`. NIFTY_11500_CE_02_JAN_20.csv missing entry 2019-03-18T15:29:00+05:30; NIFTY_11500_CE_02_JAN_20.csv missing exit 2019-03-19T09:16:00+05:30
- `2019-03-19`: `missing_option_file`. Missing: NIFTY_11550_CE_02_JAN_20.csv
- `2019-03-20`: `missing_entry_or_exit_timestamp`. NIFTY_11500_PE_02_JAN_20.csv missing entry 2019-03-20T15:29:00+05:30; NIFTY_11500_PE_02_JAN_20.csv missing exit 2019-03-22T09:16:00+05:30
- `2019-03-22`: `missing_option_file`. Missing: NIFTY_11450_PE_02_JAN_20.csv
- `2019-03-25`: `missing_option_file`. Missing: NIFTY_11350_CE_02_JAN_20.csv
- `2019-03-26`: `missing_entry_or_exit_timestamp`. NIFTY_11500_CE_02_JAN_20.csv missing entry 2019-03-26T15:29:00+05:30; NIFTY_11500_CE_02_JAN_20.csv missing exit 2019-03-27T09:16:00+05:30
- `2019-03-27`: `missing_option_file`. Missing: NIFTY_11450_PE_02_JAN_20.csv
- `2019-03-28`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-03-28T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-03-29T09:16:00+05:30
- `2019-03-29`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-03-29T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-04-01T09:16:00+05:30
- `2019-04-01`: `missing_entry_or_exit_timestamp`. NIFTY_11650_PE_02_JAN_20.csv missing entry 2019-04-01T15:29:00+05:30; NIFTY_11650_PE_02_JAN_20.csv missing exit 2019-04-02T09:16:00+05:30
- `2019-04-02`: `missing_entry_or_exit_timestamp`. NIFTY_11750_CE_02_JAN_20.csv missing entry 2019-04-02T15:29:00+05:30; NIFTY_11750_CE_02_JAN_20.csv missing exit 2019-04-03T09:16:00+05:30
- `2019-04-03`: `missing_entry_or_exit_timestamp`. NIFTY_11650_PE_02_JAN_20.csv missing entry 2019-04-03T15:29:00+05:30; NIFTY_11650_PE_02_JAN_20.csv missing exit 2019-04-04T09:16:00+05:30
- `2019-04-04`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-04-04T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-04-05T09:16:00+05:30
- `2019-04-05`: `missing_entry_or_exit_timestamp`. NIFTY_11700_CE_02_JAN_20.csv missing entry 2019-04-05T15:29:00+05:30; NIFTY_11700_CE_02_JAN_20.csv missing exit 2019-04-08T09:16:00+05:30
- `2019-04-08`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-04-08T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-04-09T09:16:00+05:30
- `2019-04-09`: `missing_entry_or_exit_timestamp`. NIFTY_11700_CE_02_JAN_20.csv missing entry 2019-04-09T15:29:00+05:30; NIFTY_11700_CE_02_JAN_20.csv missing exit 2019-04-10T09:16:00+05:30
- `2019-04-10`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-04-10T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-04-11T09:16:00+05:30
- `2019-04-11`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-04-11T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-04-12T09:16:00+05:30
- `2019-04-12`: `missing_option_file`. Missing: NIFTY_11650_CE_02_JAN_20.csv
- `2019-04-15`: `missing_entry_or_exit_timestamp`. NIFTY_11700_CE_02_JAN_20.csv missing entry 2019-04-15T15:29:00+05:30; NIFTY_11700_CE_02_JAN_20.csv missing exit 2019-04-16T09:16:00+05:30
- `2019-04-16`: `missing_entry_or_exit_timestamp`. NIFTY_11800_CE_02_JAN_20.csv missing entry 2019-04-16T15:29:00+05:30; NIFTY_11800_CE_02_JAN_20.csv missing exit 2019-04-18T09:16:00+05:30
- `2019-04-18`: `missing_entry_or_exit_timestamp`. NIFTY_11750_PE_02_JAN_20.csv missing entry 2019-04-18T15:29:00+05:30; NIFTY_11750_PE_02_JAN_20.csv missing exit 2019-04-22T09:16:00+05:30
- `2019-04-22`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-04-22T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-04-23T09:16:00+05:30
- `2019-04-23`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-04-23T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-04-24T09:16:00+05:30
- `2019-04-24`: `missing_entry_or_exit_timestamp`. NIFTY_11700_CE_02_JAN_20.csv missing entry 2019-04-24T15:29:00+05:30; NIFTY_11700_CE_02_JAN_20.csv missing exit 2019-04-25T09:16:00+05:30
- `2019-04-25`: `missing_entry_or_exit_timestamp`. NIFTY_11650_PE_02_JAN_20.csv missing entry 2019-04-25T15:29:00+05:30; NIFTY_11650_PE_02_JAN_20.csv missing exit 2019-04-26T09:16:00+05:30
- `2019-04-26`: `missing_entry_or_exit_timestamp`. NIFTY_11750_CE_02_JAN_20.csv missing entry 2019-04-26T15:29:00+05:30; NIFTY_11750_CE_02_JAN_20.csv missing exit 2019-04-30T09:16:00+05:30
- `2019-04-30`: `missing_entry_or_exit_timestamp`. NIFTY_11750_CE_02_JAN_20.csv missing entry 2019-04-30T15:29:00+05:30; NIFTY_11750_CE_02_JAN_20.csv missing exit 2019-05-02T09:16:00+05:30
- `2019-05-02`: `missing_entry_or_exit_timestamp`. NIFTY_11700_PE_02_JAN_20.csv missing entry 2019-05-02T15:29:00+05:30; NIFTY_11700_PE_02_JAN_20.csv missing exit 2019-05-03T09:16:00+05:30
- `2019-05-03`: `missing_entry_or_exit_timestamp`. NIFTY_11700_PE_02_JAN_20.csv missing entry 2019-05-03T15:29:00+05:30; NIFTY_11700_PE_02_JAN_20.csv missing exit 2019-05-06T09:16:00+05:30
- `2019-05-06`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-05-06T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-05-07T09:16:00+05:30
- `2019-05-07`: `missing_entry_or_exit_timestamp`. NIFTY_11500_PE_02_JAN_20.csv missing entry 2019-05-07T15:29:00+05:30; NIFTY_11500_PE_02_JAN_20.csv missing exit 2019-05-08T09:16:00+05:30
- `2019-05-08`: `missing_entry_or_exit_timestamp`. NIFTY_11350_PE_02_JAN_20.csv missing entry 2019-05-08T15:29:00+05:30; NIFTY_11350_PE_02_JAN_20.csv missing exit 2019-05-09T09:16:00+05:30
- `2019-05-09`: `missing_entry_or_exit_timestamp`. NIFTY_11300_PE_02_JAN_20.csv missing entry 2019-05-09T15:29:00+05:30; NIFTY_11300_PE_02_JAN_20.csv missing exit 2019-05-10T09:16:00+05:30
- `2019-05-10`: `missing_entry_or_exit_timestamp`. NIFTY_11250_PE_02_JAN_20.csv missing entry 2019-05-10T15:29:00+05:30; NIFTY_11250_PE_02_JAN_20.csv missing exit 2019-05-13T09:16:00+05:30
- `2019-05-13`: `missing_option_file`. Missing: NIFTY_11150_PE_02_JAN_20.csv
- `2019-05-14`: `missing_entry_or_exit_timestamp`. NIFTY_11250_CE_02_JAN_20.csv missing entry 2019-05-14T15:29:00+05:30; NIFTY_11250_CE_02_JAN_20.csv missing exit 2019-05-15T09:16:00+05:30
- `2019-05-15`: `missing_option_file`. Missing: NIFTY_11150_PE_02_JAN_20.csv
- `2019-05-16`: `missing_entry_or_exit_timestamp`. NIFTY_11300_CE_02_JAN_20.csv missing entry 2019-05-16T15:29:00+05:30; NIFTY_11300_CE_02_JAN_20.csv missing exit 2019-05-17T09:16:00+05:30
- `2019-05-17`: `missing_entry_or_exit_timestamp`. NIFTY_11400_CE_02_JAN_20.csv missing entry 2019-05-17T15:29:00+05:30; NIFTY_11400_CE_02_JAN_20.csv missing exit 2019-05-20T09:16:00+05:30
- `2019-05-20`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-05-20T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-05-21T09:16:00+05:30
- `2019-05-21`: `missing_entry_or_exit_timestamp`. NIFTY_11700_PE_02_JAN_20.csv missing entry 2019-05-21T15:29:00+05:30; NIFTY_11700_PE_02_JAN_20.csv missing exit 2019-05-22T09:16:00+05:30
- `2019-05-22`: `missing_entry_or_exit_timestamp`. NIFTY_11750_CE_02_JAN_20.csv missing entry 2019-05-22T15:29:00+05:30; NIFTY_11750_CE_02_JAN_20.csv missing exit 2019-05-23T09:16:00+05:30
- `2019-05-23`: `missing_entry_or_exit_timestamp`. NIFTY_11700_PE_02_JAN_20.csv missing entry 2019-05-23T15:29:00+05:30; NIFTY_11700_PE_02_JAN_20.csv missing exit 2019-05-24T09:16:00+05:30
- `2019-05-24`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-05-24T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-05-27T09:16:00+05:30
- `2019-05-27`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-05-27T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-05-28T09:16:00+05:30
- `2019-05-28`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-05-28T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-05-29T09:16:00+05:30
- `2019-05-29`: `missing_entry_or_exit_timestamp`. NIFTY_11850_PE_02_JAN_20.csv missing entry 2019-05-29T15:29:00+05:30; NIFTY_11850_PE_02_JAN_20.csv missing exit 2019-05-30T09:16:00+05:30
- `2019-05-30`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-05-30T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-05-31T09:16:00+05:30
- `2019-05-31`: `missing_entry_or_exit_timestamp`. NIFTY_11900_PE_02_JAN_20.csv missing entry 2019-05-31T15:29:00+05:30; NIFTY_11900_PE_02_JAN_20.csv missing exit 2019-06-03T09:16:00+05:30
- `2019-06-03`: `missing_entry_or_exit_timestamp`. NIFTY_12100_CE_02_JAN_20.csv missing entry 2019-06-03T15:29:00+05:30; NIFTY_12100_CE_02_JAN_20.csv missing exit 2019-06-04T09:16:00+05:30
- `2019-06-04`: `missing_entry_or_exit_timestamp`. NIFTY_12050_PE_02_JAN_20.csv missing entry 2019-06-04T15:29:00+05:30; NIFTY_12050_PE_02_JAN_20.csv missing exit 2019-06-06T09:16:00+05:30
- `2019-06-06`: `missing_entry_or_exit_timestamp`. NIFTY_11850_PE_02_JAN_20.csv missing entry 2019-06-06T15:29:00+05:30; NIFTY_11850_PE_02_JAN_20.csv missing exit 2019-06-07T09:16:00+05:30
- `2019-06-07`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-06-07T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-06-10T09:16:00+05:30
- `2019-06-10`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-06-10T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-06-11T09:16:00+05:30
- `2019-06-11`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-06-11T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-06-12T09:16:00+05:30
- `2019-06-12`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-06-12T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-06-13T09:16:00+05:30
- `2019-06-13`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-06-13T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-06-14T09:16:00+05:30
- `2019-06-14`: `missing_entry_or_exit_timestamp`. NIFTY_11800_PE_02_JAN_20.csv missing entry 2019-06-14T15:29:00+05:30; NIFTY_11800_PE_02_JAN_20.csv missing exit 2019-06-17T09:16:00+05:30
- `2019-06-17`: `missing_entry_or_exit_timestamp`. NIFTY_11650_PE_02_JAN_20.csv missing entry 2019-06-17T15:29:00+05:30; NIFTY_11650_PE_02_JAN_20.csv missing exit 2019-06-18T09:16:00+05:30
- `2019-06-18`: `missing_entry_or_exit_timestamp`. NIFTY_11700_CE_02_JAN_20.csv missing entry 2019-06-18T15:29:00+05:30; NIFTY_11700_CE_02_JAN_20.csv missing exit 2019-06-19T09:16:00+05:30
- `2019-06-19`: `missing_entry_or_exit_timestamp`. NIFTY_11700_PE_02_JAN_20.csv missing entry 2019-06-19T15:29:00+05:30; NIFTY_11700_PE_02_JAN_20.csv missing exit 2019-06-20T09:16:00+05:30
- `2019-06-20`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-06-20T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-06-21T09:16:00+05:30
- `2019-06-21`: `missing_entry_or_exit_timestamp`. NIFTY_11750_PE_02_JAN_20.csv missing entry 2019-06-21T15:29:00+05:30; NIFTY_11750_PE_02_JAN_20.csv missing exit 2019-06-24T09:16:00+05:30
- `2019-06-24`: `missing_entry_or_exit_timestamp`. NIFTY_11700_PE_02_JAN_20.csv missing entry 2019-06-24T15:29:00+05:30; NIFTY_11700_PE_02_JAN_20.csv missing exit 2019-06-25T09:16:00+05:30
- `2019-06-25`: `missing_entry_or_exit_timestamp`. NIFTY_11800_CE_02_JAN_20.csv missing entry 2019-06-25T15:29:00+05:30; NIFTY_11800_CE_02_JAN_20.csv missing exit 2019-06-26T09:16:00+05:30
- `2019-06-26`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-06-26T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-06-27T09:16:00+05:30
- `2019-06-27`: `missing_entry_or_exit_timestamp`. NIFTY_11850_PE_02_JAN_20.csv missing entry 2019-06-27T15:29:00+05:30; NIFTY_11850_PE_02_JAN_20.csv missing exit 2019-06-28T09:16:00+05:30
- `2019-06-28`: `missing_entry_or_exit_timestamp`. NIFTY_11800_PE_02_JAN_20.csv missing entry 2019-06-28T15:29:00+05:30; NIFTY_11800_PE_02_JAN_20.csv missing exit 2019-07-01T09:16:00+05:30
- `2019-07-01`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-07-01T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-07-02T09:16:00+05:30
- `2019-07-02`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-07-02T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-07-03T09:16:00+05:30
- `2019-07-03`: `missing_entry_or_exit_timestamp`. NIFTY_11900_PE_02_JAN_20.csv missing entry 2019-07-03T15:29:00+05:30; NIFTY_11900_PE_02_JAN_20.csv missing exit 2019-07-04T09:16:00+05:30
- `2019-07-04`: `missing_entry_or_exit_timestamp`. NIFTY_11950_PE_02_JAN_20.csv missing entry 2019-07-04T15:29:00+05:30; NIFTY_11950_PE_02_JAN_20.csv missing exit 2019-07-05T09:16:00+05:30
- `2019-07-05`: `missing_entry_or_exit_timestamp`. NIFTY_11800_PE_02_JAN_20.csv missing entry 2019-07-05T15:29:00+05:30; NIFTY_11800_PE_02_JAN_20.csv missing exit 2019-07-08T09:16:00+05:30
- `2019-07-08`: `missing_entry_or_exit_timestamp`. NIFTY_11550_PE_02_JAN_20.csv missing entry 2019-07-08T15:29:00+05:30; NIFTY_11550_PE_02_JAN_20.csv missing exit 2019-07-09T09:16:00+05:30
- `2019-07-09`: `missing_option_file`. Missing: NIFTY_11550_CE_02_JAN_20.csv
- `2019-07-10`: `missing_entry_or_exit_timestamp`. NIFTY_11500_PE_02_JAN_20.csv missing entry 2019-07-10T15:29:00+05:30; NIFTY_11500_PE_02_JAN_20.csv missing exit 2019-07-11T09:16:00+05:30
- `2019-07-11`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-07-11T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-07-12T09:16:00+05:30
- `2019-07-12`: `missing_entry_or_exit_timestamp`. NIFTY_11550_PE_02_JAN_20.csv missing entry 2019-07-12T15:29:00+05:30; NIFTY_11550_PE_02_JAN_20.csv missing exit 2019-07-15T09:16:00+05:30
- `2019-07-15`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-07-15T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-07-16T09:16:00+05:30
- `2019-07-16`: `missing_option_file`. Missing: NIFTY_11650_CE_02_JAN_20.csv
- `2019-07-17`: `missing_entry_or_exit_timestamp`. NIFTY_11700_CE_02_JAN_20.csv missing entry 2019-07-17T15:29:00+05:30; NIFTY_11700_CE_02_JAN_20.csv missing exit 2019-07-18T09:16:00+05:30
- `2019-07-18`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-07-18T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-07-19T09:16:00+05:30
- `2019-07-19`: `missing_option_file`. Missing: NIFTY_11450_PE_02_JAN_20.csv
- `2019-07-22`: `missing_entry_or_exit_timestamp`. NIFTY_11350_PE_02_JAN_20.csv missing entry 2019-07-22T15:29:00+05:30; NIFTY_11350_PE_02_JAN_20.csv missing exit 2019-07-23T09:16:00+05:30
- `2019-07-23`: `missing_entry_or_exit_timestamp`. NIFTY_11350_PE_02_JAN_20.csv missing entry 2019-07-23T15:29:00+05:30; NIFTY_11350_PE_02_JAN_20.csv missing exit 2019-07-24T09:16:00+05:30
- `2019-07-24`: `missing_entry_or_exit_timestamp`. NIFTY_11250_CE_02_JAN_20.csv missing entry 2019-07-24T15:29:00+05:30; NIFTY_11250_CE_02_JAN_20.csv missing exit 2019-07-25T09:16:00+05:30
- `2019-07-25`: `missing_entry_or_exit_timestamp`. NIFTY_11250_PE_02_JAN_20.csv missing entry 2019-07-25T15:29:00+05:30; NIFTY_11250_PE_02_JAN_20.csv missing exit 2019-07-26T09:16:00+05:30
- `2019-07-26`: `missing_entry_or_exit_timestamp`. NIFTY_11300_CE_02_JAN_20.csv missing entry 2019-07-26T15:29:00+05:30; NIFTY_11300_CE_02_JAN_20.csv missing exit 2019-07-29T09:16:00+05:30
- `2019-07-29`: `missing_entry_or_exit_timestamp`. NIFTY_11200_PE_02_JAN_20.csv missing entry 2019-07-29T15:29:00+05:30; NIFTY_11200_PE_02_JAN_20.csv missing exit 2019-07-30T09:16:00+05:30
- `2019-07-30`: `missing_entry_or_exit_timestamp`. NIFTY_11100_PE_02_JAN_20.csv missing entry 2019-07-30T15:29:00+05:30; NIFTY_11100_PE_02_JAN_20.csv missing exit 2019-07-31T09:16:00+05:30
- `2019-07-31`: `missing_entry_or_exit_timestamp`. NIFTY_11100_CE_02_JAN_20.csv missing entry 2019-07-31T15:29:00+05:30; NIFTY_11100_CE_02_JAN_20.csv missing exit 2019-08-01T09:16:00+05:30
- `2019-08-01`: `missing_entry_or_exit_timestamp`. NIFTY_11000_CE_02_JAN_20.csv missing entry 2019-08-01T15:29:00+05:30; NIFTY_11000_CE_02_JAN_20.csv missing exit 2019-08-02T09:16:00+05:30
- `2019-08-02`: `missing_entry_or_exit_timestamp`. NIFTY_11000_CE_02_JAN_20.csv missing entry 2019-08-02T15:29:00+05:30; NIFTY_11000_CE_02_JAN_20.csv missing exit 2019-08-05T09:16:00+05:30
- `2019-08-05`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-08-06`: `missing_option_file`. Missing: NIFTY_10950_PE_02_JAN_20.csv
- `2019-08-07`: `missing_option_file`. Missing: NIFTY_10850_PE_02_JAN_20.csv
- `2019-08-08`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-08-09`: `missing_entry_or_exit_timestamp`. NIFTY_11100_PE_02_JAN_20.csv missing entry 2019-08-09T15:29:00+05:30; NIFTY_11100_PE_02_JAN_20.csv missing exit 2019-08-13T09:16:00+05:30
- `2019-08-13`: `missing_option_file`. Missing: NIFTY_10900_PE_02_JAN_20.csv
- `2019-08-14`: `missing_entry_or_exit_timestamp`. NIFTY_11000_PE_02_JAN_20.csv missing entry 2019-08-14T15:29:00+05:30; NIFTY_11000_PE_02_JAN_20.csv missing exit 2019-08-16T09:16:00+05:30
- `2019-08-16`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-08-19`: `missing_option_file`. Missing: NIFTY_11050_PE_02_JAN_20.csv
- `2019-08-20`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-08-21`: `missing_option_file`. Missing: NIFTY_10900_PE_02_JAN_20.csv
- `2019-08-22`: `missing_option_file`. Missing: NIFTY_10750_PE_02_JAN_20.csv
- `2019-08-23`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-08-26`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-08-27`: `missing_entry_or_exit_timestamp`. NIFTY_11100_CE_02_JAN_20.csv missing entry 2019-08-27T15:29:00+05:30; NIFTY_11100_CE_02_JAN_20.csv missing exit 2019-08-28T09:16:00+05:30
- `2019-08-28`: `missing_option_file`. Missing: NIFTY_11050_PE_02_JAN_20.csv
- `2019-08-29`: `missing_option_file`. Missing: NIFTY_10950_PE_02_JAN_20.csv
- `2019-08-30`: `missing_option_file`. Missing: NIFTY_11050_CE_02_JAN_20.csv
- `2019-09-03`: `missing_option_file`. Missing: NIFTY_10800_PE_02_JAN_20.csv
- `2019-09-04`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-09-05`: `missing_option_file`. Missing: NIFTY_10850_PE_02_JAN_20.csv
- `2019-09-06`: `missing_option_file`. Missing: NIFTY_10950_CE_02_JAN_20.csv
- `2019-09-09`: `missing_entry_or_exit_timestamp`. NIFTY_11000_CE_02_JAN_20.csv missing entry 2019-09-09T15:29:00+05:30; NIFTY_11000_CE_02_JAN_20.csv missing exit 2019-09-11T09:16:00+05:30
- `2019-09-11`: `missing_entry_or_exit_timestamp`. NIFTY_11000_PE_02_JAN_20.csv missing entry 2019-09-11T15:29:00+05:30; NIFTY_11000_PE_02_JAN_20.csv missing exit 2019-09-12T09:16:00+05:30
- `2019-09-12`: `missing_entry_or_exit_timestamp`. NIFTY_11000_PE_02_JAN_20.csv missing entry 2019-09-12T15:29:00+05:30; NIFTY_11000_PE_02_JAN_20.csv missing exit 2019-09-13T09:16:00+05:30
- `2019-09-13`: `missing_entry_or_exit_timestamp`. NIFTY_11100_CE_02_JAN_20.csv missing entry 2019-09-13T15:29:00+05:30; NIFTY_11100_CE_02_JAN_20.csv missing exit 2019-09-16T09:16:00+05:30
- `2019-09-16`: `missing_entry_or_exit_timestamp`. NIFTY_11000_PE_02_JAN_20.csv missing entry 2019-09-16T15:29:00+05:30; NIFTY_11000_PE_02_JAN_20.csv missing exit 2019-09-17T09:16:00+05:30
- `2019-09-17`: `missing_option_file`. Missing: NIFTY_10850_PE_02_JAN_20.csv
- `2019-09-18`: `missing_option_file`. Missing: NIFTY_10850_CE_02_JAN_20.csv
- `2019-09-19`: `missing_option_file`. Missing: NIFTY_10700_PE_02_JAN_20.csv
- `2019-09-20`: `missing_entry_or_exit_timestamp`. NIFTY_11300_CE_02_JAN_20.csv missing entry 2019-09-20T15:29:00+05:30; NIFTY_11300_CE_02_JAN_20.csv missing exit 2019-09-23T09:16:00+05:30
- `2019-09-23`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-09-23T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-09-24T09:16:00+05:30
- `2019-09-24`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-09-24T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-09-25T09:16:00+05:30
- `2019-09-25`: `missing_option_file`. Missing: NIFTY_11450_PE_02_JAN_20.csv
- `2019-09-26`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-09-26T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-09-27T09:16:00+05:30
- `2019-09-27`: `missing_entry_or_exit_timestamp`. NIFTY_11500_PE_02_JAN_20.csv missing entry 2019-09-27T15:29:00+05:30; NIFTY_11500_PE_02_JAN_20.csv missing exit 2019-09-30T09:16:00+05:30
- `2019-09-30`: `missing_entry_or_exit_timestamp`. NIFTY_11500_CE_02_JAN_20.csv missing entry 2019-09-30T15:29:00+05:30; NIFTY_11500_CE_02_JAN_20.csv missing exit 2019-10-01T09:16:00+05:30
- `2019-10-01`: `missing_entry_or_exit_timestamp`. NIFTY_11350_PE_02_JAN_20.csv missing entry 2019-10-01T15:29:00+05:30; NIFTY_11350_PE_02_JAN_20.csv missing exit 2019-10-03T09:16:00+05:30
- `2019-10-03`: `missing_entry_or_exit_timestamp`. NIFTY_11300_PE_02_JAN_20.csv missing entry 2019-10-03T15:29:00+05:30; NIFTY_11300_PE_02_JAN_20.csv missing exit 2019-10-04T09:16:00+05:30
- `2019-10-04`: `missing_option_file`. Missing: NIFTY_11150_PE_02_JAN_20.csv
- `2019-10-07`: `missing_entry_or_exit_timestamp`. NIFTY_11100_PE_02_JAN_20.csv missing entry 2019-10-07T15:29:00+05:30; NIFTY_11100_PE_02_JAN_20.csv missing exit 2019-10-09T09:16:00+05:30
- `2019-10-09`: `missing_entry_or_exit_timestamp`. NIFTY_11300_CE_02_JAN_20.csv missing entry 2019-10-09T15:29:00+05:30; NIFTY_11300_CE_02_JAN_20.csv missing exit 2019-10-10T09:16:00+05:30
- `2019-10-10`: `missing_entry_or_exit_timestamp`. NIFTY_11250_PE_02_JAN_20.csv missing entry 2019-10-10T15:29:00+05:30; NIFTY_11250_PE_02_JAN_20.csv missing exit 2019-10-11T09:16:00+05:30
- `2019-10-11`: `missing_entry_or_exit_timestamp`. NIFTY_11300_CE_02_JAN_20.csv missing entry 2019-10-11T15:29:00+05:30; NIFTY_11300_CE_02_JAN_20.csv missing exit 2019-10-14T09:16:00+05:30
- `2019-10-14`: `missing_entry_or_exit_timestamp`. NIFTY_11350_PE_02_JAN_20.csv missing entry 2019-10-14T15:29:00+05:30; NIFTY_11350_PE_02_JAN_20.csv missing exit 2019-10-15T09:16:00+05:30
- `2019-10-15`: `missing_option_file`. Missing: NIFTY_11450_CE_02_JAN_20.csv
- `2019-10-16`: `missing_option_file`. Missing: NIFTY_11450_CE_02_JAN_20.csv
- `2019-10-17`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-10-17T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-10-18T09:16:00+05:30
- `2019-10-18`: `missing_option_file`. Missing: NIFTY_11650_CE_02_JAN_20.csv
- `2019-10-22`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-10-22T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-10-23T09:16:00+05:30
- `2019-10-23`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-10-23T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-10-24T09:16:00+05:30
- `2019-10-24`: `missing_entry_or_exit_timestamp`. NIFTY_11600_PE_02_JAN_20.csv missing entry 2019-10-24T15:29:00+05:30; NIFTY_11600_PE_02_JAN_20.csv missing exit 2019-10-25T09:16:00+05:30
- `2019-10-25`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_02_JAN_20.csv missing entry 2019-10-25T15:29:00+05:30; NIFTY_11600_CE_02_JAN_20.csv missing exit 2019-10-27T09:16:00+05:30
- `2019-10-27`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2019-10-27T15:15:00+05:30
- `2019-10-29`: `missing_entry_or_exit_timestamp`. NIFTY_11800_CE_02_JAN_20.csv missing entry 2019-10-29T15:29:00+05:30; NIFTY_11800_CE_02_JAN_20.csv missing exit 2019-10-30T09:16:00+05:30
- `2019-10-30`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-10-30T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-10-31T09:16:00+05:30
- `2019-10-31`: `missing_entry_or_exit_timestamp`. NIFTY_11900_PE_02_JAN_20.csv missing entry 2019-10-31T15:29:00+05:30; NIFTY_11900_PE_02_JAN_20.csv missing exit 2019-11-01T09:16:00+05:30
- `2019-11-01`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-11-01T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-11-04T09:16:00+05:30
- `2019-11-04`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-11-04T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-11-05T09:16:00+05:30
- `2019-11-05`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-11-05T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-11-06T09:16:00+05:30
- `2019-11-06`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-11-06T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-11-07T09:16:00+05:30
- `2019-11-07`: `missing_entry_or_exit_timestamp`. NIFTY_12000_CE_02_JAN_20.csv missing entry 2019-11-07T15:29:00+05:30; NIFTY_12000_CE_02_JAN_20.csv missing exit 2019-11-08T09:16:00+05:30
- `2019-11-08`: `missing_entry_or_exit_timestamp`. NIFTY_11900_PE_02_JAN_20.csv missing entry 2019-11-08T15:29:00+05:30; NIFTY_11900_PE_02_JAN_20.csv missing exit 2019-11-11T09:16:00+05:30
- `2019-11-11`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-11-11T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-11-13T09:16:00+05:30
- `2019-11-13`: `missing_entry_or_exit_timestamp`. NIFTY_11850_PE_02_JAN_20.csv missing entry 2019-11-13T15:29:00+05:30; NIFTY_11850_PE_02_JAN_20.csv missing exit 2019-11-14T09:16:00+05:30
- `2019-11-14`: `missing_entry_or_exit_timestamp`. NIFTY_11850_CE_02_JAN_20.csv missing entry 2019-11-14T15:29:00+05:30; NIFTY_11850_CE_02_JAN_20.csv missing exit 2019-11-15T09:16:00+05:30
- `2019-11-15`: `missing_entry_or_exit_timestamp`. NIFTY_11900_PE_02_JAN_20.csv missing entry 2019-11-15T15:29:00+05:30; NIFTY_11900_PE_02_JAN_20.csv missing exit 2019-11-18T09:16:00+05:30
- `2019-11-18`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-11-18T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-11-19T09:16:00+05:30
- `2019-11-19`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-11-19T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-11-20T09:16:00+05:30
- `2019-11-20`: `missing_entry_or_exit_timestamp`. NIFTY_12000_PE_02_JAN_20.csv missing entry 2019-11-20T15:29:00+05:30; NIFTY_12000_PE_02_JAN_20.csv missing exit 2019-11-21T09:16:00+05:30
- `2019-11-21`: `missing_entry_or_exit_timestamp`. NIFTY_11950_PE_02_JAN_20.csv missing entry 2019-11-21T15:29:00+05:30; NIFTY_11950_PE_02_JAN_20.csv missing exit 2019-11-22T09:16:00+05:30
- `2019-11-22`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-11-22T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-11-25T09:16:00+05:30
- `2019-11-25`: `missing_entry_or_exit_timestamp`. NIFTY_12100_CE_02_JAN_20.csv missing entry 2019-11-25T15:29:00+05:30; NIFTY_12100_CE_02_JAN_20.csv missing exit 2019-11-26T09:16:00+05:30
- `2019-11-26`: `missing_entry_or_exit_timestamp`. NIFTY_12050_PE_02_JAN_20.csv missing entry 2019-11-26T15:29:00+05:30; NIFTY_12050_PE_02_JAN_20.csv missing exit 2019-11-27T09:16:00+05:30
- `2019-11-27`: `missing_entry_or_exit_timestamp`. NIFTY_12100_CE_02_JAN_20.csv missing entry 2019-11-27T15:29:00+05:30; NIFTY_12100_CE_02_JAN_20.csv missing exit 2019-11-28T09:16:00+05:30
- `2019-11-28`: `missing_entry_or_exit_timestamp`. NIFTY_12150_CE_02_JAN_20.csv missing entry 2019-11-28T15:29:00+05:30; NIFTY_12150_CE_02_JAN_20.csv missing exit 2019-11-29T09:16:00+05:30
- `2019-11-29`: `missing_entry_or_exit_timestamp`. NIFTY_12050_PE_02_JAN_20.csv missing entry 2019-11-29T15:29:00+05:30; NIFTY_12050_PE_02_JAN_20.csv missing exit 2019-12-02T09:16:00+05:30
- `2019-12-02`: `missing_entry_or_exit_timestamp`. NIFTY_12050_PE_02_JAN_20.csv missing entry 2019-12-02T15:29:00+05:30; NIFTY_12050_PE_02_JAN_20.csv missing exit 2019-12-03T09:16:00+05:30
- `2019-12-03`: `missing_entry_or_exit_timestamp`. NIFTY_12000_CE_02_JAN_20.csv missing entry 2019-12-03T15:29:00+05:30; NIFTY_12000_CE_02_JAN_20.csv missing exit 2019-12-04T09:16:00+05:30
- `2019-12-04`: `missing_entry_or_exit_timestamp`. NIFTY_12050_CE_02_JAN_20.csv missing entry 2019-12-04T15:29:00+05:30; NIFTY_12050_CE_02_JAN_20.csv missing exit 2019-12-05T09:16:00+05:30
- `2019-12-05`: `missing_entry_or_exit_timestamp`. NIFTY_12000_PE_02_JAN_20.csv missing entry 2019-12-05T15:29:00+05:30; NIFTY_12000_PE_02_JAN_20.csv missing exit 2019-12-06T09:16:00+05:30
- `2019-12-06`: `missing_entry_or_exit_timestamp`. NIFTY_11900_PE_02_JAN_20.csv missing entry 2019-12-06T15:29:00+05:30; NIFTY_11900_PE_02_JAN_20.csv missing exit 2019-12-09T09:16:00+05:30
- `2019-12-09`: `missing_entry_or_exit_timestamp`. NIFTY_11950_PE_02_JAN_20.csv missing entry 2019-12-09T15:29:00+05:30; NIFTY_11950_PE_02_JAN_20.csv missing exit 2019-12-10T09:16:00+05:30
- `2019-12-10`: `missing_entry_or_exit_timestamp`. NIFTY_11850_PE_02_JAN_20.csv missing entry 2019-12-10T15:29:00+05:30; NIFTY_11850_PE_02_JAN_20.csv missing exit 2019-12-11T09:16:00+05:30
- `2019-12-11`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_02_JAN_20.csv missing entry 2019-12-11T15:29:00+05:30; NIFTY_11900_CE_02_JAN_20.csv missing exit 2019-12-12T09:16:00+05:30
- `2019-12-12`: `missing_entry_or_exit_timestamp`. NIFTY_11950_CE_02_JAN_20.csv missing entry 2019-12-12T15:29:00+05:30; NIFTY_11950_CE_02_JAN_20.csv missing exit 2019-12-13T09:16:00+05:30
- `2019-12-13`: `missing_entry_or_exit_timestamp`. NIFTY_12100_CE_02_JAN_20.csv missing entry 2019-12-13T15:29:00+05:30; NIFTY_12100_CE_02_JAN_20.csv missing exit 2019-12-16T09:16:00+05:30
- `2019-12-16`: `missing_entry_or_exit_timestamp`. NIFTY_12050_PE_02_JAN_20.csv missing entry 2019-12-16T15:29:00+05:30; NIFTY_12050_PE_02_JAN_20.csv missing exit 2019-12-17T09:16:00+05:30
- `2019-12-17`: `missing_entry_or_exit_timestamp`. NIFTY_12150_CE_02_JAN_20.csv missing entry 2019-12-17T15:29:00+05:30; NIFTY_12150_CE_02_JAN_20.csv missing exit 2019-12-18T09:16:00+05:30
- `2019-12-18`: `missing_entry_or_exit_timestamp`. NIFTY_12250_CE_02_JAN_20.csv missing entry 2019-12-18T15:29:00+05:30; NIFTY_12250_CE_02_JAN_20.csv missing exit 2019-12-19T09:16:00+05:30
- `2019-12-19`: `missing_entry_or_exit_timestamp`. NIFTY_12250_CE_02_JAN_20.csv missing entry 2019-12-19T15:29:00+05:30; NIFTY_12250_CE_02_JAN_20.csv missing exit 2019-12-20T09:16:00+05:30
- `2019-12-20`: `missing_entry_or_exit_timestamp`. NIFTY_12250_PE_02_JAN_20.csv missing entry 2019-12-20T15:29:00+05:30; NIFTY_12250_PE_02_JAN_20.csv missing exit 2019-12-23T09:16:00+05:30
- `2019-12-23`: `missing_entry_or_exit_timestamp`. NIFTY_12250_CE_02_JAN_20.csv missing entry 2019-12-23T15:29:00+05:30; NIFTY_12250_CE_02_JAN_20.csv missing exit 2019-12-24T09:16:00+05:30
- `2019-12-24`: `missing_entry_or_exit_timestamp`. NIFTY_12200_PE_02_JAN_20.csv missing entry 2019-12-24T15:29:00+05:30; NIFTY_12200_PE_02_JAN_20.csv missing exit 2019-12-26T09:16:00+05:30
- `2019-12-26`: `missing_entry_or_exit_timestamp`. NIFTY_12150_PE_02_JAN_20.csv missing entry 2019-12-26T15:29:00+05:30; NIFTY_12150_PE_02_JAN_20.csv missing exit 2019-12-27T09:16:00+05:30
- `2019-12-27`: `missing_entry_or_exit_timestamp`. NIFTY_12250_CE_02_JAN_20.csv missing entry 2019-12-27T15:29:00+05:30; NIFTY_12250_CE_02_JAN_20.csv missing exit 2019-12-30T09:16:00+05:30
- `2019-12-30`: `missing_entry_or_exit_timestamp`. NIFTY_12250_CE_02_JAN_20.csv missing entry 2019-12-30T15:29:00+05:30; NIFTY_12250_CE_02_JAN_20.csv missing exit 2019-12-31T09:16:00+05:30
- `2019-12-31`: `missing_entry_or_exit_timestamp`. NIFTY_12200_PE_02_JAN_20.csv missing entry 2019-12-31T15:29:00+05:30
- `2020-01-02`: `missing_entry_or_exit_timestamp`. NIFTY_12300_CE_09_JAN_20.csv missing entry 2020-01-02T15:29:00+05:30
- `2020-01-09`: `missing_entry_or_exit_timestamp`. NIFTY_12200_CE_16_JAN_20.csv missing entry 2020-01-09T15:29:00+05:30
- `2020-01-16`: `missing_entry_or_exit_timestamp`. NIFTY_12350_CE_23_JAN_20.csv missing entry 2020-01-16T15:29:00+05:30
- `2020-01-23`: `missing_entry_or_exit_timestamp`. NIFTY_12200_CE_30_JAN_20.csv missing entry 2020-01-23T15:29:00+05:30
- `2020-01-30`: `missing_entry_or_exit_timestamp`. NIFTY_12000_PE_06_FEB_20.csv missing entry 2020-01-30T15:29:00+05:30
- `2020-02-06`: `missing_entry_or_exit_timestamp`. NIFTY_12150_CE_13_FEB_20.csv missing entry 2020-02-06T15:29:00+05:30
- `2020-02-13`: `missing_entry_or_exit_timestamp`. NIFTY_12150_CE_20_FEB_20.csv missing entry 2020-02-13T15:29:00+05:30
- `2020-02-20`: `missing_entry_or_exit_timestamp`. NIFTY_12100_PE_27_FEB_20.csv missing entry 2020-02-20T15:29:00+05:30
- `2020-02-27`: `missing_entry_or_exit_timestamp`. NIFTY_11600_CE_05_MAR_20.csv missing entry 2020-02-27T15:29:00+05:30
- `2020-03-05`: `missing_entry_or_exit_timestamp`. NIFTY_11250_PE_12_MAR_20.csv missing entry 2020-03-05T15:29:00+05:30
- `2020-03-11`: `missing_entry_or_exit_timestamp`. NIFTY_10450_PE_12_MAR_20.csv missing exit 2020-03-12T09:16:00+05:30
- `2020-03-12`: `missing_entry_or_exit_timestamp`. NIFTY_9650_PE_19_MAR_20.csv missing entry 2020-03-12T15:29:00+05:30
- `2020-03-19`: `missing_entry_or_exit_timestamp`. NIFTY_8250_CE_26_MAR_20.csv missing entry 2020-03-19T15:29:00+05:30
- `2020-03-26`: `missing_entry_or_exit_timestamp`. NIFTY_8650_CE_01_APR_20.csv missing entry 2020-03-26T15:29:00+05:30; NIFTY_8650_CE_01_APR_20.csv missing exit 2020-03-27T09:16:00+05:30
- `2020-04-01`: `missing_entry_or_exit_timestamp`. NIFTY_8250_PE_09_APR_20.csv missing entry 2020-04-01T15:29:00+05:30
- `2020-04-08`: `missing_entry_or_exit_timestamp`. NIFTY_8750_PE_09_APR_20.csv missing exit 2020-04-09T09:16:00+05:30
- `2020-04-09`: `missing_entry_or_exit_timestamp`. NIFTY_9100_CE_16_APR_20.csv missing entry 2020-04-09T15:29:00+05:30
- `2020-04-16`: `missing_entry_or_exit_timestamp`. NIFTY_9000_CE_23_APR_20.csv missing entry 2020-04-16T15:29:00+05:30
- `2020-04-23`: `missing_entry_or_exit_timestamp`. NIFTY_9300_CE_30_APR_20.csv missing entry 2020-04-23T15:29:00+05:30
- `2020-04-30`: `missing_entry_or_exit_timestamp`. NIFTY_9850_CE_07_MAY_20.csv missing entry 2020-04-30T15:29:00+05:30
- `2020-05-07`: `missing_entry_or_exit_timestamp`. NIFTY_9200_PE_14_MAY_20.csv missing entry 2020-05-07T15:29:00+05:30
- `2020-05-14`: `missing_entry_or_exit_timestamp`. NIFTY_9150_PE_21_MAY_20.csv missing entry 2020-05-14T15:29:00+05:30
- `2020-05-21`: `missing_entry_or_exit_timestamp`. NIFTY_9100_PE_28_MAY_20.csv missing entry 2020-05-21T15:29:00+05:30
- `2020-05-28`: `missing_entry_or_exit_timestamp`. NIFTY_9500_CE_04_JUN_20.csv missing entry 2020-05-28T15:29:00+05:30
- `2020-06-04`: `missing_entry_or_exit_timestamp`. NIFTY_10050_CE_11_JUN_20.csv missing entry 2020-06-04T15:29:00+05:30
- `2020-06-11`: `missing_entry_or_exit_timestamp`. NIFTY_9900_PE_18_JUN_20.csv missing entry 2020-06-11T15:29:00+05:30
- `2020-06-18`: `missing_entry_or_exit_timestamp`. NIFTY_10100_CE_25_JUN_20.csv missing entry 2020-06-18T15:29:00+05:30
- `2020-06-25`: `missing_entry_or_exit_timestamp`. NIFTY_10300_PE_02_JUL_20.csv missing entry 2020-06-25T15:29:00+05:30
- `2020-07-02`: `missing_entry_or_exit_timestamp`. NIFTY_10550_CE_09_JUL_20.csv missing entry 2020-07-02T15:29:00+05:30
- `2020-07-09`: `missing_entry_or_exit_timestamp`. NIFTY_10850_CE_16_JUL_20.csv missing entry 2020-07-09T15:29:00+05:30
- `2020-07-16`: `missing_entry_or_exit_timestamp`. NIFTY_10750_CE_23_JUL_20.csv missing entry 2020-07-16T15:29:00+05:30
- `2020-07-23`: `missing_entry_or_exit_timestamp`. NIFTY_11250_CE_30_JUL_20.csv missing entry 2020-07-23T15:29:00+05:30
- `2020-07-30`: `missing_entry_or_exit_timestamp`. NIFTY_11100_PE_06_AUG_20.csv missing entry 2020-07-30T15:29:00+05:30
- `2020-08-06`: `missing_entry_or_exit_timestamp`. NIFTY_11200_CE_13_AUG_20.csv missing entry 2020-08-06T15:29:00+05:30
- `2020-08-13`: `missing_entry_or_exit_timestamp`. NIFTY_11300_PE_20_AUG_20.csv missing entry 2020-08-13T15:29:00+05:30
- `2020-08-20`: `missing_entry_or_exit_timestamp`. NIFTY_11300_PE_27_AUG_20.csv missing entry 2020-08-20T15:29:00+05:30
- `2020-08-27`: `missing_entry_or_exit_timestamp`. NIFTY_11550_PE_03_SEP_20.csv missing entry 2020-08-27T15:29:00+05:30
- `2020-09-03`: `missing_entry_or_exit_timestamp`. NIFTY_11550_PE_10_SEP_20.csv missing entry 2020-09-03T15:29:00+05:30
- `2020-09-10`: `missing_entry_or_exit_timestamp`. NIFTY_11450_CE_17_SEP_20.csv missing entry 2020-09-10T15:29:00+05:30
- `2020-09-17`: `missing_entry_or_exit_timestamp`. NIFTY_11500_PE_24_SEP_20.csv missing entry 2020-09-17T15:29:00+05:30
- `2020-09-24`: `missing_entry_or_exit_timestamp`. NIFTY_10800_PE_01_OCT_20.csv missing entry 2020-09-24T15:29:00+05:30
- `2020-10-01`: `missing_entry_or_exit_timestamp`. NIFTY_11400_CE_08_OCT_20.csv missing entry 2020-10-01T15:29:00+05:30
- `2020-10-08`: `missing_entry_or_exit_timestamp`. NIFTY_11850_PE_15_OCT_20.csv missing entry 2020-10-08T15:29:00+05:30
- `2020-10-15`: `missing_entry_or_exit_timestamp`. NIFTY_11650_PE_22_OCT_20.csv missing entry 2020-10-15T15:29:00+05:30
- `2020-10-22`: `missing_entry_or_exit_timestamp`. NIFTY_11900_CE_29_OCT_20.csv missing entry 2020-10-22T15:29:00+05:30
- `2020-10-29`: `missing_entry_or_exit_timestamp`. NIFTY_11650_PE_05_NOV_20.csv missing entry 2020-10-29T15:29:00+05:30
- `2020-11-05`: `missing_entry_or_exit_timestamp`. NIFTY_12150_CE_12_NOV_20.csv missing entry 2020-11-05T15:29:00+05:30
- `2020-11-12`: `missing_entry_or_exit_timestamp`. NIFTY_12700_CE_19_NOV_20.csv missing entry 2020-11-12T15:29:00+05:30
- `2020-11-13`: `missing_entry_or_exit_timestamp`. NIFTY_12700_CE_19_NOV_20.csv missing exit 2020-11-14T09:16:00+05:30
- `2020-11-14`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2020-11-14T15:15:00+05:30
- `2020-11-19`: `missing_entry_or_exit_timestamp`. NIFTY_12750_PE_26_NOV_20.csv missing entry 2020-11-19T15:29:00+05:30
- `2020-11-26`: `missing_entry_or_exit_timestamp`. NIFTY_13000_CE_03_DEC_20.csv missing entry 2020-11-26T15:29:00+05:30
- `2020-12-03`: `missing_entry_or_exit_timestamp`. NIFTY_13150_PE_10_DEC_20.csv missing entry 2020-12-03T15:29:00+05:30
- `2020-12-10`: `missing_entry_or_exit_timestamp`. NIFTY_13500_CE_17_DEC_20.csv missing entry 2020-12-10T15:29:00+05:30
- `2020-12-17`: `missing_entry_or_exit_timestamp`. NIFTY_13750_CE_24_DEC_20.csv missing entry 2020-12-17T15:29:00+05:30
- `2020-12-24`: `missing_entry_or_exit_timestamp`. NIFTY_13750_CE_31_DEC_20.csv missing entry 2020-12-24T15:29:00+05:30
- `2020-12-31`: `missing_entry_or_exit_timestamp`. NIFTY_13950_PE_07_JAN_21.csv missing entry 2020-12-31T15:29:00+05:30
- `2021-01-07`: `missing_entry_or_exit_timestamp`. NIFTY_14150_PE_14_JAN_21.csv missing entry 2021-01-07T15:29:00+05:30
- `2021-01-14`: `missing_entry_or_exit_timestamp`. NIFTY_14600_CE_21_JAN_21.csv missing entry 2021-01-14T15:29:00+05:30
- `2021-01-21`: `missing_entry_or_exit_timestamp`. NIFTY_14650_PE_28_JAN_21.csv missing entry 2021-01-21T15:29:00+05:30
- `2021-01-28`: `missing_entry_or_exit_timestamp`. NIFTY_13800_CE_04_FEB_21.csv missing entry 2021-01-28T15:29:00+05:30
- `2021-02-04`: `missing_entry_or_exit_timestamp`. NIFTY_14900_CE_11_FEB_21.csv missing entry 2021-02-04T15:29:00+05:30
- `2021-02-11`: `missing_entry_or_exit_timestamp`. NIFTY_15200_CE_18_FEB_21.csv missing entry 2021-02-11T15:29:00+05:30
- `2021-02-18`: `missing_entry_or_exit_timestamp`. NIFTY_15100_PE_25_FEB_21.csv missing entry 2021-02-18T15:29:00+05:30
- `2021-02-24`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2021-02-24T15:15:00+05:30
- `2021-02-25`: `missing_entry_or_exit_timestamp`. NIFTY_15100_PE_04_MAR_21.csv missing entry 2021-02-25T15:29:00+05:30
- `2021-03-04`: `missing_entry_or_exit_timestamp`. NIFTY_15100_PE_10_MAR_21.csv missing entry 2021-03-04T15:29:00+05:30
- `2021-03-10`: `missing_entry_or_exit_timestamp`. NIFTY_15150_CE_18_MAR_21.csv missing entry 2021-03-10T15:29:00+05:30
- `2021-03-18`: `missing_entry_or_exit_timestamp`. NIFTY_14600_PE_25_MAR_21.csv missing entry 2021-03-18T15:29:00+05:30
- `2021-03-25`: `missing_entry_or_exit_timestamp`. NIFTY_14350_PE_01_APR_21.csv missing entry 2021-03-25T15:29:00+05:30
- `2021-04-01`: `missing_entry_or_exit_timestamp`. NIFTY_14850_CE_08_APR_21.csv missing entry 2021-04-01T15:29:00+05:30
- `2021-04-08`: `missing_entry_or_exit_timestamp`. NIFTY_14900_PE_15_APR_21.csv missing entry 2021-04-08T15:29:00+05:30
- `2021-04-15`: `missing_entry_or_exit_timestamp`. NIFTY_14600_CE_22_APR_21.csv missing entry 2021-04-15T15:29:00+05:30
- `2021-04-22`: `missing_entry_or_exit_timestamp`. NIFTY_14400_CE_29_APR_21.csv missing entry 2021-04-22T15:29:00+05:30
- `2021-04-29`: `missing_entry_or_exit_timestamp`. NIFTY_14900_PE_06_MAY_21.csv missing entry 2021-04-29T15:29:00+05:30
- `2021-05-06`: `missing_entry_or_exit_timestamp`. NIFTY_14750_CE_12_MAY_21.csv missing entry 2021-05-06T15:29:00+05:30
- `2021-05-12`: `missing_entry_or_exit_timestamp`. NIFTY_14700_PE_20_MAY_21.csv missing entry 2021-05-12T15:29:00+05:30
- `2021-05-20`: `missing_entry_or_exit_timestamp`. NIFTY_14900_PE_27_MAY_21.csv missing entry 2021-05-20T15:29:00+05:30
- `2021-05-27`: `missing_entry_or_exit_timestamp`. NIFTY_15350_CE_03_JUN_21.csv missing entry 2021-05-27T15:29:00+05:30
- `2021-06-03`: `missing_entry_or_exit_timestamp`. NIFTY_15700_CE_10_JUN_21.csv missing entry 2021-06-03T15:29:00+05:30
- `2021-06-10`: `missing_entry_or_exit_timestamp`. NIFTY_15750_CE_17_JUN_21.csv missing entry 2021-06-10T15:29:00+05:30
- `2021-06-17`: `missing_entry_or_exit_timestamp`. NIFTY_15700_PE_24_JUN_21.csv missing entry 2021-06-17T15:29:00+05:30
- `2021-06-24`: `missing_entry_or_exit_timestamp`. NIFTY_15800_CE_01_JUL_21.csv missing entry 2021-06-24T15:29:00+05:30
- `2021-07-01`: `missing_entry_or_exit_timestamp`. NIFTY_15700_PE_08_JUL_21.csv missing entry 2021-07-01T15:29:00+05:30
- `2021-07-08`: `missing_entry_or_exit_timestamp`. NIFTY_15750_PE_15_JUL_21.csv missing entry 2021-07-08T15:29:00+05:30
- `2021-07-15`: `missing_entry_or_exit_timestamp`. NIFTY_15900_PE_22_JUL_21.csv missing entry 2021-07-15T15:29:00+05:30
- `2021-07-22`: `missing_entry_or_exit_timestamp`. NIFTY_15850_CE_29_JUL_21.csv missing entry 2021-07-22T15:29:00+05:30
- `2021-07-29`: `missing_entry_or_exit_timestamp`. NIFTY_15800_PE_05_AUG_21.csv missing entry 2021-07-29T15:29:00+05:30
- `2021-08-05`: `missing_entry_or_exit_timestamp`. NIFTY_16300_CE_12_AUG_21.csv missing entry 2021-08-05T15:29:00+05:30
- `2021-08-12`: `missing_entry_or_exit_timestamp`. NIFTY_16350_CE_18_AUG_21.csv missing entry 2021-08-12T15:29:00+05:30
- `2021-08-18`: `missing_entry_or_exit_timestamp`. NIFTY_16550_PE_26_AUG_21.csv missing entry 2021-08-18T15:29:00+05:30
- `2021-08-26`: `missing_entry_or_exit_timestamp`. NIFTY_16650_PE_02_SEP_21.csv missing entry 2021-08-26T15:29:00+05:30
- `2021-09-02`: `missing_entry_or_exit_timestamp`. NIFTY_17250_CE_09_SEP_21.csv missing entry 2021-09-02T15:29:00+05:30
- `2021-09-09`: `missing_entry_or_exit_timestamp`. NIFTY_17350_CE_16_SEP_21.csv missing entry 2021-09-09T15:29:00+05:30
- `2021-09-16`: `missing_entry_or_exit_timestamp`. NIFTY_17650_CE_23_SEP_21.csv missing entry 2021-09-16T15:29:00+05:30
- `2021-09-23`: `missing_entry_or_exit_timestamp`. NIFTY_17850_CE_30_SEP_21.csv missing entry 2021-09-23T15:29:00+05:30
- `2021-09-30`: `missing_entry_or_exit_timestamp`. NIFTY_17600_PE_07_OCT_21.csv missing entry 2021-09-30T15:29:00+05:30
- `2021-10-07`: `missing_entry_or_exit_timestamp`. NIFTY_17800_PE_14_OCT_21.csv missing entry 2021-10-07T15:29:00+05:30
- `2021-10-14`: `missing_entry_or_exit_timestamp`. NIFTY_18350_CE_21_OCT_21.csv missing entry 2021-10-14T15:29:00+05:30
- `2021-10-21`: `missing_entry_or_exit_timestamp`. NIFTY_18200_CE_28_OCT_21.csv missing entry 2021-10-21T15:29:00+05:30
- `2021-10-28`: `missing_entry_or_exit_timestamp`. NIFTY_17850_PE_03_NOV_21.csv missing entry 2021-10-28T15:29:00+05:30
- `2021-11-03`: `missing_entry_or_exit_timestamp`. NIFTY_17850_PE_11_NOV_21.csv missing entry 2021-11-03T15:29:00+05:30; NIFTY_17850_PE_11_NOV_21.csv missing exit 2021-11-04T09:16:00+05:30
- `2021-11-04`: `missing_entry_or_exit_timestamp`. NIFTY_17850_PE_11_NOV_21.csv missing entry 2021-11-04T15:29:00+05:30
- `2021-11-11`: `missing_entry_or_exit_timestamp`. NIFTY_17900_CE_18_NOV_21.csv missing entry 2021-11-11T15:29:00+05:30
- `2021-11-18`: `missing_entry_or_exit_timestamp`. NIFTY_17750_PE_25_NOV_21.csv missing entry 2021-11-18T15:29:00+05:30
- `2021-11-25`: `missing_entry_or_exit_timestamp`. NIFTY_17550_CE_02_DEC_21.csv missing entry 2021-11-25T15:29:00+05:30
- `2021-12-02`: `missing_entry_or_exit_timestamp`. NIFTY_17400_CE_09_DEC_21.csv missing entry 2021-12-02T15:29:00+05:30
- `2021-12-09`: `missing_entry_or_exit_timestamp`. NIFTY_17500_CE_16_DEC_21.csv missing entry 2021-12-09T15:29:00+05:30
- `2021-12-16`: `missing_entry_or_exit_timestamp`. NIFTY_17300_CE_23_DEC_21.csv missing entry 2021-12-16T15:29:00+05:30
- `2021-12-23`: `missing_entry_or_exit_timestamp`. NIFTY_17050_PE_30_DEC_21.csv missing entry 2021-12-23T15:29:00+05:30
- `2021-12-30`: `missing_entry_or_exit_timestamp`. NIFTY_17250_PE_06_JAN_22.csv missing entry 2021-12-30T15:29:00+05:30
- `2022-01-06`: `missing_entry_or_exit_timestamp`. NIFTY_17750_CE_13_JAN_22.csv missing entry 2022-01-06T15:29:00+05:30
- `2022-01-13`: `missing_entry_or_exit_timestamp`. NIFTY_18250_CE_20_JAN_22.csv missing entry 2022-01-13T15:29:00+05:30
- `2022-01-20`: `missing_entry_or_exit_timestamp`. NIFTY_17800_PE_27_JAN_22.csv missing entry 2022-01-20T15:29:00+05:30
- `2022-01-27`: `missing_entry_or_exit_timestamp`. NIFTY_17150_CE_03_FEB_22.csv missing entry 2022-01-27T15:29:00+05:30
- `2022-02-03`: `missing_entry_or_exit_timestamp`. NIFTY_17500_PE_10_FEB_22.csv missing entry 2022-02-03T15:29:00+05:30
- `2022-02-10`: `missing_entry_or_exit_timestamp`. NIFTY_17600_CE_17_FEB_22.csv missing entry 2022-02-10T15:29:00+05:30
- `2022-02-17`: `missing_entry_or_exit_timestamp`. NIFTY_17300_PE_24_FEB_22.csv missing entry 2022-02-17T15:29:00+05:30
- `2022-02-24`: `missing_entry_or_exit_timestamp`. NIFTY_16200_PE_03_MAR_22.csv missing entry 2022-02-24T15:29:00+05:30
- `2022-03-03`: `missing_entry_or_exit_timestamp`. NIFTY_16500_PE_10_MAR_22.csv missing entry 2022-03-03T15:29:00+05:30
- `2022-03-10`: `missing_entry_or_exit_timestamp`. NIFTY_16550_PE_17_MAR_22.csv missing entry 2022-03-10T15:29:00+05:30
- `2022-03-17`: `missing_entry_or_exit_timestamp`. NIFTY_17300_CE_24_MAR_22.csv missing entry 2022-03-17T15:29:00+05:30
- `2022-03-24`: `missing_entry_or_exit_timestamp`. NIFTY_17200_PE_31_MAR_22.csv missing entry 2022-03-24T15:29:00+05:30
- `2022-03-31`: `missing_entry_or_exit_timestamp`. NIFTY_17450_PE_07_APR_22.csv missing entry 2022-03-31T15:29:00+05:30
- `2022-04-07`: `missing_entry_or_exit_timestamp`. NIFTY_17650_PE_13_APR_22.csv missing entry 2022-04-07T15:29:00+05:30
- `2022-04-13`: `missing_entry_or_exit_timestamp`. NIFTY_17450_PE_21_APR_22.csv missing entry 2022-04-13T15:29:00+05:30
- `2022-04-21`: `missing_entry_or_exit_timestamp`. NIFTY_17400_CE_28_APR_22.csv missing entry 2022-04-21T15:29:00+05:30
- `2022-04-28`: `missing_entry_or_exit_timestamp`. NIFTY_17250_CE_05_MAY_22.csv missing entry 2022-04-28T15:29:00+05:30
- `2022-05-05`: `missing_entry_or_exit_timestamp`. NIFTY_16650_PE_12_MAY_22.csv missing entry 2022-05-05T15:29:00+05:30
- `2022-05-12`: `missing_entry_or_exit_timestamp`. NIFTY_15850_PE_19_MAY_22.csv missing entry 2022-05-12T15:29:00+05:30
- `2022-05-19`: `missing_entry_or_exit_timestamp`. NIFTY_15850_PE_26_MAY_22.csv missing entry 2022-05-19T15:29:00+05:30
- `2022-05-26`: `missing_entry_or_exit_timestamp`. NIFTY_16200_CE_02_JUN_22.csv missing entry 2022-05-26T15:29:00+05:30
- `2022-06-02`: `missing_entry_or_exit_timestamp`. NIFTY_16650_CE_09_JUN_22.csv missing entry 2022-06-02T15:29:00+05:30
- `2022-06-09`: `missing_entry_or_exit_timestamp`. NIFTY_16500_CE_16_JUN_22.csv missing entry 2022-06-09T15:29:00+05:30
- `2022-06-16`: `missing_entry_or_exit_timestamp`. NIFTY_15350_PE_23_JUN_22.csv missing entry 2022-06-16T15:29:00+05:30
- `2022-06-23`: `missing_entry_or_exit_timestamp`. NIFTY_15600_CE_30_JUN_22.csv missing entry 2022-06-23T15:29:00+05:30
- `2022-06-30`: `missing_entry_or_exit_timestamp`. NIFTY_15750_PE_07_JUL_22.csv missing entry 2022-06-30T15:29:00+05:30
- `2022-07-07`: `missing_entry_or_exit_timestamp`. NIFTY_16150_CE_14_JUL_22.csv missing entry 2022-07-07T15:29:00+05:30
- `2022-07-14`: `missing_entry_or_exit_timestamp`. NIFTY_15950_PE_21_JUL_22.csv missing entry 2022-07-14T15:29:00+05:30
- `2022-07-21`: `missing_entry_or_exit_timestamp`. NIFTY_16600_CE_28_JUL_22.csv missing entry 2022-07-21T15:29:00+05:30
- `2022-07-28`: `missing_entry_or_exit_timestamp`. NIFTY_16900_CE_04_AUG_22.csv missing entry 2022-07-28T15:29:00+05:30
- `2022-08-04`: `missing_entry_or_exit_timestamp`. NIFTY_17350_CE_11_AUG_22.csv missing entry 2022-08-04T15:29:00+05:30
- `2022-08-11`: `missing_entry_or_exit_timestamp`. NIFTY_17650_PE_18_AUG_22.csv missing entry 2022-08-11T15:29:00+05:30
- `2022-08-18`: `missing_entry_or_exit_timestamp`. NIFTY_17950_CE_25_AUG_22.csv missing entry 2022-08-18T15:29:00+05:30
- `2022-08-25`: `missing_entry_or_exit_timestamp`. NIFTY_17500_PE_01_SEP_22.csv missing entry 2022-08-25T15:29:00+05:30
- `2022-09-01`: `missing_entry_or_exit_timestamp`. NIFTY_17550_PE_08_SEP_22.csv missing entry 2022-09-01T15:29:00+05:30
- `2022-09-08`: `missing_entry_or_exit_timestamp`. NIFTY_17800_CE_15_SEP_22.csv missing entry 2022-09-08T15:29:00+05:30
- `2022-09-15`: `missing_entry_or_exit_timestamp`. NIFTY_17850_PE_22_SEP_22.csv missing entry 2022-09-15T15:29:00+05:30
- `2022-09-22`: `missing_entry_or_exit_timestamp`. NIFTY_17650_CE_29_SEP_22.csv missing entry 2022-09-22T15:29:00+05:30
- `2022-09-29`: `missing_entry_or_exit_timestamp`. NIFTY_16850_PE_06_OCT_22.csv missing entry 2022-09-29T15:29:00+05:30
- `2022-10-06`: `missing_entry_or_exit_timestamp`. NIFTY_17300_PE_13_OCT_22.csv missing entry 2022-10-06T15:29:00+05:30
- `2022-10-13`: `missing_entry_or_exit_timestamp`. NIFTY_17000_PE_20_OCT_22.csv missing entry 2022-10-13T15:29:00+05:30
- `2022-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_17550_CE_27_OCT_22.csv missing entry 2022-10-20T15:29:00+05:30
- `2022-10-21`: `missing_entry_or_exit_timestamp`. NIFTY_17600_PE_27_OCT_22.csv missing exit 2022-10-24T09:16:00+05:30
- `2022-10-24`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2022-10-24T15:15:00+05:30
- `2022-10-27`: `missing_entry_or_exit_timestamp`. NIFTY_17750_CE_03_NOV_22.csv missing entry 2022-10-27T15:29:00+05:30
- `2022-11-03`: `missing_entry_or_exit_timestamp`. NIFTY_18050_PE_10_NOV_22.csv missing entry 2022-11-03T15:29:00+05:30
- `2022-11-10`: `missing_entry_or_exit_timestamp`. NIFTY_18050_CE_17_NOV_22.csv missing entry 2022-11-10T15:29:00+05:30
- `2022-11-17`: `missing_entry_or_exit_timestamp`. NIFTY_18350_PE_24_NOV_22.csv missing entry 2022-11-17T15:29:00+05:30
- `2022-11-24`: `missing_entry_or_exit_timestamp`. NIFTY_18500_CE_01_DEC_22.csv missing entry 2022-11-24T15:29:00+05:30
- `2022-12-01`: `missing_entry_or_exit_timestamp`. NIFTY_18800_PE_08_DEC_22.csv missing entry 2022-12-01T15:29:00+05:30
- `2022-12-08`: `missing_entry_or_exit_timestamp`. NIFTY_18600_CE_15_DEC_22.csv missing entry 2022-12-08T15:29:00+05:30
- `2022-12-15`: `missing_entry_or_exit_timestamp`. NIFTY_18400_PE_22_DEC_22.csv missing entry 2022-12-15T15:29:00+05:30
- `2022-12-22`: `missing_entry_or_exit_timestamp`. NIFTY_18100_PE_29_DEC_22.csv missing entry 2022-12-22T15:29:00+05:30
- `2022-12-29`: `missing_entry_or_exit_timestamp`. NIFTY_18200_CE_05_JAN_23.csv missing entry 2022-12-29T15:29:00+05:30
- `2023-01-05`: `missing_entry_or_exit_timestamp`. NIFTY_18000_CE_12_JAN_23.csv missing entry 2023-01-05T15:29:00+05:30
- `2023-01-12`: `missing_entry_or_exit_timestamp`. NIFTY_17850_CE_19_JAN_23.csv missing entry 2023-01-12T15:29:00+05:30
- `2023-01-19`: `missing_entry_or_exit_timestamp`. NIFTY_18100_PE_25_JAN_23.csv missing entry 2023-01-19T15:29:00+05:30
- `2023-01-25`: `missing_entry_or_exit_timestamp`. NIFTY_17900_PE_02_FEB_23.csv missing entry 2023-01-25T15:29:00+05:30
- `2023-02-02`: `missing_entry_or_exit_timestamp`. NIFTY_17600_CE_09_FEB_23.csv missing entry 2023-02-02T15:29:00+05:30
- `2023-02-09`: `missing_entry_or_exit_timestamp`. NIFTY_17900_CE_16_FEB_23.csv missing entry 2023-02-09T15:29:00+05:30
- `2023-02-16`: `missing_entry_or_exit_timestamp`. NIFTY_18000_PE_23_FEB_23.csv missing entry 2023-02-16T15:29:00+05:30
- `2023-02-23`: `missing_entry_or_exit_timestamp`. NIFTY_17500_PE_02_MAR_23.csv missing entry 2023-02-23T15:29:00+05:30
- `2023-03-02`: `missing_entry_or_exit_timestamp`. NIFTY_17300_PE_09_MAR_23.csv missing entry 2023-03-02T15:29:00+05:30
- `2023-03-09`: `missing_entry_or_exit_timestamp`. NIFTY_17600_PE_16_MAR_23.csv missing entry 2023-03-09T15:29:00+05:30
- `2023-03-16`: `missing_entry_or_exit_timestamp`. NIFTY_17000_CE_23_MAR_23.csv missing entry 2023-03-16T15:29:00+05:30
- `2023-03-23`: `missing_entry_or_exit_timestamp`. NIFTY_17050_PE_29_MAR_23.csv missing entry 2023-03-23T15:29:00+05:30
- `2023-03-29`: `missing_entry_or_exit_timestamp`. NIFTY_17100_CE_06_APR_23.csv missing entry 2023-03-29T15:29:00+05:30
- `2023-04-06`: `missing_entry_or_exit_timestamp`. NIFTY_17600_CE_13_APR_23.csv missing entry 2023-04-06T15:29:00+05:30
- `2023-04-13`: `missing_entry_or_exit_timestamp`. NIFTY_17850_CE_20_APR_23.csv missing entry 2023-04-13T15:29:00+05:30
- `2023-04-20`: `missing_entry_or_exit_timestamp`. NIFTY_17600_CE_27_APR_23.csv missing entry 2023-04-20T15:29:00+05:30
- `2023-04-27`: `missing_entry_or_exit_timestamp`. NIFTY_17900_CE_04_MAY_23.csv missing entry 2023-04-27T15:29:00+05:30
- `2023-05-04`: `missing_entry_or_exit_timestamp`. NIFTY_18250_CE_11_MAY_23.csv missing entry 2023-05-04T15:29:00+05:30
- `2023-05-11`: `missing_entry_or_exit_timestamp`. NIFTY_18300_PE_18_MAY_23.csv missing entry 2023-05-11T15:29:00+05:30
- `2023-05-18`: `missing_entry_or_exit_timestamp`. NIFTY_18150_PE_25_MAY_23.csv missing entry 2023-05-18T15:29:00+05:30
- `2023-05-25`: `missing_entry_or_exit_timestamp`. NIFTY_18350_CE_01_JUN_23.csv missing entry 2023-05-25T15:29:00+05:30
- `2023-06-01`: `missing_entry_or_exit_timestamp`. NIFTY_18500_PE_08_JUN_23.csv missing entry 2023-06-01T15:29:00+05:30
- `2023-06-08`: `missing_entry_or_exit_timestamp`. NIFTY_18650_PE_15_JUN_23.csv missing entry 2023-06-08T15:29:00+05:30
- `2023-06-15`: `missing_entry_or_exit_timestamp`. NIFTY_18700_PE_22_JUN_23.csv missing entry 2023-06-15T15:29:00+05:30
- `2023-06-22`: `missing_entry_or_exit_timestamp`. NIFTY_18800_PE_28_JUN_23.csv missing entry 2023-06-22T15:29:00+05:30; NIFTY_18800_PE_28_JUN_23.csv missing exit 2023-06-23T09:16:00+05:30
- `2023-06-23`: `missing_entry_or_exit_timestamp`. NIFTY_18650_PE_28_JUN_23.csv missing entry 2023-06-23T15:29:00+05:30; NIFTY_18650_PE_28_JUN_23.csv missing exit 2023-06-26T09:16:00+05:30
- `2023-06-26`: `missing_entry_or_exit_timestamp`. NIFTY_18700_CE_28_JUN_23.csv missing entry 2023-06-26T15:29:00+05:30; NIFTY_18700_CE_28_JUN_23.csv missing exit 2023-06-27T09:16:00+05:30
- `2023-06-27`: `missing_entry_or_exit_timestamp`. NIFTY_18800_CE_28_JUN_23.csv missing entry 2023-06-27T15:29:00+05:30
- `2023-06-28`: `missing_entry_or_exit_timestamp`. NIFTY_19000_CE_29_JUN_23.csv missing entry 2023-06-28T15:29:00+05:30; NIFTY_19000_CE_29_JUN_23.csv missing exit 2023-06-30T09:16:00+05:30
- `2023-07-06`: `missing_entry_or_exit_timestamp`. NIFTY_19500_CE_13_JUL_23.csv missing entry 2023-07-06T15:29:00+05:30
- `2023-07-13`: `missing_entry_or_exit_timestamp`. NIFTY_19450_PE_20_JUL_23.csv missing entry 2023-07-13T15:29:00+05:30
- `2023-07-20`: `missing_entry_or_exit_timestamp`. NIFTY_19950_CE_27_JUL_23.csv missing entry 2023-07-20T15:29:00+05:30
- `2023-07-27`: `missing_entry_or_exit_timestamp`. NIFTY_19700_PE_03_AUG_23.csv missing entry 2023-07-27T15:29:00+05:30
- `2023-08-03`: `missing_entry_or_exit_timestamp`. NIFTY_19400_PE_10_AUG_23.csv missing entry 2023-08-03T15:29:00+05:30
- `2023-08-10`: `missing_entry_or_exit_timestamp`. NIFTY_19550_PE_17_AUG_23.csv missing entry 2023-08-10T15:29:00+05:30
- `2023-08-17`: `missing_entry_or_exit_timestamp`. NIFTY_19350_PE_24_AUG_23.csv missing entry 2023-08-17T15:29:00+05:30
- `2023-08-24`: `missing_entry_or_exit_timestamp`. NIFTY_19400_PE_31_AUG_23.csv missing entry 2023-08-24T15:29:00+05:30
- `2023-08-31`: `missing_entry_or_exit_timestamp`. NIFTY_19300_PE_07_SEP_23.csv missing entry 2023-08-31T15:29:00+05:30
- `2023-09-07`: `missing_entry_or_exit_timestamp`. NIFTY_19700_CE_14_SEP_23.csv missing entry 2023-09-07T15:29:00+05:30
- `2023-09-14`: `missing_entry_or_exit_timestamp`. NIFTY_20100_CE_21_SEP_23.csv missing entry 2023-09-14T15:29:00+05:30
- `2023-09-21`: `missing_entry_or_exit_timestamp`. NIFTY_19750_PE_28_SEP_23.csv missing entry 2023-09-21T15:29:00+05:30
- `2023-09-28`: `missing_entry_or_exit_timestamp`. NIFTY_19550_PE_05_OCT_23.csv missing entry 2023-09-28T15:29:00+05:30
- `2023-10-05`: `missing_entry_or_exit_timestamp`. NIFTY_19550_CE_12_OCT_23.csv missing entry 2023-10-05T15:29:00+05:30
- `2023-10-12`: `missing_entry_or_exit_timestamp`. NIFTY_19800_PE_19_OCT_23.csv missing entry 2023-10-12T15:29:00+05:30
- `2023-10-19`: `missing_entry_or_exit_timestamp`. NIFTY_19600_PE_26_OCT_23.csv missing entry 2023-10-19T15:29:00+05:30
- `2023-10-26`: `missing_entry_or_exit_timestamp`. NIFTY_18850_PE_02_NOV_23.csv missing entry 2023-10-26T15:29:00+05:30
- `2023-11-02`: `missing_entry_or_exit_timestamp`. NIFTY_19150_CE_09_NOV_23.csv missing entry 2023-11-02T15:29:00+05:30
- `2023-11-09`: `missing_entry_or_exit_timestamp`. NIFTY_19400_PE_16_NOV_23.csv missing entry 2023-11-09T15:29:00+05:30
- `2023-11-10`: `missing_entry_or_exit_timestamp`. NIFTY_19450_CE_16_NOV_23.csv missing exit 2023-11-12T09:16:00+05:30
- `2023-11-12`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2023-11-12T15:15:00+05:30
- `2023-11-16`: `missing_entry_or_exit_timestamp`. NIFTY_19750_PE_23_NOV_23.csv missing entry 2023-11-16T15:29:00+05:30
- `2023-11-23`: `missing_entry_or_exit_timestamp`. NIFTY_19800_PE_30_NOV_23.csv missing entry 2023-11-23T15:29:00+05:30
- `2023-11-30`: `missing_entry_or_exit_timestamp`. NIFTY_20150_CE_07_DEC_23.csv missing entry 2023-11-30T15:29:00+05:30
- `2023-12-07`: `missing_entry_or_exit_timestamp`. NIFTY_20900_CE_14_DEC_23.csv missing entry 2023-12-07T15:29:00+05:30
- `2023-12-14`: `missing_entry_or_exit_timestamp`. NIFTY_21200_CE_21_DEC_23.csv missing entry 2023-12-14T15:29:00+05:30
- `2023-12-21`: `missing_entry_or_exit_timestamp`. NIFTY_21300_CE_28_DEC_23.csv missing entry 2023-12-21T15:29:00+05:30
- `2023-12-28`: `missing_entry_or_exit_timestamp`. NIFTY_21750_CE_04_JAN_24.csv missing entry 2023-12-28T15:29:00+05:30
- `2024-01-04`: `missing_entry_or_exit_timestamp`. NIFTY_21650_CE_11_JAN_24.csv missing entry 2024-01-04T15:29:00+05:30
- `2024-01-11`: `missing_entry_or_exit_timestamp`. NIFTY_21650_CE_18_JAN_24.csv missing entry 2024-01-11T15:29:00+05:30
- `2024-01-18`: `missing_entry_or_exit_timestamp`. NIFTY_21500_CE_25_JAN_24.csv missing entry 2024-01-18T15:29:00+05:30
- `2024-01-25`: `missing_entry_or_exit_timestamp`. NIFTY_21350_CE_01_FEB_24.csv missing entry 2024-01-25T15:29:00+05:30
- `2024-02-01`: `missing_entry_or_exit_timestamp`. NIFTY_21700_PE_08_FEB_24.csv missing entry 2024-02-01T15:29:00+05:30
- `2024-02-08`: `missing_entry_or_exit_timestamp`. NIFTY_21750_PE_15_FEB_24.csv missing entry 2024-02-08T15:29:00+05:30
- `2024-02-15`: `missing_entry_or_exit_timestamp`. NIFTY_21950_CE_22_FEB_24.csv missing entry 2024-02-15T15:29:00+05:30
- `2024-02-22`: `missing_entry_or_exit_timestamp`. NIFTY_22200_CE_29_FEB_24.csv missing entry 2024-02-22T15:29:00+05:30
- `2024-02-29`: `missing_entry_or_exit_timestamp`. NIFTY_22050_CE_07_MAR_24.csv missing entry 2024-02-29T15:29:00+05:30
- `2024-03-02`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2024-03-02T15:15:00+05:30
- `2024-03-07`: `missing_entry_or_exit_timestamp`. NIFTY_22500_PE_14_MAR_24.csv missing entry 2024-03-07T15:29:00+05:30
- `2024-03-14`: `missing_entry_or_exit_timestamp`. NIFTY_22150_CE_21_MAR_24.csv missing entry 2024-03-14T15:29:00+05:30
- `2024-03-21`: `missing_entry_or_exit_timestamp`. NIFTY_22000_PE_28_MAR_24.csv missing entry 2024-03-21T15:29:00+05:30
- `2024-03-28`: `missing_entry_or_exit_timestamp`. NIFTY_22350_PE_04_APR_24.csv missing entry 2024-03-28T15:29:00+05:30
- `2024-04-04`: `missing_entry_or_exit_timestamp`. NIFTY_22550_CE_10_APR_24.csv missing entry 2024-04-04T15:29:00+05:30
- `2024-04-10`: `missing_entry_or_exit_timestamp`. NIFTY_22750_CE_18_APR_24.csv missing entry 2024-04-10T15:29:00+05:30
- `2024-04-18`: `missing_entry_or_exit_timestamp`. NIFTY_22050_PE_25_APR_24.csv missing entry 2024-04-18T15:29:00+05:30
- `2024-04-25`: `missing_entry_or_exit_timestamp`. NIFTY_22550_CE_02_MAY_24.csv missing entry 2024-04-25T15:29:00+05:30
- `2024-05-02`: `missing_entry_or_exit_timestamp`. NIFTY_22650_PE_09_MAY_24.csv missing entry 2024-05-02T15:29:00+05:30
- `2024-05-09`: `missing_entry_or_exit_timestamp`. NIFTY_21950_PE_16_MAY_24.csv missing entry 2024-05-09T15:29:00+05:30
- `2024-05-16`: `missing_entry_or_exit_timestamp`. NIFTY_22400_CE_23_MAY_24.csv missing entry 2024-05-16T15:29:00+05:30
- `2024-05-18`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2024-05-18T15:15:00+05:30
- `2024-05-23`: `missing_entry_or_exit_timestamp`. NIFTY_22950_CE_30_MAY_24.csv missing entry 2024-05-23T15:29:00+05:30
- `2024-05-30`: `missing_entry_or_exit_timestamp`. NIFTY_22550_CE_06_JUN_24.csv missing entry 2024-05-30T15:29:00+05:30
- `2024-06-06`: `missing_entry_or_exit_timestamp`. NIFTY_22850_CE_13_JUN_24.csv missing entry 2024-06-06T15:29:00+05:30
- `2024-06-13`: `missing_entry_or_exit_timestamp`. NIFTY_23400_CE_20_JUN_24.csv missing entry 2024-06-13T15:29:00+05:30
- `2024-06-20`: `missing_entry_or_exit_timestamp`. NIFTY_23600_CE_27_JUN_24.csv missing entry 2024-06-20T15:29:00+05:30
- `2024-06-27`: `missing_entry_or_exit_timestamp`. NIFTY_24050_CE_04_JUL_24.csv missing entry 2024-06-27T15:29:00+05:30
- `2024-07-04`: `missing_entry_or_exit_timestamp`. NIFTY_24300_PE_11_JUL_24.csv missing entry 2024-07-04T15:29:00+05:30
- `2024-07-11`: `missing_entry_or_exit_timestamp`. NIFTY_24350_CE_18_JUL_24.csv missing entry 2024-07-11T15:29:00+05:30
- `2024-07-18`: `missing_entry_or_exit_timestamp`. NIFTY_24800_CE_25_JUL_24.csv missing entry 2024-07-18T15:29:00+05:30
- `2024-07-25`: `missing_entry_or_exit_timestamp`. NIFTY_24400_CE_01_AUG_24.csv missing entry 2024-07-25T15:29:00+05:30
- `2024-08-01`: `missing_entry_or_exit_timestamp`. NIFTY_25000_CE_08_AUG_24.csv missing entry 2024-08-01T15:29:00+05:30
- `2024-08-08`: `missing_entry_or_exit_timestamp`. NIFTY_24100_PE_14_AUG_24.csv missing entry 2024-08-08T15:29:00+05:30
- `2024-08-14`: `missing_entry_or_exit_timestamp`. NIFTY_24150_PE_22_AUG_24.csv missing entry 2024-08-14T15:29:00+05:30
- `2024-08-22`: `missing_entry_or_exit_timestamp`. NIFTY_24800_PE_29_AUG_24.csv missing entry 2024-08-22T15:29:00+05:30
- `2024-08-29`: `missing_entry_or_exit_timestamp`. NIFTY_25150_CE_05_SEP_24.csv missing entry 2024-08-29T15:29:00+05:30
- `2024-09-05`: `missing_entry_or_exit_timestamp`. NIFTY_25150_PE_12_SEP_24.csv missing entry 2024-09-05T15:29:00+05:30
- `2024-09-12`: `missing_entry_or_exit_timestamp`. NIFTY_25300_CE_19_SEP_24.csv missing entry 2024-09-12T15:29:00+05:30
- `2024-09-19`: `missing_entry_or_exit_timestamp`. NIFTY_25450_PE_26_SEP_24.csv missing entry 2024-09-19T15:29:00+05:30
- `2024-09-26`: `missing_entry_or_exit_timestamp`. NIFTY_26200_CE_03_OCT_24.csv missing entry 2024-09-26T15:29:00+05:30
- `2024-10-03`: `missing_entry_or_exit_timestamp`. NIFTY_25250_PE_10_OCT_24.csv missing entry 2024-10-03T15:29:00+05:30
- `2024-10-10`: `missing_entry_or_exit_timestamp`. NIFTY_25000_PE_17_OCT_24.csv missing entry 2024-10-10T15:29:00+05:30
- `2024-10-17`: `missing_entry_or_exit_timestamp`. NIFTY_24750_PE_24_OCT_24.csv missing entry 2024-10-17T15:29:00+05:30
- `2024-10-24`: `missing_entry_or_exit_timestamp`. NIFTY_24400_CE_31_OCT_24.csv missing entry 2024-10-24T15:29:00+05:30
- `2024-10-31`: `missing_entry_or_exit_timestamp`. NIFTY_24250_CE_07_NOV_24.csv missing entry 2024-10-31T15:29:00+05:30; NIFTY_24250_CE_07_NOV_24.csv missing exit 2024-11-01T09:16:00+05:30
- `2024-11-01`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2024-11-01T15:15:00+05:30
- `2024-11-07`: `missing_entry_or_exit_timestamp`. NIFTY_24200_PE_14_NOV_24.csv missing entry 2024-11-07T15:29:00+05:30
- `2024-11-14`: `missing_entry_or_exit_timestamp`. NIFTY_23550_CE_21_NOV_24.csv missing entry 2024-11-14T15:29:00+05:30
- `2024-11-21`: `missing_entry_or_exit_timestamp`. NIFTY_23350_CE_28_NOV_24.csv missing entry 2024-11-21T15:29:00+05:30
- `2024-11-28`: `missing_entry_or_exit_timestamp`. NIFTY_23950_PE_05_DEC_24.csv missing entry 2024-11-28T15:29:00+05:30
- `2024-12-05`: `missing_entry_or_exit_timestamp`. NIFTY_24700_CE_12_DEC_24.csv missing entry 2024-12-05T15:29:00+05:30
- `2024-12-12`: `missing_entry_or_exit_timestamp`. NIFTY_24550_PE_19_DEC_24.csv missing entry 2024-12-12T15:29:00+05:30
- `2024-12-19`: `missing_entry_or_exit_timestamp`. NIFTY_23950_CE_26_DEC_24.csv missing entry 2024-12-19T15:29:00+05:30
- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25850_PE_28_OCT_25.csv missing exit 2025-10-21T09:16:00+05:30
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2026-03-18`: `missing_option_file`. Missing: NIFTY_23750_PE_24_MAR_26.csv
- `2026-04-30`: `missing_entry_or_exit_timestamp`. NIFTY_24050_CE_05_MAY_26.csv missing exit 2026-05-04T09:16:00+05:30
- `2026-05-04`: `missing_entry_or_exit_timestamp`. NIFTY_24100_PE_05_MAY_26.csv missing entry 2026-05-04T15:29:00+05:30; NIFTY_24100_PE_05_MAY_26.csv missing exit 2026-05-05T09:16:00+05:30
- `2026-05-05`: `missing_entry_or_exit_timestamp`. NIFTY_24050_CE_12_MAY_26.csv missing entry 2026-05-05T15:29:00+05:30; NIFTY_24050_CE_12_MAY_26.csv missing exit 2026-05-06T09:16:00+05:30
- `2026-05-06`: `missing_entry_or_exit_timestamp`. NIFTY_24350_CE_12_MAY_26.csv missing entry 2026-05-06T15:29:00+05:30; NIFTY_24350_CE_12_MAY_26.csv missing exit 2026-05-07T09:16:00+05:30
- `2026-05-07`: `missing_entry_or_exit_timestamp`. NIFTY_24350_PE_12_MAY_26.csv missing entry 2026-05-07T15:29:00+05:30; NIFTY_24350_PE_12_MAY_26.csv missing exit 2026-05-08T09:16:00+05:30
- `2026-05-08`: `missing_entry_or_exit_timestamp`. NIFTY_24200_PE_12_MAY_26.csv missing entry 2026-05-08T15:29:00+05:30; NIFTY_24200_PE_12_MAY_26.csv missing exit 2026-05-11T09:16:00+05:30
- `2026-05-11`: `missing_entry_or_exit_timestamp`. NIFTY_23800_PE_12_MAY_26.csv missing entry 2026-05-11T15:29:00+05:30; NIFTY_23800_PE_12_MAY_26.csv missing exit 2026-05-12T09:16:00+05:30
- `2026-06-03`: `missing_entry_or_exit_timestamp`. NIFTY_23400_CE_09_JUN_26.csv missing exit 2026-06-04T09:16:00+05:30
- `2026-06-04`: `missing_entry_or_exit_timestamp`. NIFTY_23450_CE_09_JUN_26.csv missing entry 2026-06-04T15:29:00+05:30; NIFTY_23450_CE_09_JUN_26.csv missing exit 2026-06-05T09:16:00+05:30
- `2026-06-05`: `missing_entry_or_exit_timestamp`. NIFTY_23350_PE_09_JUN_26.csv missing entry 2026-06-05T15:29:00+05:30; NIFTY_23350_PE_09_JUN_26.csv missing exit 2026-06-08T09:16:00+05:30
- `2026-06-08`: `missing_entry_or_exit_timestamp`. NIFTY_23100_PE_09_JUN_26.csv missing entry 2026-06-08T15:29:00+05:30; NIFTY_23100_PE_09_JUN_26.csv missing exit 2026-06-09T09:16:00+05:30
- `2026-06-16`: `missing_entry_or_exit_timestamp`. NIFTY_24000_CE_23_JUN_26.csv missing exit 2026-06-17T09:16:00+05:30
- `2026-06-17`: `missing_entry_or_exit_timestamp`. NIFTY_24100_CE_23_JUN_26.csv missing entry 2026-06-17T15:29:00+05:30; NIFTY_24100_CE_23_JUN_26.csv missing exit 2026-06-18T09:16:00+05:30
- `2026-06-18`: `missing_entry_or_exit_timestamp`. NIFTY_24200_CE_23_JUN_26.csv missing entry 2026-06-18T15:29:00+05:30; NIFTY_24200_CE_23_JUN_26.csv missing exit 2026-06-19T09:16:00+05:30
- `2026-06-19`: `no_next_trading_day`. No next trading day in dataset.

## Remarks

- Exact timestamp matching; no nearest-candle fallback.
- The 15:15 spot row is the 15:30 close proxy; 15:29 option open is the entry proxy.
- Expiry folder dates are the source of truth for expiry selection.
- Lot sizes are applied by expiry date to maintain ~300 quantity throughout the period.
