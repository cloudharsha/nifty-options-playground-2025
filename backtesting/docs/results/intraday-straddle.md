# Intraday Straddle

ATM straddles opened and closed within one session, with independent or joint stop losses and a CE/PE balance filter at entry. Covers both NIFTY and SENSEX.

- Scripts: [`backtesting/python/intraday-straddle/`](../../python/intraday-straddle/)
- Results: [`backtesting/results/intraday-straddle/`](../../results/intraday-straddle/)

Back to the [backtesting index](../../README.md).

Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Intraday ATM Straddle — Independent SL per Leg (1 lot, 09:20–15:20, 2× SL each leg) | Profit | Rs 3L | Rs 40,756.25 | 13.59% | Rs 38,647.00 | [Summary](../../results/legacy/intraday_atm_straddle_indep_sl_2025_summary.md) |  |
| Archived | 2025 | Intraday ATM Straddle — 25-period 15m MA Filter (1 lot, 09:40–15:20, MA entry + dynamic MA SL) | Profit | Rs 3L | Rs 35,710.36 | 11.90% | Rs 24,078.33 | [Summary](../../results/legacy/intraday_atm_straddle_ma25_2025_summary.md) |  |
| Archived | 2025 | Intraday ATM Straddle — Joint SL (1 lot, 09:20–15:20, 2× SL exits both legs) | Profit | Rs 3L | Rs 16,595.00 | 5.53% | Rs 53,756.50 | [Summary](../../results/legacy/intraday_atm_straddle_joint_sl_2025_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — Expiry-Inclusive, **50% Ind. SL** (~300 qty, 09:20–15:20, no balance filter) | Profit | Rs 10L | Rs 15,57,357 | N/A | Rs 3,50,852 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_expiry_incl_nifty_sl50_summary.md) | Best of the sweep, ret/DD 4.4. Two-thirds of the profit is expiry day. See the [stop-loss sweep](#stop-loss-sweep--20-vs-40-vs-50) |
| Current | ~6Y | NIFTY Intraday ATM Straddle — Expiry-Inclusive, **40% Ind. SL** (~300 qty, 09:20–15:20, no balance filter) | Profit | Rs 10L | Rs 10,64,310 | N/A | Rs 3,88,168 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_expiry_incl_nifty_sl40_summary.md) | Same net as 20%, deeper drawdown. 2026 so far −Rs 3.14L |
| Current | ~6Y | NIFTY Intraday ATM Straddle — Expiry-Inclusive (~300 qty, 09:20–15:20, 20% Ind. SL per leg, no balance filter) | Profit | Rs 10L | Rs 10,48,326 | N/A | Rs 2,93,983 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_expiry_incl_nifty_summary.md) |  |
| Current | 2024–2026 | SENSEX Intraday ATM Straddle — Expiry-Inclusive (100 qty, 09:20–15:20, 20% Ind. SL per leg, balance filter) | Profit | Rs 5L | Rs 3,29,040 | N/A | Rs 1,70,381 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_expiry_incl_sensex_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — **50% Ind. SL**, Weekly Expiry (~300 qty, 09:20–15:20, balance filter) | Profit | Rs 10L | Rs 4,84,211 | N/A | Rs 2,30,816 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_50pct_sl_nifty_2020_2026_summary.md) | Best non-expiry-day result, ret/DD 2.1. Lost in 2023, 2024 and 2026 |
| Current | ~6Y | NIFTY Intraday ATM Straddle — **40% Ind. SL**, Weekly Expiry (~300 qty, 09:20–15:20, balance filter) | Profit | Rs 10L | Rs 1,50,263 | N/A | Rs 3,52,539 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_40pct_sl_nifty_2020_2026_summary.md) | Worse than both 20% and 50% — drawdown larger than the profit |
| Current | 2024–2026 | SENSEX Intraday ATM Straddle — 20% Ind. SL, Monthly Expiry (100 qty, 09:20–15:20, balance filter) | Profit | Rs 5L | Rs 2,52,845 | N/A | Rs 1,12,754 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_sensex_monthly_2024_2026_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — 20% Ind. SL, Weekly Expiry (~300 qty, 09:20–15:20, balance filter) | Profit | Rs 10L | Rs 2,16,384 | N/A | Rs 2,60,277 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_nifty_2020_2026_summary.md) |  |
| Current | 2024–2026 | SENSEX Intraday ATM Straddle — 20% Ind. SL, Weekly Expiry (100 qty, 09:20–15:20, balance filter) | Profit | Rs 5L | Rs 1,44,762 | N/A | Rs 1,72,031 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_sensex_2024_2026_summary.md) |  |
| Archived | 2025 | Short ATM Weekly Straddle 2025 | Loss | Rs 10L | Rs -10,824.00 | -1.08% | N/A | [Summary](../../results/legacy/short_atm_weekly_straddle_2025_summary.md) |  |
| Archived | 2025 | Gap Open ATM Straddle 09:15 2025 | Loss | Rs 10L | Rs -2,73,125.00 | -27.31% | N/A | [Summary](../../results/legacy-2/gap_open_atm_straddle_0915_2025_summary.md) |  |
| Current | ~6Y | NIFTY Intraday ATM Straddle — 20% Ind. SL, Monthly Expiry (~300 qty, 09:20–15:20, balance filter) | Loss | Rs 10L | Rs -1,54,701 | N/A | Rs 3,49,483 | [Summary](../../results/intraday-straddle/intraday_atm_straddle_20pct_sl_nifty_monthly_2020_2026_summary.md) |  |

