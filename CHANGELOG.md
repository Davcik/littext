# Changelog

All notable changes to `littext` are recorded here. This is a summary for
users; the format follows [Keep a Changelog](https://keepachangelog.com/)
and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-17

### Added

- First public release.

`littext` extracts candidate construct relationships from a corpus of
academic text and returns them as Stata frames, with figures and a
curatable hypothesis-register export.

### Features

- `littext analyze` — the pipeline: noun-chunk construct extraction
  (spaCy), sentence-transformer embeddings, HDBSCAN synonym clustering,
  lexical construct-hierarchy detection, and candidate-relationship
  scoring via dependency patterns and normalized pointwise mutual
  information. Results are returned in three frames: `lt_constructs`,
  `lt_relations`, `lt_diag`.
- `littext graph` — ten figure types (five Stata-native, five
  matplotlib). The matplotlib types support the construct-hierarchy roll-up
  via `level()` and interactive Plotly HTML via `format(html|both)`.
- `littext export` — writes the candidate relationships as a hypothesis
  register (CSV and/or XLSX), sorted by confidence, with `minconf()`,
  `type()`, and `top()` filters for triage.
- `littext example` — loads a bundled synthetic resource-based-view
  corpus (300 abstracts) for demonstration and reproducible examples.
- `littext install` — verifies the Python environment and required
  packages.

### Notes

- The bundled corpus is synthetic and is provided for illustration and
  reproducible examples only; it is not a real bibliometric sample.
- Figure-producing commands require an absolute-path `outdir()`.
- Relationship valence (`relation_type`) and affective sentiment
  (`text_polarity`, optional via `addsentiment`) are distinct; the second
  is not a measure of the first.

## [0.1.0] - 2026-04-01

### Added

- Initial release.

---

A detailed development history (the v0.1*–v0.4* iteration log, with
design-decision rationale) is maintained separately by the author.
