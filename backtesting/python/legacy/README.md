# Archived scripts

**These scripts do not run as-is. Do not reach for one expecting it to work.**

Two things are wrong with all 34 of them, and both are unfixed on purpose:

1. **Wrong repo root.** Each computes `Path(__file__).resolve().parents[2]`,
   which resolved correctly when these files sat at `python/`. They now sit one
   level deeper, so `parents[2]` yields `backtesting/` instead of the repo root
   and every default path lands one level too shallow. The correct value here is
   `parents[3]`. This fails silently rather than raising.
2. **Dead data directory.** Their defaults point at `Options_2025/`, which no
   longer exists. The current datasets are `NiftyOptions_2020_2026/Options/` and
   `SensexOptions_2024_2026/Options/`.

The fix is one character in each file plus a path swap. It is deliberately not
applied, because these scripts produced the numbers recorded in
[`results/legacy/`](../../results/legacy/) and
[`results/legacy-2/`](../../results/legacy-2/) against the **2025-only** dataset
that shipped at the time. Repointing them at the 2020–2026 data would make them
run and quietly produce different numbers from the ones the index reports —
which is worse than leaving them visibly broken.

If you want to revive one: move it out of `legacy/`, fix both issues, re-run it
against current data, and index it as a new result rather than overwriting the
archived one.

`run_weekly_adjusting_strangle_through_expiry_2025.py` imports
`run_combined_expiry_adjusting_strangle_2025` from this directory. Those two
must stay together.

The [tests](../tests/) exercise helper functions from five of these scripts and
do pass — they build their arguments by hand and never call `parse_args()`, so
they never touch the broken defaults.
