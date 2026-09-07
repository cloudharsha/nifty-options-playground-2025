# Dataset Reference

What the market data looks like and the contract conventions that change P/L.
Getting the lot size or expiry day wrong silently rescales every number in a
backtest, so read this before writing a strategy.

The data itself is **not** in this repo — see [data layout](../../README.md#data-layout)
for where the scripts expect to find it.

Back to the [backtesting index](../README.md).

---

## Directory Overview

| Dataset | Index | Exchange | Data Range | Folders |
|---|---|---|---|---|
| `NiftyOptions_2020_2026` | NIFTY 50 | NSE | Jan 2, 2020 – Dec 29, 2026 | 351 expiry dates |
| `SensexOptions_2024_2026` | S&P BSE SENSEX | BSE | Oct 4, 2024 – Jun 2028+ | 94 expiry dates |

---

## File Structure

```
{Dataset}/
  Options/
    {YYYY-MM-DD}/               ← expiry date of the contract
      {INDEX}_{STRIKE}_{TYPE}_{DD}_{MON}_{YY}.csv
```

**Example filenames:**
```
NIFTY_23500_CE_02_JAN_25.csv
SENSEX_80000_PE_07_JAN_25.csv
```

**CSV format** (1-minute OHLCV bars, IST):
```
timestamp,open,high,low,close,volume,oi
2025-01-02T09:15:00+05:30,150.3,152.0,149.5,151.2,3750.0,284875.0
```

- `timestamp`: ISO 8601, `+05:30` offset (IST). Market hours: 09:15–15:30.
- `volume` / `oi`: In absolute share units, **not lots**. Divide by lot size to get contracts.
- Some deep-OTM files contain only the header row (no trades occurred).

---

## NIFTY 50 Options — NiftyOptions_2020_2026

### Strike Interval
**50 points** throughout the entire dataset (Jan 2020 – 2026).

### Lot Size History

| Period (by expiry date) | Lot Size | Notes |
|---|---|---|
| Jan 2, 2020 – Oct 6, 2021 | **75** | Original NSE lot size |
| Oct 7, 2021 – Apr 25, 2024 | **50** | NSE revision effective Oct 2021 expiry |
| May 2, 2024 – Nov 21, 2024 | **25** | NSE revision effective May 2024 expiry |
| Nov 28, 2024 – Dec 30, 2025 | **75** | SEBI mandated minimum ₹15L contract value; NSE increased lot size effective new contracts from Nov 20, 2024 |
| Jan 2026 onwards | **65** | NSE reduced lot size to align with SEBI's updated ₹15–20L contract value range |

> **How to apply:** When backtesting a date range that spans a lot size change, use the lot size
> that was active on the **expiry date** of the contract being traded, not the trade date.
> Existing weekly contracts at the Nov 2024 boundary retained their previous lot size (25) until
> expiry; new weekly contracts introduced from Nov 20, 2024 onwards carried lot size 75.

### Approximate SPAN Margin per Lot

For capital-sizing calculations, a synthetic directional position (long CE + short PE, or long PE + short CE) has margin requirements similar to a NIFTY futures contract, approximately **8–12% of contract value** (lot_size × NIFTY_level).

| Period | Lot Size | NIFTY Level (approx) | Contract Value | ~Margin/Lot (10%) |
|---|---|---|---|---|
| 2020 | 75 | 10,000–12,000 | 7.5L–9L | 75k–90k |
| 2021 | 75 → 50 | 13,000–18,000 | 6.5L–9L | 65k–90k |
| 2022 | 50 | 15,000–18,000 | 7.5L–9L | 75k–90k |
| 2023 | 50 | 17,000–22,000 | 8.5L–11L | 85k–110k |
| 2024 (pre-Nov) | 25 | 21,000–26,000 | 5.25L–6.5L | 52k–65k |
| 2024 (post-Nov) | 75 | 23,000–26,000 | 17.25L–19.5L | 172k–195k |
| 2025 | 75 | 22,000–27,000 | 16.5L–20.25L | 165k–202k |
| 2026 | 65 | 22,000–26,000 | 14.3L–16.9L | 143k–169k |

**Formula for backtesting lot count with capital C:**
`lots = max(1, floor(C / (lot_size × NIFTY_close × 0.10)))`

### Expiry Day History

| Period | Weekly Expiry Day |
|---|---|
| Jan 2, 2020 – Aug 28, 2025 | **Thursday** |
| Sep 2, 2025 – present | **Tuesday** |

- Holiday adjustments: when the scheduled expiry day is a market holiday, expiry moves to the **previous trading day** (e.g., Oct 20, 2025 is Monday because Oct 21 was a holiday).
- Monthly and quarterly contracts follow the same expiry day rule (last Thursday / last Tuesday of the month/quarter).

### Strike Price Ranges by Era

| Era | Approximate Nifty Level | Strike Range in Data |
|---|---|---|
| 2020 | 9,000 – 14,000 | ~8,000 – 15,000 |
| 2021 | 13,000 – 18,000 | ~12,000 – 19,000 |
| 2022 | 15,000 – 19,000 | ~13,000 – 21,000 |
| 2023 | 17,000 – 22,000 | ~15,000 – 24,000 |
| 2024 | 21,000 – 26,000 | ~19,000 – 28,000 |
| 2025–2026 | 22,000 – 27,000+ | ~20,000 – 30,000+ |

### Long-Dated Contracts
The dataset also includes 8 quarterly/annual expiry dates beyond 2026:
`2027-03-30, 2027-06-29, 2027-12-28, 2028-06-27, 2028-12-26, 2029-06-26, 2029-12-24, 2030-12-31`
These are very low-liquidity contracts; most files will be header-only or near-empty.

---

## BSE SENSEX Options — SensexOptions_2024_2026

### Strike Interval
**100 points** throughout the entire dataset (Oct 2024 – 2026+).

### Lot Size

**10 shares/lot** — consistent throughout the data range.

### Expiry Day History

| Period | Weekly Expiry Day |
|---|---|
| Oct 4, 2024 – Jan 3, 2025 | **Friday** |
| Jan 7, 2025 – present | **Tuesday** |

- Holiday adjustments apply (expiry shifts to previous trading day).
- Oct 31, 2024 (Thursday) and Nov 14, 2024 (Thursday) are holiday-adjusted expiries where the Friday was a market holiday.
- From Jan 7, 2025 onward, **both Nifty and Sensex expire on Tuesday**, meaning they now share the same expiry day.

### Data Notes
- BSE Sensex options had low liquidity in late 2024. Many files in Oct–Dec 2024 will be header-only (no trades).
- Liquidity improved through 2025. Files from mid-2025 onward are more likely to have meaningful OHLCV data.
- The dataset includes some quarterly contracts extending to 2028+.

---

## Backtesting Checklist

1. **Lot size awareness:** Apply the correct lot size for your date range. P&L will be wrong by 2× or 3× if you use the wrong value.

2. **Expiry day filter:** If your strategy enters/exits on expiry day, make sure your date filter accounts for:
   - Thursday expiry (Nifty, pre-Sep 2025)
   - Friday expiry (Sensex, pre-Jan 2025)
   - Tuesday expiry (both from their respective switch dates)
   - Holiday-shifted expiries (off by 1 day)

3. **Empty file handling:** Always check that a CSV has data beyond the header before processing. Strategies that assume data exists will fail silently on empty files.

4. **OI in share units:** `oi` column is in shares. For contract count: `oi / lot_size`.

5. **ATM strike selection:** Strikes are at 50-point (Nifty) or 100-point (Sensex) intervals. Round the index level to the nearest interval to find ATM.

6. **Timestamp parsing:** All timestamps include `+05:30`. Parse as timezone-aware datetimes to avoid offset errors when computing time-to-expiry.

---

## Quick Reference

```
Nifty lot size:   75  (until Oct 6, 2021 expiry)
                  50  (Oct 7, 2021 – Apr 25, 2024 expiry)
                  25  (May 2, 2024 – Nov 21, 2024 expiry)
                  75  (Nov 28, 2024 – Dec 30, 2025 expiry)
                  65  (Jan 2026 expiry onwards)

Nifty expiry:     Thursday  (Jan 2020 – Aug 2025)
                  Tuesday   (Sep 2025 onwards)

Sensex lot size:  10  (throughout Oct 2024+)

Sensex expiry:    Friday    (Oct 2024 – Jan 3, 2025)
                  Tuesday   (Jan 7, 2025 onwards)

Strike intervals: Nifty = 50 pts | Sensex = 100 pts
```
