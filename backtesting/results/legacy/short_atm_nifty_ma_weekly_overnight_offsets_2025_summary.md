# 2025 Overnight Weekly Short NIFTY 25-SMA Strike-Offset Backtest

## Strategy Details

- Signal source: NIFTY 15-minute close
- Signal bar time: `15:15` row as `15:30` close proxy
- MA rule: 25-SMA of spot closes including the signal bar
- Direction rule: above SMA -> short PE; below SMA -> short CE; equal -> no trade
- Strike ranges: OTM 100/200/300/400/500 and ITM 100/200/300, each tested independently
- OTM/ITM is interpreted relative to the sold option side
- Entry execution time: `15:29` option open
- Exit execution time: next trading day `09:16` option open
- Expiry rule: first weekly expiry strictly after entry date
- ATM reference rule: nearest 50 using the spot signal close
- Contract multiplier: 65 x 4 = 260 rupees per option point
- Execution slippage: 1.00 point per order, applied against every entry and exit
- Brokerage rule: Rs 25 per order, so one completed short leg pays Rs 50

## Range Comparison

| Range | Traded | Skipped | CE Sell | PE Sell | Wins | Losses | Max DD | Net P/L | Brokerage | Gross P/L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| OTM_100 | 245 | 4 | 125 | 120 | 145 | 100 | 58480.00 | 363236.80 | 12250.00 | 375486.80 |
| OTM_200 | 244 | 5 | 125 | 119 | 149 | 95 | 45259.00 | 281303.60 | 12200.00 | 293503.60 |
| OTM_300 | 245 | 4 | 125 | 120 | 147 | 98 | 34482.00 | 199936.00 | 12250.00 | 212186.00 |
| OTM_400 | 244 | 5 | 124 | 120 | 129 | 115 | 26823.00 | 135545.00 | 12200.00 | 147745.00 |
| OTM_500 | 245 | 4 | 125 | 120 | 103 | 142 | 28324.00 | 86768.40 | 12250.00 | 99018.40 |
| ITM_100 | 245 | 4 | 125 | 120 | 134 | 111 | 95435.00 | 514952.00 | 12250.00 | 527202.00 |
| ITM_200 | 245 | 4 | 125 | 120 | 133 | 112 | 113666.00 | 578795.00 | 12250.00 | 591045.00 |
| ITM_300 | 245 | 4 | 125 | 120 | 131 | 114 | 125171.00 | 623772.40 | 12250.00 | 636022.40 |

## Range Details

### OTM_100

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `145`
- Losing days: `100`
- Break-even days: `0`
- Max profit day: `2025-05-09` with net P/L `48780.60`
- Max loss day: `2025-08-14` with net P/L `-47630.00`
- Max consecutive wins: `7`
- Max consecutive losses: `5`
- Max drawdown: `58480.00`
- Total Profit/Loss: `363236.80`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `375486.80`

### OTM_200

- Traded days: `244`
- Skipped days: `5`
- CE-sell count: `125`
- PE-sell count: `119`
- Winning days: `149`
- Losing days: `95`
- Break-even days: `0`
- Max profit day: `2025-04-07` with net P/L `42798.00`
- Max loss day: `2025-08-14` with net P/L `-38816.00`
- Max consecutive wins: `7`
- Max consecutive losses: `5`
- Max drawdown: `45259.00`
- Total Profit/Loss: `281303.60`
- Total Brokerage: `12200.00`
- Profit/Loss without Brokerage: `293503.60`

### OTM_300

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `147`
- Losing days: `98`
- Break-even days: `0`
- Max profit day: `2025-04-07` with net P/L `40523.00`
- Max loss day: `2025-08-14` with net P/L `-30509.00`
- Max consecutive wins: `7`
- Max consecutive losses: `5`
- Max drawdown: `34482.00`
- Total Profit/Loss: `199936.00`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `212186.00`

### OTM_400

- Traded days: `244`
- Skipped days: `5`
- CE-sell count: `124`
- PE-sell count: `120`
- Winning days: `129`
- Losing days: `115`
- Break-even days: `0`
- Max profit day: `2025-04-07` with net P/L `38079.00`
- Max loss day: `2025-08-14` with net P/L `-22605.00`
- Max consecutive wins: `6`
- Max consecutive losses: `5`
- Max drawdown: `26823.00`
- Total Profit/Loss: `135545.00`
- Total Brokerage: `12200.00`
- Profit/Loss without Brokerage: `147745.00`

