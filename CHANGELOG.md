# Changelog

All notable changes to the `littext` Stata package are documented in this
file. The format is based on [Keep a Changelog](https://keepachangelog.com/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.4.8] - 2026-05-29

Hypothesis-register export (roadmap B3).

### Added

- New subcommand `littext export`: writes the candidate relationships from
  the most recent `littext analyze` (the `lt_relations` frame) as a clean
  candidate table for hand-curation, sorted by descending confidence so
  the strongest candidates are reviewed first. No curation columns are
  added (the analyst adds their own, per design).
- Options: `outdir()` (required, absolute, matching `littext graph`);
  `name()` (file stub, default `littext_register`); `format(csv|xlsx|both)`
  with full CSV quoting so evidence spans with commas survive; `minconf(#)`,
  `type()` (space/comma list), and `top(#)` filters to make a large
  candidate set reviewable; and `columns()` to override the default
  essentials-plus-provenance column set (`source target relation_type
  confidence evidence_text extraction_method doc_id`).
- `_littext_export.ado` (new file; declared in `littext.pkg`). It works on
  a copy of `lt_relations`, never disturbing the cached frame, and errors
  cleanly if no analysis is in memory.
- The smoke test (`tests/littext_smoke.do`) gained an export stage that
  re-runs the pipeline, exports a CSV register, and confirms it is written.

### Fixed

- `_littext_analyze.ado`: frame-state handling reworked so analyze is
  safe to run repeatedly in a session. Previously analyze ended with
  `lt_relations` as the active frame; a second analyze then failed two
  ways in sequence -- `r(111) variable ... not found` (because `text()`
  was validated against the now-active `lt_relations`, not the user's
  data) and, past that, `r(110) frame already defined` (because Stata
  cannot drop the current frame). Analyze now records the frame it was
  called from, switches there before dropping/recreating the output
  frames, and returns the user to it on exit (Option B). The result
  frames `lt_constructs` / `lt_relations` / `lt_diag` remain available by
  name. A guard handles the rare case where the entry frame is itself an
  output frame. The completion-message hints now use the `frame
  lt_relations:` prefix accordingly.
- `_littext_example.ado`: loads the corpus into the `default` frame, so
  the bundled example lands in a predictable frame regardless of what a
  prior analyze left active.

### Changed

- `littext.ado`: registered the `export` subcommand; also normalised the
  dispatcher to the project's `/* */` comment convention and refreshed the
  version stamp (it had carried a stale v0.2.9 header).
- `littext.sthlp` / `litt.sthlp`: documented `littext export`, its options,
  and examples. README updated with the file-layout entry and a usage note.

## [0.4.7] - 2026-05-29

Interactive (Plotly) output for all five matplotlib figure types
(roadmap B1b).

### Added

- `format()` option on `littext graph`: {static, html, both}. `static`
  (default) is the existing matplotlib PNG + PDF; `html` writes an
  interactive Plotly figure; `both` writes all three. Applies to the
  five matplotlib types (`map`, `network`, `dendrogram`, `cooccurrence`,
  `roles`); ignored with a note for the Stata-native types.
- `embed()` option: {selfcontained, cdn}. `selfcontained` (default)
  embeds plotly.js in the HTML (~3.5 MB) so it opens offline on any
  machine -- chosen as the default because the primary use is
  presentations and sharing; `cdn` writes a small file that requires an
  internet connection to render.
- `littext_viz.py`: five Plotly builders (`_plotly_network`,
  `_plotly_scatter`, `_plotly_heatmap`, `_plotly_dendrogram`) plus the
  `_save_html` / `_want_static` / `_want_html` helpers. The interactive
  network preserves the v0.4.5 edge policy (per-type colouring; never
  merged across valence) and supports the same `level()` roll-up as the
  static version. Verified end to end here: all four builders emit valid
  HTML, with self-contained files ~3.5 MB+ and CDN files a few KB.
- `tests/test_viz_format.py`: pure-Python unit tests for the
  format-selection helpers.
- `plotly` added to the required-package list in `littext_env.py`
  (so `littext install, verbose` checks it), the help Requirements
  section, the manifest description, and the README install line.

### Design notes

- matplotlib remains the static / publication engine; Plotly is purely
  additive. The two share each renderer's computed data (matrices,
  coordinates, edge lists) and branch on `format()`, so the static output
  is byte-identical to prior behaviour when `format(static)`.
