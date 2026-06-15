# nifty-options-playground-2025

2025 NIFTY market data for backtesting:

- expiry-wise NIFTY option contract candles in `Options_2025/`
- derived 15-minute option contract candles in `Options_2025_15m/`
- 1-minute and 15-minute NIFTY 50 index candles in `nifty/`
- local conversion utilities in `scripts/`
- FYERS helper scripts in `fyers-api/` to pull the index data again if needed

## Repo contents

### `Options_2025/`

Raw option contract data, grouped by expiry date.

- `53` expiry folders
- date span: `2025-01-02` to `2025-12-30`
- `10,388` CSV files total

Structure:

```text
Options_2025/
  2025-01-02/
    NIFTY_21600_CE_02_JAN_25.csv
    NIFTY_21600_PE_02_JAN_25.csv
    ...
  2025-01-09/
  ...
  2025-12-30/
```

Each folder is one expiry.  
Each file is one contract: `NIFTY_<strike>_<CE|PE>_<expiry>.csv`

Options CSV schema:

```csv
timestamp,open,high,low,close,volume,oi
```

Important behavior:

- one file = one expiry + strike + option type
- files contain contract history, not just expiry-day candles
- some files can be header-only, so loaders should skip empty files
- strike coverage changes by expiry
- the strike ladder is typically in `50` point intervals
- do not hardcode Thursday expiry; use the folder date as truth

### `Options_2025_15m/`

Derived 15-minute option contract data, grouped by the same expiry folders and filenames as `Options_2025/`.

Generation command:

```bash
python3 scripts/build_options_2025_15m.py --clean-output
```

Structure:

```text
Options_2025_15m/
  2025-01-02/
    NIFTY_21600_CE_02_JAN_25.csv
    NIFTY_21600_PE_02_JAN_25.csv
    ...
  2025-01-09/
  ...
  2025-12-30/
```

Schema:

```csv
timestamp,open,high,low,close,volume,oi
```

Aggregation rules:

- the folder and filename layout mirrors `Options_2025/` exactly
- timestamps are floored to 15-minute IST clock boundaries such as `09:15`, `09:30`, `09:45`, and `15:15`
- `open` is the first 1-minute row in the bucket
- `high` is the highest `high` in the bucket
- `low` is the lowest `low` in the bucket
- `close` is the last `close` in the bucket
- `volume` is summed across the bucket
- `oi` is taken from the last 1-minute row in the bucket
- partial buckets are preserved when a contract starts late or has sparse source minutes
- header-only source contracts remain header-only in `Options_2025_15m/`

### `nifty/`

Underlying NIFTY 50 index candles for the same year.

- file: `nifty/NIFTY50_INDEX_1m_2025.csv`
- file: `nifty/NIFTY50_INDEX_15m_last_4y.csv`
- `93,061` minute rows
- date span: `2025-01-01T09:15:00+05:30` to `2025-12-31T15:29:00+05:30`

Schema:

```csv
timestamp,open,high,low,close,volume
```

Example:

```csv
timestamp,open,high,low,close,volume
2025-01-01T09:15:00+05:30,23637.65,23681.7,23633.35,23649.55,0
```

Notes:

- timestamps are timezone-aware and use `+05:30`
- this file is suitable as the underlying index series for option backtests
- volume is `0` for many earlier rows; treat index volume carefully if your strategy depends on it

### `fyers-api/`

Utility scripts for FYERS-based data pull:

- [fyers-api/fyers_auth.py](/mnt/c/Users/harsh/Desktop/workspace/git/nifty-options-playground-2025/fyers-api/fyers_auth.py:1): generate auth URL and exchange auth code for access token
- [fyers-api/download_nifty_history.py](/mnt/c/Users/harsh/Desktop/workspace/git/nifty-options-playground-2025/fyers-api/download_nifty_history.py:1): download NIFTY 50 minute history into `nifty/`
- [fyers-api/README.md](/mnt/c/Users/harsh/Desktop/workspace/git/nifty-options-playground-2025/fyers-api/README.md:1): setup and run instructions

### `backtesting/`

Backtest runners and generated results:

**Overnight strategies**
- [backtesting/python/run_short_atm_weekly_straddle_2025.py](backtesting/python/run_short_atm_weekly_straddle_2025.py): overnight weekly short ATM straddle (sell 15:20, buy 09:16 next day)
- [backtesting/python/run_short_iron_fly_2025.py](backtesting/python/run_short_iron_fly_2025.py): overnight short iron fly
- [backtesting/python/run_overnight_strangle_by_day_2025.py](backtesting/python/run_overnight_strangle_by_day_2025.py): overnight OTM short strangle with day-of-week premium bands (sell 15:20, buy 09:20 next day); fallback band if primary not found

**Intraday strategies**
- [backtesting/python/run_intraday_joint_sl_strangle_2025.py](backtesting/python/run_intraday_joint_sl_strangle_2025.py): intraday OTM short strangle with day-of-week bands and joint 2× SL (if either leg hits SL, both exit together)
- [backtesting/python/run_intraday_atm_straddle_joint_sl_2025.py](backtesting/python/run_intraday_atm_straddle_joint_sl_2025.py): intraday ATM short straddle with joint 2× SL (enter 09:20, exit 15:20)
- [backtesting/python/run_intraday_atm_straddle_indep_sl_2025.py](backtesting/python/run_intraday_atm_straddle_indep_sl_2025.py): intraday ATM short straddle with independent 2× SL per leg (each leg manages itself; partner continues when one is stopped out)

