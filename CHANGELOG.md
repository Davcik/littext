# Changelog

All notable changes to `littext` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.9] – 2026-05-24

### Background

The v0.2.8 trace diagnostic on three real F-candidate sentences from the
99-document corpus produced a decisive result: pattern F fires correctly
when `_classify_pair` is called directly with the surface forms that
actually appear in the parsed sentence. Yet the full pipeline run on the
same corpus produced zero F-matches. The gap between in-isolation success
and in-production failure was traced to a silent fallback in
`_classify_pair`: when the canonical_form of a construct (passed as
identifier in the relation matcher's pair loop) differs lexically from
any token sequence present in the sentence, `_find_construct_span`
returns None and `_classify_pair` falls through to "Z" without trying
any of the six dependency patterns.

This affected every pair where HDBSCAN clustering relabelled a surface
form to a canonical form with a different surface (e.g. surface
"loyalty" clustered under canonical "brand loyalty"; surface "online
experience" clustered under canonical "online environment"). The bug is
present from v0.2.0 onward; it is not new in v0.2.8. It explains the
suppressed counts in patterns B, C, D, E, and F across the 33-document
and 99-document validation runs.

### Added
- `_find_any_span(doc, surfaces)` in `littext_relate.py`: tries each
  surface form in the candidate list, longest first, and returns the
  first contiguous match. Accepts a string (backwards-compatible) or a
  list. Underlies the v0.2.9 fix without changing the single-surface
  `_find_construct_span` helper.
- `_classify_pair` gained optional `a_surfaces` and `b_surfaces`
  parameters. When supplied, span lookup uses the surface lists; the
  canonical forms `a` and `b` continue to be used as the source and
  target identifiers in the returned row. Default behaviour
  (a_surfaces=[a], b_surfaces=[b]) preserves backwards compatibility for
  test scripts and direct calls.

### Changed
- The `score_relations` loop now builds a `canon_to_surfaces` map from
  the constructs frame and passes each cluster's full surface-form list
  to `_classify_pair`. The relation matcher's pair iteration remains
  keyed on canonical forms; the span lookup now traverses the cluster.

### Expected effect on the 99-document validation corpus

The trace identified three exact sentences where pattern F was being
silently disabled by this bug. Direct calls to the v0.2.8 implementation
on those sentences with surface forms returned valid F-matches; production
calls with canonical forms returned Z. The v0.2.9 fix should restore
those three matches and likely a similar number of B/C/D/E matches that
were affected by the same span-lookup failure.

Predicted v0.2.9 directional-row count: 70-90 (up from 61 in v0.2.7 and
v0.2.8). The increase will come predominantly from pattern F (the
patterns most sensitive to span recovery in long sentences) and from
pattern D (which uses subtree walks that also depend on accurate
construct-span anchoring).

### Provenance note for the methods paper

This bug is a methodologically interesting case: an architectural
shortcut taken in v0.2.0 (the canonical/surface mapping in the relation
matcher) interacted with the synonym clustering step to silently disable
the dependency-pattern matchers in a fraction of pairs. Neither
component was wrong in isolation; the bug emerged from their
composition. The v0.2.9 fix illustrates the value of evidence-based
diagnostics over hypothesis-based fixes: had we shipped v0.2.9 as a
guess (e.g. "perhaps pattern F needs a wider lexicon"), we would have
left the underlying bug in place and made the symptom marginally worse
by adding more patterns whose span lookups would also fail. The trace
that pinpointed the canonical-vs-surface mismatch was perhaps thirty
minutes of work that prevented an indefinite cycle of speculative fixes.

## [0.2.8] – 2026-05-20

### Background

The v0.2.7 evaluation on a 99-document marketing-research corpus surfaced
three concrete failure modes: methodological boilerplate contaminating
the constructs frame (the most visible offenders being "main purpose",
"recent years", "thematic analysis", "non-participatory netnography",
and geographic locations); a regression in pattern F (zero matches on
the larger corpus despite the presence of approximately 25 candidate
sentences); and a tokenisation artefact where parenthetical glosses
left a leading "(" attached to a construct token (the most visible case
being "(cbbe" for "(consumer-based brand equity)").

### Added
- Pattern F (copular nominal anchor) now recognises two additional
  syntactic configurations that surfaced in real-corpus parses:
  (config 2) "X as [anchor] of Y" - the anchor noun is the pobj of an
  "as" preposition whose head is a matrix verb; the X-construct is the
  matrix verb's dobj (preferred) or nsubj. This catches sentences such
  as "the model incorporates X as determinants of Y" and "we analyze X
  as a determinant of Y", which appeared roughly a dozen times in the
  v0.2.7 corpus but matched no pattern.
  (config 3) "The [anchor] of Y is X" - the anchor noun is itself the
  nsubj of a copula, and X is the attr/acomp. This is the structural
  inverse of the canonical configuration and is common in marketing
  abstracts that lead with the relationship anchor.
- Stop-list expansion (`_STOP_PHRASES` in littext_extract.py) added 56
  entries drawn empirically from the v0.2.7 constructs frame. Categories:
  writing boilerplate ("main purpose", "recent years", "previous studies",
  "existing literature", "theoretical framework", "proposed conceptual
  model", etc.), geographic scope markers ("china", "chinese consumers",
  "kuwait", "united arab emirates", "united states"), and methodology
  role markers ("frequency analysis", "thematic analysis", "data analysis",
  "non-participatory netnography"). Statistical methods (PLS-SEM, ANOVA,
  confirmatory factor analysis, partial least squares, structural equation,
  extended technology acceptance model) are DELIBERATELY RETAINED as
  legitimate constructs, per the design principle that research-methods
  vocabulary is itself an object of empirical inquiry in the marketing
  literature.

### Changed
- `_clean_chunk` in littext_extract.py now strips leading/trailing bracket,
  brace, angle-bracket, quote, and stray punctuation characters from
  candidate constructs. The most visible case this fixes is parenthetical
  glosses where spaCy absorbs the opening "(" into the following token
  (e.g. "(cbbe" for "(consumer-based brand equity)"). Quotes and stray
  comma/semicolon/colon characters are stripped for the same reason.
  Six lines of code; testable via the simple cases ("(cbbe" -> "cbbe",
  "brand equity)" -> "brand equity").
- Pattern F's Config 1 (canonical "X is the [anchor] of Y") tightened
  to require that the ancestor walk from anchor to copula passes only
  through bridge dependencies (amod, compound, nmod, det, quantmod). The
  v0.2.4 walk accepted any ancestor verb as the copula, which incorrectly
  poached the nsubj of unrelated matrix verbs in the Config 2 case
  ("we analyze X as determinant of Y"). Tightening Config 1 was a
  prerequisite for Configs 2 and 3 to fire.

### Provenance note
- The v0.2.8 pattern F revision is a third instance of evidence-based
  refinement in this package's development: a controlled vocabulary
  ([_COPULAR_ANCHOR_LEXICON]) was already in place from v0.2.3, but its
  syntactic match conditions did not cover the configurations that real
  marketing prose actually uses. The lesson, suitable for inclusion in
  the eventual methods paper: even a well-chosen lexicon must be paired
  with empirically-validated syntactic templates - a lexicon alone does
  not guarantee coverage.
- The stop-list separation principle established in v0.1.2 is preserved:
  methodology role markers ("mediating role", "antecedents") remain
  excluded from the constructs frame while continuing to function as
  triggers in the relation matcher. v0.2.8 extends this principle to
  writing boilerplate and geographies, with statistical methods explicitly
  kept on the constructs side at user request.

## [0.2.7] – 2026-05-18

### Added
- New graph type `extraction`: Stata-native horizontal bar of relations
  by `extraction_method`. Surfaces at a glance how many candidate
  relationships came from each dependency-pattern matcher
  (cooccur+dep:A through F) versus the cooccur fallback. Useful for
  rapid quality assessment of a run.
- New graph type `cooccurrence`: matplotlib heatmap of pairwise relationship
  confidence among the top-k canonical constructs. Cell intensity (YlOrRd
  colourmap) encodes the maximum confidence found between each construct
  pair. Diagonal cells and absent pairs are shown in light grey. Complements
  the network graph: the network shows discrete high-confidence edges; the
  heatmap shows the full pairwise landscape including weak relationships.
- New graph type `roles`: matplotlib heatmap with the top-k constructs as
  rows and the six relation types as columns. Cell values are counts of
  how often each construct participated in each relation type. Cells are
  annotated with their counts. Substantively informative: surfaces which
  constructs tend to function as mediators, moderators, sources of
  positive associations, etc.
- New option `weighted` on `type(network)`: colours edges continuously by
  confidence (viridis colourmap) rather than discretely by relation type.
  A colourbar replaces the discrete legend. Useful when edge strength
  matters more than syntactic type.

### Changed
- Graph dispatcher type validation message restructured to list Stata-native
  versus matplotlib types separately, since the user-facing distinction is
  whether the output is editable in Stata's graph window.
- `littext.sthlp` updated to document the three new types and the
  `weighted` option. The graph syntax line now reflects the additions.

### Use cases unaffected
- The five pre-existing graph types (`frequency`, `distribution`, `trend`,
  `confidence`, `map`, `network`, `dendrogram`) behave identically to v0.2.6.
- The `outdir()` semantics (default to `c(pwd)`, accept absolute paths,
  warn on relative paths) apply uniformly to all ten graph types.

### Provenance note
- The two heatmaps (`cooccurrence` and `roles`) close a gap that earlier
  versions of the package showed at SSC-suitability inspection: text-mining
  packages from other ecosystems (BERTopic, Leximancer) routinely offer
  co-occurrence matrix views, and reviewers used to those tools were
  likely to expect at least one heatmap-style visualisation. The `roles`
  heatmap is the substantively distinctive contribution; it exploits the
  package's six-element controlled vocabulary in a way that generic
  text-mining tools cannot.

## [0.2.6] – 2026-05-10

### Background

The v0.2.5 production run on 33 real marketing abstracts produced 12
directional rows. Offline simulation of the same patterns against the
parse trees of specific test sentences predicted 15-25. Reconciling the
gap revealed the upstream cause: the noun-chunk extractor's `minfreq=2`
default filters out single-document constructs, and on a small corpus
the constructs of greatest theoretical interest (e.g. emotional contagion,
message consistency, market performance) appear in only one document
each. They are pruned before the relation matcher sees them.

### Changed
- `_littext_analyze.ado`: the `minfreq()` option default is now
  corpus-size-aware. When the user does not pass `minfreq()` explicitly,
  the default is `1` for corpora with fewer than 50 documents and `2`
  for corpora of 50 or more. The user-supplied value overrides in either
  case. The resolved `minfreq` value and the rationale ("default for
  small corpora", "default for corpora of N documents", or "user-specified")
  are printed at run time so the user understands what was applied.
- The `MINFreq()` syntax declaration changes from `(integer 2)` to
  `(string)` because Stata's `integer N` form forces a default; we need
  to detect "user did not specify" reliably, which requires a string-typed
  option that we validate after parsing.

### Help
- `littext.sthlp` updated to document the new `minfreq()` default and the
  reasoning behind it. SMCL line lengths verified under 120 bytes.

### Visualisation
- No changes to the visualisation layer. The seven graph types
  (frequency, distribution, trend, confidence, map, network, dendrogram)
  continue to operate on the three output frames and are agnostic to the
  `minfreq` value applied. The v0.2 `extraction_method` column can be
  visualised with one line of Stata after analyze:
  `graph hbar (count), over(extraction_method) ytitle("Number of relationships")`.
  A dedicated `type(extraction)` graph option may be added in v0.2.7
  if useful.

### Expected behaviour on the 33-abstract test corpus
- Construct count should rise from 55 (v0.2.5) toward roughly 80-100,
  with the additional constructs being the theoretically distinctive
  single-document phrases.
- Directional row count should rise from 12 (v0.2.5) toward 20-30 as
  the v0.2.5 patterns get to fire on the previously-pruned constructs.

## [0.2.5] – 2026-05-07

### Background

A ten-case parse-tree inspection on real marketing abstracts identified
six concrete failure modes in v0.2.4. The most consequential finding was
that PP attachment of phrases such as "on the formation of brand equity"
is unstable across spaCy parser runs: the same sentence may attach the
phrase to the relationship anchor noun ("effect") in one run and to a
noun inside its subtree ("tools") in the next. Pattern D in v0.2.4
inspected only direct children of the anchor and therefore missed every
case where the parser made the alternative attachment.

### Added
- `_collect_preps_in_subtree(anchor, prep_texts, max_depth=3)`: returns
  every preposition token whose surface text is in `prep_texts`, reachable
  from `anchor` through prep/pobj/conj/nmod/compound/amod arcs. Used by
  patterns D and E to find "on", "for", "between", "with" prepositions
  anywhere in the anchor's local subtree rather than only as direct
  children.
- Pattern A: nominal mediation/moderation branch. When the trigger
  (`mediating` or `moderating`) has `pos_=VERB` but `dep_=amod`, the
  matcher now recognises it as an adjectival modifier of a head noun
  (typically `role` or `effect`) and identifies the head noun's
  "of"-pobj as the mediator. Previously this construction fell through
  to the verbal branch and either misfired or missed. This pattern is
  pervasive in marketing prose ("the mediating role of X").
- Pattern D: new branch for "X have an effect on Y" where the source
  is the nsubj of the matrix verb that takes the anchor as dobj. This
  catches the construction where the anchor noun lacks an "of"-pobj
  because the source is realised verbally rather than nominally.
- Pattern E: same matrix-verb-nsubj branch as pattern D, layered with
  adjectival valence.

### Changed
- `_POS_LEMMAS` extended with `affect`, `shape`, `determine`, `explain`,
  `contribute`, `influence`, `impact`. These bipolar verbs are pervasive
  in empirical marketing prose. They default to `pos_assoc`; explicit
  negative valence is recovered separately by pattern E when an adjacent
  valence adjective modifies a relationship-anchor noun in the same
  sentence.
- `_sentence_flags`: detection of valence adjectives on relationship-anchor
  nouns now follows `conj` chains from `amod` adjectives. "A significant
  and positive relationship" parses as amod(significant -> relationship)
  and conj(positive -> significant), so "positive" is not a direct amod
  child of the anchor. The v0.2.4 check missed this; v0.2.5 walks the
  conj.
- Pattern D and E "between A and B" handling now accepts `nmod` as well
  as `conj` for the second conjunct's dependency to the head pobj, since
  spaCy parses this construction inconsistently.

### Provenance note for the methods paper
- v0.2.5 is the second example in the package's development of evidence-
  based pattern refinement: the v0.2.4 patterns assumed PP attachment is
  stable; parse inspection on real abstracts proved otherwise. The
  methodological lesson, suitable for inclusion in the eventual paper:
  NLP pattern-matching against statistical parsers must accommodate the
  parser's actual output distribution, not the linguist's expected output.

## [0.2.4] – 2026-04-23

### Background

Diagnostic inspection of v0.2.3 on the real 33-abstract corpus revealed
that the new patterns (in particular pattern F, the copular nominal
anchor) failed to fire on sentences they were explicitly designed for.
A token-level parse inspection on the sentence "trust is the most
important antecedent of e-loyalty in online shopping for Gen Y customers"
showed the root cause: spaCy's tokenizer splits hyphenated nouns into
three separate tokens ("e", "-", "loyalty"), and the dependency labeller
attaches each as a SEPARATE pobj of the governing preposition. The
v0.2.3 traversal logic in six places used a "for grand in child.children:
if grand.dep_ == 'pobj': break" pattern that returned only the FIRST
pobj. On hyphenated constructs this was almost always the wrong fragment.

### Added
- Helper `_all_pobjs(prep_token)` returns ALL pobj children of a
  preposition rather than the first. Multi-pobj prepositions occur with
  hyphenated nouns (spaCy tokenizer split), with conjoined NP objects
  ("between A and B"), and with apposition.
- Helper `_any_pobj_reaches(prep_token, span)` is a convenience that
  combines `_all_pobjs` with `_construct_anywhere_below` for the common
  pattern of asking "does any pobj of this prep reach the construct?"

### Changed
- All six single-pobj traversal sites across patterns B, C, D, E, and F
  now collect ALL pobjs and use `any()` over the resulting lists.
- Pattern F also now walks UP from the anchor noun through ancestors
  (until it finds a copula or verb) rather than checking only the
  immediate head. This handles the case where an adjective intervenes
  between the anchor and the copula (e.g. "...important antecedent of...",
  where "antecedent" attaches to "is" but only via "important" in some
  parses).

### Provenance note for the eventual Stata Journal paper
- The v0.2.3 → v0.2.4 transition is a good example of evidence-based
  pattern refinement: the v0.2.3 patterns were designed from textbook
  English-grammar templates ("X is the antecedent of Y"); the v0.2.4
  fixes came from inspecting actual spaCy parse trees of real marketing
  abstracts. The methodology lesson is that NLP-style patterns must be
  validated against real parser output, not against the linguist's mental
  model of the grammar.

## [0.2.3] – 2026-04-20

### Background

Diagnostic inspection of the v0.2.2 output on a 33-abstract real
marketing corpus revealed that the five dependency-arc pattern matchers
(A through E) collectively fired on only 6 of 94 candidate relationships.
The architecture was sound but the pattern coverage was too narrow: real
academic marketing prose expresses directional claims through three
constructions that v0.2.2 did not catch -- constructs nested inside
prep-of chains, nominal anchor nouns beyond the initial v0.2.0 set, and
copular sentences with predicate-noun anchors. v0.2.3 addresses all three.

### Added
- Helper `_construct_anywhere_below` performs a bounded-depth (max 4)
  walk DOWN the dependency tree through prep/pobj/conj/nmod arcs, so a
  construct head two or three levels deep inside a noun phrase still
  counts as connected to a governing verb. The depth bound is empirically
  chosen: depth 4 captures the long "the perception of the effect of X
  on Y" chains observed in real abstracts while remaining O(N) in practice
  because anchor sentences are short.
- Pattern F (copular nominal anchor): recognises "X is the antecedent of
  Y", "Z is a predictor of consumer loyalty", "loyalty is the outcome
  of brand authenticity". Direction follows the inherent semantics of
  the anchor noun: antecedent/precursor/predictor/driver of -> forward;
  outcome/consequence of -> backward. The lexicon
  `_COPULAR_ANCHOR_LEXICON` maps each anchor to (relation_type, direction).
  Confidence boost +0.22, slightly below pattern C (+0.25) because pattern
  F is empirically slightly less specific.

### Changed
- The relationship-anchor noun set `_REL_ANCHOR_NOUNS` is expanded from 14
  to 33 entries, adding antecedent(s), precursor(s), predictor(s),
  determinant(s), driver(s), outcome(s), consequence(s), mediator(s),
  moderator(s). These nouns continue to be stop-listed from the constructs
  frame -- a separate code path -- because they are not theoretical
  constructs. This deliberate separation of "construct stop-list" from
  "relation-pattern trigger lexicon" first appeared in v0.1.2 and is
  generalised here.
- Patterns B, C, D, and E now use `_construct_anywhere_below` rather than
  the strict `_is_within_or_descendant` to test whether a construct sits
  in a subject or object role. Pattern A retains the original ancestry
  walk because its semantics require checking that a construct head is
  syntactically *governed by* the moderate/mediate trigger, not that
  the construct is downstream of an arbitrary verb argument.

### Expected behaviour
- Pattern coverage on real marketing abstracts should rise from the
  v0.2.2 floor of ~6% (6 of 94 rows) toward roughly 30-40%. The remaining
  `assoc` rows will be true co-occurrences without explicit directional
  language plus residual misses in cross-clause constructions, the latter
  being v0.3 work.

## [0.2.2] – 2026-04-18

### Fixed
- Second performance regression in `score_relations`. Trace logs from
  v0.2.1 showed the hang persisted at stage (f) scoring relationships
  even with the per-sentence Doc cache. Root cause: `_pattern_A` was
  building a fresh subtree-index set on every (pair, sentence, child)
  combination via `{c.i for c in child.subtree}`, which on long real
  abstracts blew up to billions of comparisons. The expression also had
  a broken `any()` filter, producing the iteration cost without
  delivering the intended filter semantics.
- `_is_within_or_descendant` is now bounded by document length to prevent
  any possibility of an infinite loop on a pathological dependency parse.

### Added
- Per-sentence pattern-viability flags (`_sentence_flags`). Each parsed
  sentence is now inspected once to determine whether each of the five
  patterns (A through E) could possibly match, based on the presence of
  the relevant triggers (moderate/mediate verb, valence verb, passive
  marker, anchor noun, etc.). The five pattern matchers consult the
  flags and exit immediately when the trigger is absent. On real corpora
  most sentences have zero or one viable pattern, eliminating a 4×
  overhead in stage (f).
- Progress reporting during stage (f): a percentage update is printed
  every 10% of the pair-scoring loop, so future hangs are localised to
  a specific pair index rather than appearing as an opaque stall.

### Changed
- Stage (f) wall-clock on the 33-abstract corpus should now run in
  roughly 1-5 seconds rather than the >15 minutes observed under v0.2.0
  and v0.2.1.

## [0.2.1] – 2026-04-03

### Fixed
- Performance regression in `score_relations` introduced by v0.2.0. The
  five-pattern matcher re-parsed each sentence once per construct pair it
  contributed to, turning an O(P) loop into O(P·S). On the 33-abstract
  marketing corpus this produced run times exceeding 15 minutes versus
  v0.1.3's 11 seconds; trace logging confirmed the hang was in stage (f)
  scoring candidate relationships, not in the Stata-Python bridge.

### Changed
- `score_relations` now caches parsed spaCy `Doc` objects per unique
  sentence, so each sentence is parsed exactly once regardless of how many
  construct pairs it produces.
- Two further pre-built lookup dicts replace per-row DataFrame filtering
  in the inner loop: `unit_id` → unit row, and `canonical_form` →
  `construct_id`. Together with the doc cache, expected runtime on the
  33-abstract corpus is back to roughly 12-20 seconds.

## [0.2.0] – 2026-04-02

### Added
- Five-pattern dependency-arc relation matcher in `littext_relate.py`,
  replacing the v0.1 string-position-based heuristic. Patterns, applied in
  priority order:
  - **A — Nominal moderation/mediation.** "the moderating role of X on the
    relationship between A and B"; "X mediates the effect of A on B".
    Boost +0.30. Highest precision.
  - **C — Passive constructions.** "Y is driven by X" → source=X, target=Y.
    Subject identified via `nsubjpass`, agent via the prepositional `agent`
    arc. Boost +0.25.
  - **B — Finite-verb VSO.** "X drives Y" → subject and object identified
    via `nsubj` / `dobj` / `pobj` arcs around the matched verb. Boost +0.20.
  - **E — Adjectival valence.** "a positive effect of X on Y" → valence
    read from the adjectival modifier on the relationship-anchor noun.
    Boost +0.15.
  - **D — Nominal-pattern relationships.** "the effect of X on Y",
    "the relationship between X and Y", "X is associated with Y". Boost +0.10.
- New `extraction_method` values in `lt_relations`: `cooccur+dep:A`,
  `cooccur+dep:B`, ..., `cooccur+dep:E`, allowing downstream filtering by
  pattern type and precision.
- Source/target ordering is now derived from dependency arcs rather than
  surface string position. Roughly half of v0.1's directional rows had
  source and target swapped because the heuristic used surface order; the
  v0.2 matcher reads the actual syntactic subject and object.

### Changed
- The two valence-adjective lexicons (`_POS_ADJ_LEMMAS`, `_NEG_ADJ_LEMMAS`)
  are deliberately small and high-precision. Ambiguous adjectives such as
  "significant" (which usually denotes statistical significance rather than
  valence) are excluded.

### Notes
- Confidence boosts now differ by pattern type. Patterns A and C carry the
  highest boosts (their syntactic anchors are unambiguous); pattern D
  carries the lowest because the nominal "of...on" construction occasionally
  fires on non-relational sentences.
- Expected effect on real-corpus output: the `assoc` share should fall from
  ~85% to 50-60%, and source/target direction should be correct on roughly
  80% of directional rows rather than ~50%.

## [0.1.3] – 2026-03-22

### Added
- POS-aware trigger matching in the dependency-pattern matcher
  (`littext_relate._find_dep_pattern`). Triggers for `pos_assoc`, `neg_assoc`,
  `causes`, `moderates`, and `mediates` now fire only when the matched token
  is tagged as a VERB by spaCy. This prevents two false-positive patterns
  observed on real corpora: (a) the noun "causes" in phrases like "social
  causes" being misread as the verb "causes"; (b) the participle
  "moderating" being read as the verb "moderate" when it functions
  adjectivally in noun phrases like "the moderating effect".
- Lemma-only verb sets (`_POS_VERBS_LEMMAS`, `_NEG_VERBS_LEMMAS`,
  `_CAUSE_VERBS_LEMMAS`) for matching against spaCy's `.lemma_` attribute.
  The inflected-form sets are retained for backward compatibility.

### Changed
- Stop-list extended with four additional entries (`concept`,
  `proof of concept`, `terms`, `manifold ways`) drawn from residual
  discourse-marker phrases observed in the top-of-list candidate
  relationships on real marketing corpora. The stop-list is now at
  185 entries.

### Fixed
- The relations frame no longer reports spurious `causes` rows triggered by
  noun-form occurrences of "causes" (e.g. "social causes", "common causes").
- The relations frame no longer reports `moderates` rows triggered by
  adjectival "moderating" inside noun-phrases like "the moderating effect".

## [0.1.2] – 2026-03-20

### Changed
- Stop-list extended with methodological-discourse vocabulary that v0.1.1 had
  left in place as canonical constructs: `mediating role`, `moderating effect`,
  `mediating effect`, `moderating role`, `antecedents`, `consequences`,
  `antecedent`, `consequence`, `present study`. These phrases continue to
  function as triggers for the dependency-pattern matcher in
  `littext_relate.py`; they are excluded only from the constructs frame.

### Fixed
- Top-of-list candidate relationships no longer feature methodological-role
  phrases as endpoints (e.g. spurious "antecedents → mediating role" rows
  that v0.1.1 was producing at confidence > 0.95).

## [0.1.1] – 2026-03-11

### Added
- Pre-extraction text cleanup: Emerald-style structured-abstract section
  headers (*Purpose:*, *Findings:*, *Originality/value:*, etc.) and publisher
  copyright trailers (Elsevier, Emerald, Taylor & Francis, Wiley, Springer,
  SAGE) are stripped before construct extraction.
- Within-cluster similarity floor (`SIMILARITY_FLOOR = 0.65`) splits any
  HDBSCAN cluster whose minimum pairwise cosine similarity falls below the
  threshold. Rejects the failure mode in which semantically-related but
  distinct constructs (*brand equity*, *brand trust*, *service quality*,
  *consumers*) were pooled into a single mega-cluster.
- `outdir()` option on `littext graph` accepts an absolute path so figure
  output locations are predictable. Defaults to `c(pwd)` when omitted; the
  resolved absolute path is always printed.

### Changed
- Stop-list expanded from 36 to 172 entries, adding generic academic
  discourse vocabulary, methodological terms (`structural equation modeling`,
  `ANOVA`, `MTurk`, etc.), and publisher fragments (`Elsevier B.V.`,
  `Emerald Publishing Limited`, `Taylor & Francis`, etc.).
- HDBSCAN `min_cluster_size` fixed at 2 (was previously scaling with corpus
  size, producing over-merged mega-clusters on small corpora).
- SMCL help-file lines now respect Stata's ~120-byte line-length convention
  to avoid truncation or mis-wrapping in narrow Results windows.

### Fixed
- UMAP `UserWarning: n_jobs value 1 overridden to 1 by setting random_state`
  is suppressed at the call site (it was harmless but cluttered output).

## [0.1.0] – 2026-02-18

### Added
- Initial release.
- `littext analyze`: extracts candidate constructs and relationships from
  an unstructured corpus. Output: three Stata frames (`lt_constructs`,
  `lt_relations`, `lt_diag`) left in memory.
- `littext graph`: seven figure types — `frequency`, `distribution`,
  `trend`, `confidence` (Stata-native), and `map`, `network`, `dendrogram`
  (matplotlib). PNG and PDF saved to the working directory.
- `littext example`: loads either the bundled 30-abstract test corpus
  (`n(30)`, default) or the 200-abstract demonstration corpus (`n(200)`),
  with optional ground-truth relations via `gold`.
- `littext install`: verifies the Python environment (quiet check uses
  `importlib.util.find_spec` for sub-millisecond startup; verbose imports
  each package to read its version).
- `litt`: short alias for `littext`.
- Six-element controlled relation-type vocabulary: `pos_assoc`, `neg_assoc`,
  `moderates`, `mediates`, `causes`, `assoc`.
- Pipeline: spaCy `en_core_web_sm` noun-chunk extraction →
  sentence-transformers `all-MiniLM-L6-v2` embeddings → HDBSCAN synonym
  clustering → normalised PMI co-occurrence scoring →
  dependency-pattern matcher for relationship valence.
- Synthetic example corpora bundled with the package.
- End-to-end smoke test do-file under `tests/`.

[Unreleased]: https://github.com/Davcik/littext/compare/v0.2.9...HEAD

