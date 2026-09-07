# 25-SMA Overnight

Positions opened on a 25-SMA signal and carried overnight into the weekly expiry, including the strike-offset sweep (ITM 100-300, OTM 100-500) and the long-side variant.

- Scripts: [`backtesting/python/25ma-overnight/`](../../python/25ma-overnight/)
- Results: [`backtesting/results/25ma-overnight/`](../../results/25ma-overnight/)

Back to the [backtesting index](../../README.md).

> **Corrected 2026-09-08 — every "Current" row below moved down by 3–13 points.**
> These scripts took their direction from the 15:15 15-minute bar but entered at
> 15:29. That bar does not close until 15:30, so the entry preceded its own
> signal by a minute. The default signal bar is now 15:00, which closes at 15:15
> and is genuinely known at entry. One minute of hindsight was worth 4–6
> percentage points of CAGR a year; the long variant flips from profit to loss.
> Detail and pre-fix numbers in the [lookahead audit](../lookahead-audit.md).
> The "Archived" 2025 rows come from non-runnable `python/legacy/` scripts and
> were **not** re-run; they still carry the bug.


Capital Base is what the strategy actually needs, not a fixed reference - read the
[index notes](../../README.md#reading-the-numbers) before comparing rows across families.

| Status | Period | Test | Result | Capital Base | Net P/L | CAGR / Return | Max DD | Summary | Remarks |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| Archived | 2025 | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 1L | Rs 2,51,943.80 | 251.94% | Rs 1,02,323.00 | [Summary](../../results/legacy-2/long_atm_nifty_ma_weekly_overnight_2025_summary.md) | [6Y (corrected): −5.90% CAGR](../../results/25ma-overnight/long/long_atm_nifty_ma_weekly_overnight_2020_2026_summary.md) |
| Archived | 2025 | Long ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 1L | Rs 2,51,943.80 | 251.94% | Rs 1,02,323.00 | [Summary](../../results/legacy/long_atm_nifty_ma_weekly_overnight_2025_summary.md) | [6Y (corrected): −5.90% CAGR](../../results/25ma-overnight/long/long_atm_nifty_ma_weekly_overnight_2020_2026_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset ITM 300 | Profit | Rs 10L | Rs 6,23,772.40 | 62.38% | Rs 1,25,171.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): 13.83% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset ITM 200 | Profit | Rs 10L | Rs 5,78,795.00 | 57.88% | Rs 1,13,666.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): 14.93% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset ITM 100 | Profit | Rs 10L | Rs 5,14,952.00 | 51.50% | Rs 95,435.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): 13.96% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 10L | Rs 4,46,015.60 | 44.60% | Rs 76,221.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_2025_summary.md) |  |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 100 | Profit | Rs 10L | Rs 3,63,236.80 | 36.32% | Rs 58,480.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): 6.95% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Archived | 2025 | Long/Short ATM NIFTY MA Weekly Overnight 2025 | Profit | Rs 10L | Rs 3,36,729.70 | 33.67% | Rs 80,646.50 | [Summary](../../results/legacy/long_short_atm_nifty_ma_weekly_overnight_2025_summary.md) |  |
| Archived | ~4Y | Long/Short ATM NIFTY MA Weekly Overnight 2022-2026 (capital-based lots, margin ≈10%) | Profit | Rs 10L | Rs 20,77,457.90 | 32.63% CAGR | Rs 6,80,802.50 | [Summary](../../results/legacy/long_short_atm_nifty_ma_weekly_overnight_2020_2026_summary.md) |  |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 200 | Profit | Rs 10L | Rs 2,81,303.60 | 28.13% | Rs 45,259.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): 2.77% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 300 | Profit | Rs 10L | Rs 1,99,936.00 | 19.99% | Rs 34,482.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): 0.30% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset ITM 200 | Profit | Rs 10L | Rs 18,24,282 | 14.93% CAGR | Rs 3,53,561 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 57.88%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset ITM 300 | Profit | Rs 10L | Rs 16,29,235 | 13.83% CAGR | Rs 3,94,855 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 62.38%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset ITM 100 | Profit | Rs 10L | Rs 16,52,625 | 13.96% CAGR | Rs 3,14,282 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 51.50%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 400 | Profit | Rs 10L | Rs 1,35,545.00 | 13.55% | Rs 26,823.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): −2.19% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset OTM 100 | Profit | Rs 10L | Rs 6,51,606 | 6.95% CAGR | Rs 3,01,850 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 36.32%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Offset OTM 500 | Profit | Rs 10L | Rs 86,768.40 | 8.68% | Rs 28,324.00 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) | [6Y (corrected): −5.86% CAGR](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset OTM 200 | Profit | Rs 10L | Rs 2,26,421 | 2.77% CAGR | Rs 2,75,020 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 28.13%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Current | 2020–2026 | Long ATM NIFTY MA Weekly Overnight | Loss | Rs 5L | −Rs 1,82,442 | −5.90% CAGR | Rs 7,39,380 | [Summary](../../results/25ma-overnight/long/long_atm_nifty_ma_weekly_overnight_2020_2026_summary.md) | [2025: 251.94%](../../results/legacy-2/long_atm_nifty_ma_weekly_overnight_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset OTM 300 | Profit | Rs 10L | Rs 22,715 | 0.30% CAGR | Rs 2,98,343 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 19.99%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset OTM 400 | Loss | Rs 10L | −Rs 1,52,176 | −2.19% CAGR | Rs 4,20,010 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 13.55%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Current | 2020–2026 | Short ATM NIFTY MA Weekly Overnight Offset OTM 500 | Loss | Rs 10L | −Rs 3,63,001 | −5.86% CAGR | Rs 5,25,709 | [Summary](../../results/25ma-overnight/short-offsets/short_atm_nifty_ma_weekly_overnight_offsets_2020_2026_summary.md) | [2025: 8.68%](../../results/legacy/short_atm_nifty_ma_weekly_overnight_offsets_2025_summary.md) |
| Archived | 2025 | Short ATM NIFTY MA Weekly Overnight Hedged 2025 | Loss | Rs 10L | Rs -2,18,490.00 | -21.85% | Rs 3,22,592.50 | [Summary](../../results/legacy/short_atm_nifty_ma_weekly_overnight_hedged_2025_summary.md) |  |