## Stop-loss sweep — 20% vs 40% vs 50%

Sell the ATM CE and PE at 09:20 on the current-week contract, put an independent
stop on each leg at a fixed percentage above its entry price, and square off at
15:20. Same engine, costs (0.50 pt/order slippage, Rs 25/order) and ~300 qty sizing
as the 20% runs above; only `--sl-pct` changes. Both 20% runs were re-run after
adding the output-name options and reproduce the committed files byte-for-byte.

Two variants, because they answer different questions:

- **Expiry-inclusive** — always the current-week contract, **including on expiry
  day**, no balance filter. This is the literal "same week" spec. 1,573 days traded.
- **Weekly** — current week, but rolls to next week on expiry day, and skips the
  day if CE and PE differ by more than 20%. 888 days traded (426 balance skips,
  365 missing 09:20 candles, mostly next-week contracts on expiry day).

### Expiry-inclusive (the "same week" spec)

| SL per leg | Net P/L | Max DD | Ret/DD | Win | PF | Expiry-day P/L | Other-day P/L | One leg stopped | Neither stopped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20% | Rs 10,48,326 | Rs 2,93,983 | 3.57 | 53.4% | 1.14 | Rs 8,11,967 | Rs 2,36,359 | 954 | 52 |
| 40% | Rs 10,64,310 | Rs 3,88,168 | 2.74 | 61.9% | 1.15 | Rs 9,50,467 | Rs 1,13,843 | 1,070 | 303 |
| **50%** | **Rs 15,57,357** | Rs 3,50,852 | **4.44** | 62.2% | **1.25** | Rs 10,44,140 | Rs 5,13,217 | 986 | 459 |

"One leg stopped" counts days where exactly one leg stopped out. Of the 1,573 days,
the rest saw both legs stopped (567 / 200 / 128).

### Weekly (balance filter, never holds the expiring contract)

| SL per leg | Net P/L | Max DD | Ret/DD | Win | PF | Neither stopped |
|---|---:|---:|---:|---:|---:|---:|
| 20% | Rs 2,16,384 | Rs 2,60,277 | 0.83 | 54.6% | 1.04 | 49 |
| 40% | Rs 1,50,263 | Rs 3,52,539 | 0.43 | 62.8% | 1.04 | 237 |
| **50%** | **Rs 4,84,211** | **Rs 2,30,816** | **2.10** | 62.3% | **1.13** | 333 |

### Year by year

| Year | Exp-incl 20% | Exp-incl 40% | Exp-incl 50% | Weekly 20% | Weekly 40% | Weekly 50% |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 2,40,028 | 3,49,723 | 3,78,460 | −72,983 | 26,887 | 77,560 |
| 2021 | 3,20,066 | 4,45,382 | 3,43,768 | 2,33,952 | 2,56,959 | 1,30,238 |
| 2022 | 2,26,718 | 3,26,384 | 5,78,188 | −10,693 | 1,65,374 | 4,09,602 |
| 2023 | −73,739 | 3,925 | −71,892 | −26,271 | −27,846 | −57,480 |
| 2024 | 3,58,244 | 49,793 | 2,35,374 | 2,43,978 | −2,08,380 | −96,474 |
| 2025 | 1,45,477 | 2,03,446 | 2,50,261 | −78,629 | 1,59,756 | 80,348 |
| 2026 (to Jun) | −1,68,468 | −3,14,343 | −1,56,800 | −72,970 | −2,22,487 | −59,584 |

### What it says

**50% beats 40% and 20% in both variants.** It has the highest net, the best
return per drawdown and the best profit factor. The wider stop roughly halves
the both-legs-stopped days (whipsaws) and lets a third of days run to 15:20 untouched.

**40% is not a midpoint, it is the worst of the three on the weekly variant.**
Net falls and drawdown rises versus 20%. A sweep that goes 20 → 40 → 50 and is not
monotonic is mostly noise between adjacent levels. Read "50% is better" as "wider
than 20% is better", not as a precise optimum. The [expiry-day sweep](expiry-day-short-premium.md#the-stop-loss-sweep--50-is-too-tight-for-everything)
found the same thing on expiry day alone, where 80–90% loss was best.

**The "same week" result is mostly an expiry-day result.** In the expiry-inclusive
runs, expiry day (331 of 1,573 days) produces Rs 8.1–10.4L of the profit. The other
1,242 days produce Rs 1.1–5.1L, about what the weekly variant makes. Selling the
straddle Monday–Wednesday at 09:20 is a thin edge. Expiry-day theta is what pays.

**It is not stable year to year.** Every configuration lost money in 2023 and in
2026 so far, and the weekly 50% run also lost in 2024. Max drawdown is Rs 2.3–3.9L
on ~300 qty, deep enough to sit through a year of losses.

Scripts: [`run_intraday_atm_straddle_20pct_sl_expiry_included.py`](../../python/intraday-straddle/run_intraday_atm_straddle_20pct_sl_expiry_included.py)
(`--index NIFTY --sl-pct 0.40 --output-suffix _sl40`) and
[`run_intraday_atm_straddle_20pct_sl_nifty_2020_2026.py`](../../python/intraday-straddle/run_intraday_atm_straddle_20pct_sl_nifty_2020_2026.py)
(`--sl-pct 0.40 --output-name intraday_atm_straddle_40pct_sl_nifty_2020_2026`).