- Plotly is imported lazily inside the builders, so `littext analyze` and
  static-only figures never pay the import cost.
- The "too few data" placeholder paths remain static-only; requesting
  `format(html)` on an empty corpus yields a static placeholder
  explaining why, which is acceptable.

## [0.4.6] - 2026-05-29

### Changed

- `littext graph`: `outdir()` is now effectively required. Previously,
  omitting it defaulted to `c(pwd)`, which on Windows could silently be
  Stata's own installation directory (observed: figures landing in
  `...\StataNow19\`). The command now stops with an actionable error when
  `outdir()` is omitted, rather than guessing a location. A relative path
  is still accepted but resolved against `c(pwd)` with a warning. The
  resolved absolute destination is printed on every save. This aligns the
  command with the package contract that output destinations are explicit
  and predictable.
- `_littext_graph.ado` header and `littext.sthlp` / `litt.sthlp` updated:
  `outdir()` documented as REQUIRED (no default).

### Migration notes

- Scripts that relied on the implicit `c(pwd)` default must now pass
  `outdir()` explicitly, e.g.
  `littext graph, type(map) outdir("D:/project/figures")`. This is a
  deliberate breaking change in a 0.x series: the prior default was
  unpredictable and could write into the Stata program folder.

## [0.4.5] - 2026-05-29

Construct-hierarchy roll-up for the matplotlib `map` and `network`
renderers (roadmap B1). `level()` is no longer ignored by these figures.

### Added

- `littext_viz._build_level_map`: a shared helper that maps each
  `canonical_form` to its rolled ancestor for `level(leaf|root|N)`. The
  integer-depth semantics mirror `_lt_remap_canonical` in
  `_littext_graph.ado` exactly (a construct at depth d > N is replaced by
  walking `parent_canonical` (d - N) steps; constructs at depth <= N are
  kept), so the Stata-native and matplotlib roll-ups agree. Degrades
  gracefully to leaf level with an explanatory note if the cached frame
  lacks the hierarchy columns.

### Changed

- `type(map)` honours `level()`: a rolled construct group is drawn as one
  point at the frequency-weighted centroid of its children's UMAP
  coordinates (a centroid, not a re-embedding), sized by summed
  `freq_doc`. Leaf level is unchanged from prior behaviour.
- `type(network)` honours `level()` with the edge policy chosen in design:
  endpoints are rolled, self-loops from collapsing are dropped, and
  parallel edges are aggregated by (rolled source, rolled target,
  relation_type) -- summed within a type, NEVER merged across types.
  Parallel edges of different types between a rolled pair are fanned by a
  small per-type curvature so both remain visible. Applies to both the
  type-coloured and the `weighted` (confidence-coloured) views.
- `_littext_graph.ado`: removed the warn-and-ignore block for
  `level()` with matplotlib types; `level` is now passed to
  `draw_figure`. `draw_figure` gained a `level` parameter.
- `littext.sthlp` / `litt.sthlp`: `level()` documentation updated to
  describe map/network support, the centroid rule, the edge policy, and
  the explicit exclusion of the heatmaps and the distance-based
  dendrogram. Added `level()` examples for `network` and `map`.

### Notes

- `type(dendrogram)` deliberately does NOT roll up: its tree is built from
  HDBSCAN cluster distances, not the lexical construct hierarchy, so a
  hierarchy roll-up would mislabel the structure it draws. The heatmaps
  (`cooccurrence`, `roles`) likewise ignore `level()`. All three emit a
  one-line note if a non-leaf level is requested. Interactive (Plotly)
  versions of these figures are scheduled for the next commit.
- The roll-up logic is unit-verified against a synthetic three-level
  hierarchy (root/0 collapse to the root; level 1 collapses depth-2 to
  its depth-1 parent; level 2 is a no-op), matching the Stata-native
  path.

## [0.4.4] - 2026-05-29

Relation-extraction evaluation harness with a regression floor.

### Added

- `tests/claude_eval_relations.py`: a pure-standard-library scorer that
  compares extracted relations against the synthetic gold and reports
  precision / recall / F1 overall and by relation type, exiting non-zero
  when overall F1 falls below a floor. Matching policy: relation types
  must agree; construct endpoints match by normalized exact OR symmetric
  substring containment (`--match exact|substring`); directed types match
  in order while `assoc` matches either orientation; moderation and
  mediation are scored as triples by parsing the gold's `X -> Y` target
  encoding. Counting is greedy one-to-one. Verified self-consistent
  (gold-vs-gold yields F1 = 1.000 with all 317 triples parsed).
- `tests/test_eval_relations.py`: seventeen pure-Python unit tests for
  the matching engine (normalization, exact vs substring, directionality,
  symmetric `assoc`, triple parsing and matching, one-to-one counting,
  PRF math, and confirmation that substring containment over-matches
  short tokens).
- `tests/littext_eval.do`: the Stata harness. Runs the pipeline on the
  example corpus, exports `lt_relations`, and shells out to the scorer.
  Batch-mode exit code 9 below floor, 0 on pass.

### Design notes

- Two-stage by construction: Stata produces extractions (needs spaCy and
  the embedder); Python scores them (deterministic, dependency-light,
  CI-friendly). The scorer is unit-testable without Stata.
- The floor is NOT hardcoded by guesswork. The harness ships with the
  floor at 0 (report-only) so the first run is a calibration pass; the
  observed F1 then sets a floor slightly below it, tolerant of the
  HDBSCAN / embedding run-to-run variation.
- HONEST SCOPE: these numbers are a development REGRESSION FLOOR, not
  external validation. The synthetic gold is generated from the same
  construct and dependency-pattern substrate the extractor targets, so
  the scores are optimistically biased and must not be reported as the
  paper's validation. External validity still requires independently
  coded data.
- PROVISIONAL on the extracted side: the moderation/mediation matcher
  assumes `lt_relations` encodes these the way the gold does (target =
  `X -> Y`). This assumption is isolated in `_extracted_record()` and the
  harness warns if no extracted mod/med row parses as a triple. It must
  be validated against a real `lt_relations`; if the schema differs, only
  that one function changes.

## [0.4.3] - 2026-05-29

End-to-end smoke / regression test (roadmap A3).

### Added

- `tests/littext_smoke.do`: the per-commit regression guard. It runs the
  full pipeline on the bundled example corpus and asserts that the output
  is structurally correct: the three frames (`lt_constructs`,
  `lt_relations`, `lt_diag`) exist and are non-empty; `lt_relations`
  carries `source`, `target`, `relation_type`, `confidence`, `evidence`,
  `extraction_method`; `lt_constructs` carries the v0.3.2 hierarchy
  columns (`canonical_form`, `parent_canonical`, `canonical_root`,
  `hierarchy_depth`, `is_root`); observed `relation_type` values fall
  within the documented vocabulary; and the static example (300 rows)
  and gold (1280 rows) load with their exact expected shapes. In batch
  mode it exits with OS code 9 on any failure, 0 on pass.

### Design notes

- The test asserts EXACT counts only on static data (the 300-row corpus
  and 1280-row gold), where a wrong count signals data corruption, and
  THRESHOLD (non-empty) assertions on pipeline output, because construct
  and relation counts vary run to run with the HDBSCAN and embedding
  stages. Exact-count assertions on pipeline output would be flaky.
- Column checks are per-column so a failure names the exact missing
  column rather than failing an entire varlist opaquely.
- It is distinct from `claude_verify_install.do`: that verifies packaging
  and path resolution (clean-room net install, bridge); this verifies
  pipeline OUTPUT against whatever littext is on the adopath. The smoke
  test does not manipulate PLUS and is the lighter, run-on-every-change
  guard.
- The test suite is now heterogeneous: the pure-Python unit tests
  (`test_cleaners.py`, `test_hierarchy.py`, `test_load_corpus_drop.py`)
  run from the command prompt via Python; the smoke test runs in Stata
  (interactively or via `stata -b do tests/littext_smoke.do`). It is not
  added to `littext.pkg`; like the other tests it lives in the repository
  only, not the installed footprint.

## [0.4.2] - 2026-05-29

Example-data wiring (roadmap A2). `littext example` is now functional,
backed by a single canonical synthetic corpus.

### Added

- `data/littext_example.dta` (300 abstracts) and
  `data/littext_example_gold.dta` (1280 ground-truth relations), both
  declared `F` (force-installed) in `littext.pkg` so
  `_littext_example.ado` can `findfile` them after a flattened install.
  The `abstract` column is stored as `strL` because four abstracts
  exceed the str2045 ceiling (max 2106 bytes); this is lossless and
  requires .dta format 117+.
- `claude_make_example_dta.py`: the dependency-light (pandas-only)
  provenance script that builds the two `.dta` files from the RBV CSVs,
  with an integrity report (row counts, id linkage, relation-type
  distribution). A development artifact; not installed.
- The verification `.do` now includes an example-data stage: it loads
  `littext example`, asserts the expected 300-row / 1280-row shapes and
  the expected variables, loads the gold, and analyses the example
  corpus end to end.

### Changed

- `_littext_example.ado` rewritten for a single canonical corpus. The
  prior `n(30)` / `n(200)` dual-size scheme is removed; `littext
  example` now takes only `gold` and `clear`. Backward compatibility
  with the `n()` option is intentionally NOT preserved (the old corpora
  never existed on disk).
- `littext.pkg`: added the two example `.dta` files as `F` and the CSV /
  XLSX / corpus-README mirrors as ancillary `f`.
- `littext.sthlp` / `litt.sthlp`: removed `n(#)` from the `littext
  example` syntax and from the examples; the examples now use the single
  300-abstract RBV corpus. Version stamp 0.4.2.
- `README.md`: documents the working `littext example`, lists the two
  `.dta` files, and states the five gold relation types explicitly.
- `CITATION.cff`: version 0.4.2.

### Notes

- The gold corpus uses five relation types (`pos_assoc`, `neg_assoc`,
  `moderates`, `mediates`, `assoc`); `assoc` appears only twice and is
  effectively a non-directional fallback. The extractor's documented
  vocabulary additionally includes `causes`, which the synthetic gold
  does not exercise. Reconciling the extractor-to-gold relation-type
  mapping is a prerequisite for any evaluation harness (deferred).
- The synthetic corpus is generated from the same construct and
  dependency-pattern substrate the extractor targets; it is a controlled
  regression anchor, not a basis for reporting precision/recall as
  external validation.

## [0.4.1] - 2026-05-28

Packaging and distribution: LICENSE, manifest correctness, and a
documentation refresh toward a GitHub/SSC release. No pipeline
behaviour changes.

### Added

- GPL-3.0 `LICENSE` file at the package root, referenced by the help
  file and README. Declared `F` (force-installed) in `littext.pkg` so
  the licence text accompanies the code on a default install.
- `claude_check_manifest.py`: a dependency-free diagnostic, run from
  the command prompt, that parses `littext.pkg`, confirms every
  declared file exists on disk, flags any `python/*.py` on disk that is
  absent from the manifest (the class of defect that hid the missing
  cleaners and hierarchy modules), and warns when a Python module is
  declared `f` rather than `F`. Development artifact; not part of the
  installed footprint.

### Changed

- `littext.pkg`: the Python pipeline modules are now declared with the
  force-install directive `F` instead of `f`. Under `f`, files without
  an `.ado`/`.sthlp` suffix are treated as ancillary and are NOT placed
  on the adopath by a default `net install` / `ssc install`, which left
  the package unable to import its own pipeline on a clean install.
- `littext.pkg`: added `python/littext_cleaners.py` and
  `python/littext_hierarchy.py`, introduced in v0.3.3 and v0.3.2 but
  never added to the manifest and therefore never installed.
- `littext.pkg`: added `LICENSE`; rewrote the explanatory header to
  describe the `f`-versus-`F` semantics and to note that the `python/`
  path component is the fetch path, not a reproduced adopath
  subdirectory; refreshed `Distribution-Date` to 20260528.
- `littext.sthlp` / `litt.sthlp`: corrected the dangling `LICENCE`
  reference to `LICENSE`; bumped the version stamp to 0.4.1; corrected
  the `level()` note that wrongly attributed the matplotlib limitation
  to v0.3.0; shortened one over-length SMCL example line.
- `stata.toc`: refreshed `Distribution-Date`; updated the versioned-
  subdirectory example from 0.3 to 0.4.
- `README.md`: corrected the file-layout tree to match the actual
  package contents; completed the Python-module list; corrected the
  visualisation table (ten figure types, not seven); set the current
  release to 0.4.1; replaced the claim that `littext_example.dta`
  ships with an interim manual-import note for the synthetic RBV
  corpus pending example-data wiring.
- `CITATION.cff`: set version 0.4.1 and corrected the release date
  (the prior value post-dated the build).
- New `_littext_resolve.ado`: a shared helper that locates a packaged
  resource (a `python/` module or a `data/` file) across both on-disk
  layouts -- the development tree (with `python/` and `data/`
  subdirectories) and the flattened adopath produced by `net install`.
  It returns `r(dir)` and `r(path)` and fails with an actionable
  message if the resource is in neither layout. Added to the manifest.
- `_littext_analyze.ado`, `_littext_install.ado`, `_littext_graph.ado`,
  and `_littext_example.ado` no longer assume a `python/` (or `data/`)
  subdirectory beneath the `.ado`; each now calls `_littext_resolve`.
  This fixes the defect whereby a `net install`-ed package could not
  import its own pipeline, because the modules are force-installed flat
  rather than under `python/`.
- `_littext_graph.ado`: removed a `///` line continuation (one
  statement per line) and corrected the matplotlib `level()` note that
  wrongly cited v0.3.0.

- `_littext_resolve.ado`: corrected the resolution mechanism. The first
  implementation reconstructed the module path from littext.ado's
  directory (`<dir>/python/` then `<dir>/`). That is wrong for an
  installed package: net install distributes force-installed files into
  the PLUS letter/extension subdirectories (littext.ado to `l/`,
  `_littext_*.ado` to `_/`, the Python modules to their own subdir), so
  the modules are neither beside littext.ado nor under a `python/`
  subfolder. The resolver now calls `findfile` on the target file (the
  correct adopath-wide mechanism for force-installed files) and falls
  back to the `<pkgdir>/python|data/` layout only for the development
  tree, where that subdirectory is not on the adopath. The four callers
  are unchanged.

- `_littext_analyze.ado`: rewrote the six texttype-default assignments
  (lines 51-56) from the single-line inline-brace form
  `if cond { local ... ; local ... }` to proper multi-line blocks, one
  statement per line. Stata's block parser requires the opening brace to
  end its line and the closing brace to begin a line; the inline form
  produced "matching close brace not found" (r198) at program-definition
  time, which surfaced the first time `analyze` parsed past the syntax
  stage on a clean install. The branch logic and values are unchanged.

### Known issues carried forward

- `littext example` is non-functional: it loads `littext_example.dta`,
  which is not present in `data/`. Example-data wiring is deferred to
  the next commit. Until then, load the synthetic RBV corpus from
  `data/` manually (see `data/littext_rbv_synth_v01_README.md`).
- The flattened-install path fix now uses `findfile` on the target
  module (with a development-layout fallback) across all four
  path-resolving subcommands via `_littext_resolve`. Verified that the
  installed modules resolve via findfile; the final gate is a clean-room
  run in which the bridge import (`littext install, verbose`) and a
  three-row analyze both succeed, confirming the modules are co-located
  on the directory the resolver returns.

### Migration notes

- Users who installed a pre-0.4.1 build with `net install` (without
  `, all`) will not have the Python modules on the adopath and should
  reinstall once 0.4.1 is published.

## [0.3.4] - 2026-05-28

### Changed

- Abstract texttype length-sanity window raised from (200, 6000) to
  (200, 10000) characters. The upper bound now tolerates
  extended-abstract formats of up to roughly 1500 words (conference
  and some journal extended abstracts), which previously triggered a
  spurious "median text length above typical window" warning. The
  trade-off is a slightly reduced ability to catch full-text-as-
  abstract misdeclaration; the >25% row-drop warning remains as a
  second line of defence.

## [0.3.3] - 2026-05-27

Tier-2 text-kind declaration with pluggable cleaning regimes.

### Added

- New option `texttype()` on `littext analyze`. Accepts `abstract`
  (default), `fulltext`, `transcript`, `review`, `comment`, `other`.
- When `texttype()` is not declared, the package defaults to
  `texttype(abstract)` and emits a visible note indicating that this
  default was applied.
- `texttype()` drives three downstream defaults: which cleaning regime
  is applied; the default segmentation `unit()`; and the default
  `mintextlen()`. Each derived default is overridable by passing the
  corresponding option explicitly. The resolved values and their
  sources ("user-specified" vs "texttype default") are printed at run
  time.
- New module `python/littext_cleaners.py` containing six pluggable
  cleaning regimes:
  - `abstract`: Emerald section headers; copyright tails; arXiv
    Comments/Subjects/etc. tags. Preserves the prior `_clean_text`
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
- New unit test `tests/test_cleaners.py` (eight test groups,
  sixty-plus assertions for the six cleaning regimes, the dispatcher,
  idempotence, and the defaults helpers). Pure-Python; no spaCy,
  sentence-transformers, or HDBSCAN required.

### Changed

- The prior `_clean_text` function in `littext_pipeline.py` is
  deprecated and now delegates to `littext_cleaners._clean_abstract`.
  External code importing `_clean_text` continues to work unchanged.
- `python/littext_pipeline.py` threads `texttype` through
  `run_pipeline` to `_load_corpus`, which applies the selected
  cleaner.
- `_littext_analyze.ado` changed the `mintextlen()` option from
  `integer 200` to `string` so the package can detect whether the user
  passed it explicitly versus accepting the texttype-derived default.

### Migration notes

- Users running on non-abstract corpora should declare the appropriate
  `texttype()` to enable the corresponding cleaner. The default
  `texttype(abstract)` is applied silently to legacy scripts but is
  accompanied by a visible note.
- The texttype cleaners are English-specific. Non-English corpora
  benefit only from `texttype(other)` minimal cleaning.
- `texttype(comment)` segments at sentence level, not document level:
  the segmenter supports `sentence`, `abstract`, and `paragraph` only.

## [0.3.2] - 2026-05-27

Construct-hierarchy detector.

### Added

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
- New unit test `tests/test_hierarchy.py` (eleven test groups).
  Pure-Python; no spaCy or HDBSCAN required.

### Changed

- `python/littext_pipeline.py` now invokes `assign_hierarchy` after
  `cluster_constructs`. Adds approximately one second of runtime on a
  100-document corpus; cost scales linearly in the number of canonical
  forms.
- `python/littext_io.py` now writes the four hierarchy columns to the
  `lt_constructs` Stata frame.

### Migration notes

- Existing scripts that reference `lt_constructs` columns by name will
  continue to work; the four hierarchy columns are additions, not
  renames.
- The hierarchy detector is English-specific. Non-English corpora will
  produce mostly empty parent assignments, which is the safe default.

## [0.3.1] - 2026-05-26

Tier-1 corpus-input guardrails.

### Added

- Two new options on `littext analyze`: `mintextlen(#)` setting the
  minimum text length in characters, and `keepempty` to disable
  row-dropping entirely.
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
- New unit test `tests/test_load_corpus_drop.py` (six test cases).
  Pure-Python; no spaCy required.

### Changed

- Default `littext analyze` behaviour: rows with empty or
  whitespace-only `text()` are now dropped by default rather than
  silently producing no constructs. May reduce the `lt_diag` row count
  for corpora that previously contained empty cells. To restore the
  previous behaviour, pass `keepempty`.
- `_load_corpus` signature now accepts `min_text_len` and `keep_empty`
  parameters (defaults preserve the prior behaviour when called
  directly).

### Migration notes

- Users who previously relied on `littext analyze` to retain empty rows
  in `lt_diag` will see those rows excluded by default. Pass `keepempty`
  to restore.
- The Stata-side variable check rejects numeric variables passed to
  `text()`; users who previously passed a numeric variable that
  happened to parse to a usable string must cast it with `tostring`
  before calling `littext analyze`.

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
  of 50 or more documents retain the prior default of 2. Resolved
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