### OTM_500

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `103`
- Losing days: `142`
- Break-even days: `0`
- Max profit day: `2025-04-07` with net P/L `35349.00`
- Max loss day: `2025-08-14` with net P/L `-15936.00`
- Max consecutive wins: `10`
- Max consecutive losses: `12`
- Max drawdown: `28324.00`
- Total Profit/Loss: `86768.40`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `99018.40`

### ITM_100

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `134`
- Losing days: `111`
- Break-even days: `0`
- Max profit day: `2025-05-09` with net P/L `67407.00`
- Max loss day: `2025-08-14` with net P/L `-62424.00`
- Max consecutive wins: `6`
- Max consecutive losses: `6`
- Max drawdown: `95435.00`
- Total Profit/Loss: `514952.00`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `527202.00`

### ITM_200

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `133`
- Losing days: `112`
- Break-even days: `0`
- Max profit day: `2025-05-09` with net P/L `78067.00`
- Max loss day: `2025-08-14` with net P/L `-68677.00`
- Max consecutive wins: `6`
- Max consecutive losses: `6`
- Max drawdown: `113666.00`
- Total Profit/Loss: `578795.00`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `591045.00`

### ITM_300

- Traded days: `245`
- Skipped days: `4`
- CE-sell count: `125`
- PE-sell count: `120`
- Winning days: `131`
- Losing days: `114`
- Break-even days: `0`
- Max profit day: `2025-05-09` with net P/L `89871.00`
- Max loss day: `2025-08-14` with net P/L `-71667.00`
- Max consecutive wins: `6`
- Max consecutive losses: `6`
- Max drawdown: `125171.00`
- Total Profit/Loss: `623772.40`
- Total Brokerage: `12250.00`
- Profit/Loss without Brokerage: `636022.40`

## Exceptions By Range

### OTM_100

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25950_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### OTM_200

- `2025-09-23`: `missing_entry_or_exit_timestamp`. NIFTY_25000_PE_30_SEP_25.csv missing entry timestamp 2025-09-23T15:29:00+05:30; NIFTY_25000_PE_30_SEP_25.csv missing exit timestamp 2025-09-24T09:16:00+05:30
- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_26050_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### OTM_300

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_26150_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### OTM_400

- `2025-03-25`: `missing_entry_or_exit_timestamp`. NIFTY_24000_CE_27_MAR_25.csv missing entry timestamp 2025-03-25T15:29:00+05:30; NIFTY_24000_CE_27_MAR_25.csv missing exit timestamp 2025-03-26T09:16:00+05:30
- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_26250_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### OTM_500

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_26350_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### ITM_100

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25750_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### ITM_200

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25650_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

### ITM_300

- `2025-10-20`: `missing_entry_or_exit_timestamp`. NIFTY_25550_CE_28_OCT_25.csv missing exit timestamp 2025-10-21T09:16:00+05:30; Next trading day is a special session that starts at 13:45, so the exact 09:16 exit candle is unavailable.
- `2025-10-21`: `missing_spot_signal_timestamp`. Missing spot signal timestamp 2025-10-21T15:15:00+05:30
- `2025-12-30`: `no_next_weekly_expiry`. No weekly expiry folder exists strictly after the trade date.
- `2025-12-31`: `no_next_trading_day`. No next trading day exists in the dataset.

## Remarks

- Exact timestamp matching is required; no nearest-candle fallback is allowed.
- The `15:15` spot row is used as the `15:30` close proxy because the spot dataset has no exact `15:30` timestamp.
- The `15:29` option row is used as the sell proxy because the options dataset has no exact `15:30` timestamp.
- The NIFTY spot file is the source of truth for the trading calendar.
- Expiry folder dates are used as truth, which naturally handles Tuesday special expiries and holiday shifts.
- Equality between the spot close and the SMA produces no trade for every range on that date.
- Missing option files or timestamps skip only the affected range/date.
