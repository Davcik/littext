# Changelog entry for v0.3.0 (commit 1 of 4)

## [0.3.0] - ????-??-??

This commit introduces the Tier-1 corpus-input guardrails specified in
the v0.3 design note. It is the first of four commits in the v0.3
release cycle: subsequent commits address F-pattern matcher extensions,
the construct-hierarchy detector, and the Tier-2 texttype declaration.

### Added

- `mintextlen(#)` option on `littext analyze`: minimum text length in
  characters. Rows below the threshold are dropped before the pipeline
  runs. Default 200, calibrated for academic abstracts.
- `keepempty` option on `littext analyze`: disables row-dropping
  entirely. Use when preserving the input row count is required for
  downstream purposes.
- Explicit row-drop diagnostic in `_littext_analyze.ado`: logs the
  number of rows dropped for each of three reasons (empty text, missing
  id, below `mintextlen`), and warns when more than 25% of input rows
  are dropped.
- Defensive secondary row-drop in `_load_corpus`: catches rows that
  pass Stata-side validation but become empty after `_clean_text()`
  strips publisher boilerplate.
- String-type check on the variable passed to `text()`: errors out
  before any Python is invoked if the variable is numeric.
- Hard failure with informative message when no rows survive
  row-drop, rather than silently proceeding to empty output frames.

### Changed

- Default behaviour: rows with empty or whitespace-only `text()` are
  now dropped by default rather than silently producing no constructs.
  This may reduce the `lt_diag` row count for corpora that previously
  contained empty cells.
- `_load_corpus` signature: now accepts `min_text_len` and
  `keep_empty` parameters (defaults preserve the v0.2.9 behaviour
  when called directly).

### Migration notes

- Users who previously relied on `littext analyze` to count empty rows
  in `lt_diag` will see those rows excluded by default. To restore the
  previous behaviour, pass `keepempty`.
- The Stata-side variable check rejects numeric variables passed to
  `text()`; users who previously passed a numeric variable that
  happened to parse to a usable string (e.g., year-as-text) must cast
  it explicitly with `tostring`.
