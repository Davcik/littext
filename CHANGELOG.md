# Changelog

All notable changes to the `littext` Stata package are documented in this
file. The format is based on [Keep a Changelog](https://keepachangelog.com/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-05-27

The v0.3.0 release introduces corpus-input guardrails, a lexical
construct-hierarchy detector, and a text-kind declaration with pluggable
cleaning regimes. Together these address the principal defects observed
in v0.2.9 use: silent passage of empty rows through the pipeline; flat
treatment of constructs whose surface forms encode IS-A subsumption
(consumer-based brand equity, financial-based brand equity, online brand
equity, and similar); and a hard-coded assumption that the unit of
analysis is an academic abstract, which produced silently wrong results
on transcripts, reviews, full-text papers, and social-media posts.

The release is structured as three independent commits whose effects
are summarised here. (A fourth commit, F-pattern matcher extensions, was
scoped at the start of v0.3 development but was invalidated by a
parser-level diagnostic and was not implemented; see "Investigated but
not implemented" below.)

### Added — Tier-1 corpus-input guardrails (commit 1)

- Two new options on `littext analyze`: `mintextlen(#)` setting the
  minimum text length in characters (default derived from `texttype()`,
  see below), and `keepempty` to disable row-dropping entirely.
- Stata-side row-drop removes empty/whitespace text, rows with missing
  user-supplied id, and rows below `mintextlen`. Each drop is logged
  with a count.
- Warning emitted when more than 25% of input rows are dropped, on the
  prior that this most often indicates a misdeclared text column.
- Hard failure with informative message when no rows survive.
- Defensive secondary drop in `_load_corpus` catches rows that pass
  Stata-side validation but become empty after text cleaning strips
  publisher boilerplate.
- Variable existence and string-type validation on `text()` before any
  Python is invoked.

### Added — Construct-hierarchy detector (commit 3)

- New module `python/littext_hierarchy.py` implementing two detection
  rules over the canonical vocabulary produced by HDBSCAN clustering:
  (1) the right-substring rule with a frequency prior, and (2) the
  hyphenated-prefix rule for constructs of the form `X-based Parent`,
  `X-driven Parent`, `X-led Parent`, and `X-oriented Parent`. The
  detector runs between `cluster_constructs` and `score_relations`.
- Four new columns on `lt_constructs`: `parent_canonical` (immediate
  IS-A parent or empty for roots), `canonical_root` (topmost ancestor),
  `hierarchy_depth` (zero for roots, one for direct children), and
  `is_root` (1 if root, 0 otherwise). `canonical_root` is precomputed
  to make graph roll-up to root level fast.
- `level()` option on `littext graph`. Accepts `leaf` (default, no
  roll-up), `root` (collapse to topmost ancestor via the precomputed
  `canonical_root`), or a non-negative integer N (collapse to depth N
  via an iterative walk of the parent chain). Honoured by
  `type(frequency)`; ignored with a one-line note by other Stata-
  native types whose x-axis is not construct-keyed; warned and ignored
  by matplotlib types in this release.
- Helper program `_lt_remap_canonical` in `_littext_graph.ado`, invoked
  by the graph dispatcher to apply the chosen `level()` to the working
  frame.

### Added — Tier-2 text-kind declaration (commit 4)

- New option `texttype()` on `littext analyze`. Accepts `abstract`
  (default), `fulltext`, `transcript`, `review`, `comment`, `other`.
- When `texttype()` is not declared, the package defaults to
  `texttype(abstract)` and emits a visible note indicating that this
  default was applied. (This is "Option B" from the design pass —
  the visible note is intended to nudge users to declare their text
  kind explicitly.)
- `texttype()` drives three downstream defaults: which cleaning regime
  is applied (see below); the default segmentation `unit()`; and the
  default `mintextlen()`. Each derived default is overridable by
  passing the corresponding option explicitly. The resolved values
  and their sources ("user-specified" vs "texttype default") are
  printed at run time.
- New module `python/littext_cleaners.py` containing six pluggable
  cleaning regimes:
  - `abstract`: Emerald section headers; copyright tails; arXiv
    Comments/Subjects/etc. tags. Preserves v0.2.9 `_clean_text`
    behaviour exactly.
  - `fulltext`: all of the above plus LaTeX commands (`\cite`,
    `\citep`, `\ref`, etc.); LaTeX environments; reference-section
    detection (heuristic: from a line containing only "References" or
    "Bibliography" to end of text); figure/table caption opener lines;
    numeric inline citations `[12]`, `[12-15]`.
  - `transcript`: speaker labels (`SPEAKER:`, multi-word ALL-CAPS
    labels, `Q:`, `A:`, proper-name-colon at line start); timestamp
    markers (`[HH:MM:SS]`, `(MM:SS)`, line-start `HH:MM:SS`).
  - `review`: HTML tags and entities; star ratings (`5 out of 5
    stars`); review labels (`Verified Purchase`, `Vine Customer
    Review`, etc.); helpful-votes labels.
  - `comment`: URL stripping (`http(s)://...`, `www....`); @mentions
    and #hashtags preserved (they carry substantive content);
    emoticons preserved (they carry sentiment).
  - `other`: minimal cleaning only (whitespace collapse,
    control-character removal). Safety hatch for text kinds the
    taxonomy does not anticipate.
- Post-clean length sanity check: emits a non-blocking warning when
  the corpus's median text length falls outside the typical window
  for the declared texttype. Designed to surface mis-declarations
  (e.g., titles supplied as `text()` when `texttype(abstract)` is
  declared).

### Added — Unit tests

- `tests/test_load_corpus_drop.py` (six test cases for the Tier-1
  guardrails).
- `tests/test_hierarchy.py` (eleven test groups for the hierarchy
  detector).
- `tests/test_cleaners.py` (eight test groups, sixty-plus assertions
  for the six cleaning regimes, the dispatcher, idempotence, and the
  defaults helpers).
- All tests are pure-Python and do not require spaCy,
  sentence-transformers, or HDBSCAN.

### Changed

- Default `littext analyze` behaviour: rows with empty or whitespace-only
  `text()` are now dropped by default rather than silently producing no
  constructs. May reduce the `lt_diag` row count for corpora that
  previously contained empty cells. To restore the previous behaviour,
  pass `keepempty`.
- The v0.2.9 `_clean_text` function in `littext_pipeline.py` is
  deprecated and now delegates to `littext_cleaners._clean_abstract`.
  External code importing `_clean_text` continues to work unchanged.
- `python/littext_pipeline.py` now invokes `assign_hierarchy` after
  `cluster_constructs`. Adds approximately one second of runtime on a
  100-document corpus; cost scales linearly in the number of canonical
  forms.
- `python/littext_io.py` now writes the four hierarchy columns to the
  `lt_constructs` Stata frame.
- `python/littext_pipeline.py` threads `texttype` through
  `run_pipeline` to `_load_corpus`, which applies the selected
  cleaner.
- `_littext_analyze.ado` changed the `mintextlen()` option from
  `integer 200` to `string` so the package can detect whether the user
  passed it explicitly versus accepting the texttype-derived default.

### Migration notes

- Users who previously relied on `littext analyze` to retain empty rows
  in `lt_diag` will see those rows excluded by default. Pass `keepempty`
  to restore.
- The Stata-side variable check rejects numeric variables passed to
  `text()`; users who previously passed a numeric variable that
  happened to parse to a usable string must cast it with `tostring`
  before calling `littext analyze`.
- Users running on non-abstract corpora should declare the appropriate
  `texttype()` to enable the corresponding cleaner. The default
  `texttype(abstract)` is applied silently to legacy scripts but is
  accompanied by a visible note.
- The hierarchy detector and texttype cleaners are English-specific.
  Non-English corpora will produce mostly empty parent assignments
  and benefit only from `texttype(other)` minimal cleaning. A future
  release may add language-aware versions of both.
- Existing scripts that reference `lt_constructs` columns by name will
  continue to work; the four hierarchy columns are additions, not
  renames.

### Investigated but not implemented

- **F-pattern matcher extensions.** Originally scoped as commit 2 of
  the v0.3 cycle following a surface-level diagnostic of the v0.2.9
  pattern-F = 0 result. A parser-level diagnostic against the 99-
  document brand-equity corpus found that pattern F fires correctly on
  six of seven plausible candidates, including all four candidates the
  surface diagnostic had wrongly flagged as defects. The remaining
  four non-fires are correctly classified as non-F by the package (the
  anchor noun is a prepositional object or conjunct, not the predicate
  of a copula). No matcher work was carried out against this evidence.

## [0.2.9] - 2026-05-25

### Changed

- `_littext_analyze.ado` now uses a single `python script` invocation
  rather than the previous multi-line `python: ... end` block, which
  could not coexist with `program define` because the inner `end`
  keyword collided with the program's own `end` and produced a parser
  error at .ado load time.

### Fixed

- Frame state corruption when an inner graph command errored. Replaced
  with a copy-to-temp-frame idiom that is robust to errors.

## [0.2.8] - 2026-05-20

### Added

- Pattern F matcher (copular anchor): "X is an antecedent of Y",
  "X is the principal driver of Y", "X is a determinant of Y", etc.
  Three configurations: predicate-nominal attr, `as`-PP, and
  subject-of-copula structures.

## [0.2.7] - 2026-05-15

### Added

- `extraction_method` column on `lt_relations` distinguishing
  cooccur+dep patterns A through F from the cooccur-only fallback.
- `type(extraction)` graph option.
- Two matplotlib graph types: `cooccurrence` (pairwise NPMI heatmap)
  and `roles` (construct x relation-type heatmap).

### Changed

- `outdir()` option on `littext graph` now resolves relative paths
  against the Stata working directory rather than emitting them
  silently to an unpredictable location.

## [0.2.6] - 2026-05-10

### Added

- Corpus-size-aware `minfreq()` default. Corpora with fewer than 50
  documents now retain single-document constructs by default; corpora
  of 50 or more documents retain the v0.2.x default of 2. Resolved
  value and rationale are printed at run time.

## [0.2.0] - 2026-05-01

### Added

- Sentence-transformer embeddings via `sentence-transformers`. Default
  model `all-MiniLM-L6-v2`. `embedmodel()` option for override.
- HDBSCAN clustering of construct embeddings into synonym groups.
- Five matplotlib graph types: `map`, `network`, `dendrogram`,
  `frequency`, `distribution`.

## [0.1.3] - 2026-04-25

### Fixed

- Cluster splitting now applies after HDBSCAN's noise-point promotion,
  not before.

## [0.1.2] - 2026-04-20

### Changed

- Construct stop-list separated from relation trigger lexicon.

## [0.1.1] - 2026-04-15

### Changed

- HDBSCAN `min_cluster_size` is now fixed at 2 rather than scaling
  with corpus size.
- Within-cluster similarity filter splits any cluster whose minimum
  pairwise cosine similarity falls below 0.65.

## [0.1.0] - 2026-04-01

### Added

- Initial release.
- spaCy noun-chunk extraction for candidate constructs.
- Co-occurrence-based relation candidacy with normalised PMI scoring.
- Dependency-pattern matching for relationship valence: patterns A
  (mediation/moderation), B (active VSO), C (passive), D (nominal),
  E (adjectival valence).
- Three Stata frames: `lt_constructs`, `lt_relations`, `lt_diag`.
- Help file, short alias `litt`, end-to-end smoke test.