`backtesting/results/`: generated CSV, summary, and log files for each strategy

## How to use this repo for testing

Use the two datasets together like this:

- underlying spot/index path comes from `nifty/NIFTY50_INDEX_1m_2025.csv`
- option contract candles come from `Options_2025/<expiry>/...`
- join on `timestamp` when comparing option candles with index candles
- derive expiry from the folder name, not by weekday assumptions
- derive strike and option type from the option filename

Practical loader assumptions:

- parse timestamps as timezone-aware datetimes
- skip header-only option CSVs
- do not assume every expiry has the same strike set
- do not assume CE and PE files both exist for every strike, even though they usually do
- do not assume all contracts have the same row count
- if you use `Options_2025_15m/`, pair it with a 15-minute spot series and matching timestamps

## Backtesting

Both backtest scripts:

- use `nifty/NIFTY50_INDEX_1m_2025.csv` as the trading-day calendar and spot reference
- use exact option timestamps from `Options_2025/`
- write outputs into `backtesting/results/`
- support default runs and explicit parameter overrides
- are intentionally unchanged by the 15-minute dataset build

Default execution assumptions vary by script. Intraday scripts use:

- `lot_size = 75`, `lots = 1`, multiplier = `75` per point
- `slippage_points_per_order = 0.5`
- `brokerage_per_order = 25`

Overnight scripts use:

- `lot_size = 65`, `lots = 4`, multiplier = `260` per point
- `slippage_points_per_order = 1`
- `brokerage_per_order = 25`

All scripts support `--lot-size`, `--lots`, `--slippage-points-per-order`, `--brokerage-per-order` overrides.

Summary files include: total net P/L, gross P/L, brokerage, winning/losing days, max single-day profit/loss, **peak cumulative profit**, and **max drawdown**.

### 1. Weekly Short ATM Straddle

Run with defaults:

```bash
python3 backtesting/python/run_short_atm_weekly_straddle_2025.py
```

Run with explicit parameters:

```bash
python3 backtesting/python/run_short_atm_weekly_straddle_2025.py \
  --spot-file nifty/NIFTY50_INDEX_1m_2025.csv \
  --options-dir Options_2025 \
  --results-dir backtesting/results \
  --entry-time 15:20 \
  --exit-time 09:16 \
  --brokerage-per-order 25 \
  --lot-size 65 \
  --lots 4 \
  --slippage-points-per-order 1
```

Outputs:

- `backtesting/results/short_atm_weekly_straddle_2025_daywise.csv`
- `backtesting/results/short_atm_weekly_straddle_2025_summary.md`
- `backtesting/results/short_atm_weekly_straddle_2025.log`

Check progress while it runs:

```bash
tail -f backtesting/results/short_atm_weekly_straddle_2025.log
```

### 2. Short Iron Fly

Run with defaults:

```bash
python3 backtesting/python/run_short_iron_fly_2025.py
```

Run with explicit parameters:

```bash
python3 backtesting/python/run_short_iron_fly_2025.py \
  --spot-file nifty/NIFTY50_INDEX_1m_2025.csv \
  --options-dir Options_2025 \
  --results-dir backtesting/results \
  --entry-time 15:20 \
  --exit-time 09:16 \
  --brokerage-per-order 25 \
  --lot-size 65 \
  --lots 4 \
  --slippage-points-per-order 1 \
  --wing-min-ratio 0.25 \
  --wing-max-ratio 0.35 \
  --wing-target-ratio 0.3333333333
```

Outputs:

- `backtesting/results/short_iron_fly_2025_daywise.csv`
- `backtesting/results/short_iron_fly_2025_summary.md`
- `backtesting/results/short_iron_fly_2025.log`

Check progress while it runs:

```bash
tail -f backtesting/results/short_iron_fly_2025.log
```

If you want to watch both logs in separate terminals:

```bash
tail -f backtesting/results/short_atm_weekly_straddle_2025.log
tail -f backtesting/results/short_iron_fly_2025.log
```

## Quick examples

Inspect one expiry:

```bash
ls Options_2025/2025-01-02 | head
```

Inspect one option contract:

```bash
sed -n '1,10p' Options_2025/2025-01-02/NIFTY_22000_PE_02_JAN_25.csv
```

Inspect the NIFTY index series:

```bash
sed -n '1,10p' nifty/NIFTY50_INDEX_1m_2025.csv
```

Count option files in one expiry:

```bash
find Options_2025/2025-01-02 -maxdepth 1 -type f -name '*.csv' | wc -l
```

Build the 15-minute options dataset:

```bash
python3 scripts/build_options_2025_15m.py --clean-output
```

## Summary

The main testing model in this repository is:

- `Options_2025/` = option contracts by expiry
- `Options_2025_15m/` = derived 15-minute option contracts by expiry
- `nifty/` = underlying index data
- `scripts/` = local conversion utilities
- `fyers-api/` = data pull utilities
