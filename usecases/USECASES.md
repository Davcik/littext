# littext: Seven Research Workflows

**A use-cases document for the `littext` Stata package**
Nebojsa S. Davcik · EM Normandie Business School

---

## Preliminaries

`littext` performs automated construct discovery and relationship inference
from corpora of academic text. A single `littext analyze` call reads a
frame of documents, extracts theoretical constructs as normalised
noun-chunks, clusters synonymous surface forms via sentence-transformer
embeddings and HDBSCAN, infers a lexical IS-A hierarchy over the resulting
canonical constructs, and scores candidate inter-construct relationships
using a six-pattern dependency-arc matcher together with a normalised
point-wise-mutual-information co-occurrence baseline. The results are
returned in three Stata frames — `lt_constructs`, `lt_relations`, and
`lt_diag` — which subsequent commands (`littext graph`, `littext export`)
consume.

This document presents seven research workflows the package supports. Each
is stated as a research question, followed by the Stata script that
addresses it and an interpretation of the output. The scripts are also
provided as standalone, runnable `.do` files (`uc1`–`uc7`), each preceded
by the shared `uc0_setup.do`.

### A standing caveat on the data

Every workflow below runs on the corpus bundled with the package: 300
synthetic abstracts constructed to embed known resource-based-view (RBV)
constructs and relationships. This corpus makes the document fully
reproducible — any reader can execute every script and obtain the figures
and tables discussed — but it is not a real bibliometric sample. Its
apparent "findings" illustrate what the workflow yields; they are not
empirical claims about the management literature. Wherever a workflow
would, on real data, license a substantive inference, the interpretation
states the conditions under which that inference would hold. The seventh
workflow (cross-domain comparison) is the most constrained by the
synthetic corpus and is presented explicitly as an illustrative workflow
rather than a worked finding.

### Setup (run once)

```stata
global LITTEXT_DIR "D:/YOUR_FOLDER/YOUR_FOLDER/littext"
global UC_OUT      "D:/YOUR_FOLDER/YOUR_FOLDER/littext/littext_usecases_out"

adopath ++ "$LITTEXT_DIR"
capture mkdir "$UC_OUT"

littext example, clear
littext analyze, text(abstract) id(article_id) year(year) journal(journal) texttype(abstract)
```

On the bundled corpus this yields, in round terms, on the order of seven
hundred canonical constructs and several thousand candidate relationships;
the exact counts vary slightly between runs because the embedding and
HDBSCAN stages are not fully deterministic. After `analyze` the active
frame is unchanged (the corpus); results are read from the named frames
with a frame prefix.

---

## Workflow 1 — Construct landscape mapping

**Research question.** Which theoretical constructs dominate a body of
literature, and how is the construct vocabulary distributed across the
corpus?

**Script.**

```stata
littext graph, type(frequency) top(25) outdir("$UC_OUT") saving(uc1_frequency)
littext graph, type(map) top(40) outdir("$UC_OUT") format(both)

frame lt_constructs: gsort -freq_doc
frame lt_constructs: list canonical_form freq_doc freq_total cluster_id in 1/25, noobs
frame lt_constructs: count
```

**Interpretation.** The frequency ranking answers the question directly:
it identifies the constructs that recur across the largest number of
documents, which is the first thing a reviewer assembling a synthesis
wants to know. The distinction between `freq_doc` (documents in which a
construct appears) and `freq_total` (total mentions) matters
analytically — a construct with high total frequency but low document
frequency is concentrated in a few intensive treatments, whereas one with
high document frequency is diffuse across the field; the two profiles
imply different roles in a literature. The concept map situates the
constructs in a two-dimensional projection of their embedding space, so
that lexically distinct but semantically proximate constructs appear near
one another; its interactive (HTML) form is the more useful of the two
outputs here, because hovering resolves the labels that overlap illegibly
in a dense static scatter. The count of distinct canonical forms is a
summary measure of vocabulary breadth: read against the raw number of
extracted noun-chunks, it indexes how much synonymy the clustering stage
absorbed. On real data this workflow is the natural opening description of
a field; on the synthetic corpus it should be read as a demonstration of
that description rather than as a map of the actual RBV literature.

## Workflow 2 — Relationship discovery and hypothesis-register generation

**Research question.** What candidate relationships between constructs does
the corpus assert, at what confidence, and how can they be handed to a
human coder as a curatable hypothesis register?

**Script.**

```stata
frame lt_relations: count
frame lt_relations: gsort -confidence
frame lt_relations: list source target relation_type confidence in 1/15, noobs

littext export, outdir("$UC_OUT") name(uc2_register_full) format(both)
littext export, outdir("$UC_OUT") name(uc2_register_triage) format(csv) minconf(0.7) type(pos_assoc neg_assoc) top(150)
littext export, outdir("$UC_OUT") name(uc2_register_modmed) format(csv) type(moderates mediates)
```

**Interpretation.** This is the workflow for which `littext` was designed:
it converts an unstructured corpus into a structured register of candidate
relationships that a researcher can curate into a formal coding scheme.
The full export is exhaustive and therefore unwieldy; the value of the
command lies in the filtered registers. The triage register — directional
associations only, confidence at or above 0.7, capped at the 150 strongest
— is the set a coder would review first, ordered so that the most strongly
evidenced candidates appear at the top. The moderation/mediation register
isolates the contingency and mechanism claims, which are of particular
interest because they correspond to the hypotheses that most often
structure a theoretical contribution. Two cautions govern interpretation.
First, `confidence` is the extractor's internal score, reflecting pattern
strength and co-occurrence; it is not a probability that the relationship
is true, and a curator must still adjudicate each candidate against the
source text, for which the exported `evidence_text` column is provided.
Second, the register is a generative aid: its purpose is recall (surfacing
candidates a manual reader might miss), not precision, and it should be
used to widen the hypothesis space before narrowing it, not as a substitute
for the narrowing.

---

## Workflow 3 — Construct-hierarchy analysis

**Research question.** How do specific sub-constructs nest under broader
parent constructs, and how does the relationship picture change when the
corpus is read at the parent level rather than at maximum lexical
specificity?

**Script.**

```stata
frame lt_constructs: count if is_root == 0
frame lt_constructs: list canonical_form parent_canonical canonical_root hierarchy_depth if is_root == 0 in 1/25, noobs

littext graph, type(network) top(30) level(leaf) outdir("$UC_OUT") saving(uc3_network_leaf) format(both)
littext graph, type(network) top(30) level(root) outdir("$UC_OUT") saving(uc3_network_root) format(both)
littext graph, type(map) top(40) level(1) outdir("$UC_OUT") saving(uc3_map_level1)
```

**Interpretation.** The hierarchy columns encode an IS-A relation inferred
lexically: a construct whose canonical form is a right-substring of, or a
hyphenated specialisation of, another is treated as that other's subtype.
Listing the non-root constructs with their parents exposes this structure
for inspection — it is the first thing to audit, because a spurious parent
assignment will propagate into the rolled-up figures. The pair of network
figures is the analytical core of the workflow: the leaf-level network
shows every construct as its own node, while the root-level network
collapses each subtype into its parent and re-aggregates the edges. The
edge aggregation is deliberate and worth understanding: parallel edges
between a rolled pair are summed *within* a relation type but never merged
*across* types, so a positive and a negative association between the same
parent pair remain two distinct edges rather than cancelling or conflating.
Comparing the two networks answers the research question directly — it
shows which relationships are properties of specific subtypes and which
survive aggregation to the parent level. The magnitude of the change is
itself informative: a corpus rich in lexical specialisations will show a
pronounced simplification at the root level, whereas a flat vocabulary will
change little, and that is a fact about the field's terminological
structure rather than a limitation of the method. For a scholar whose work
concerns a construct family with well-developed subtypes, this is the
workflow that distinguishes claims about the family from claims about its
members.

## Workflow 4 — Antecedent and consequent role structure

**Research question.** Which constructs act predominantly as drivers,
which as outcomes, and which appear as moderators or mediators — that is,
what is each construct's typical role in the field's nomological network?

**Script.**

```stata
littext graph, type(roles) top(25) outdir("$UC_OUT") format(both)

capture frame drop _uc4
frame copy lt_relations _uc4
frame _uc4: contract source relation_type, freq(n_as_source)
frame _uc4: gsort -n_as_source
frame _uc4: list source relation_type n_as_source in 1/20, noobs
frame drop _uc4

frame copy lt_relations _uc4
frame _uc4: contract target relation_type, freq(n_as_target)
frame _uc4: gsort -n_as_target
frame _uc4: list target relation_type n_as_target in 1/20, noobs
frame drop _uc4
```

**Interpretation.** The role heatmap cross-tabulates constructs against
relation types, distinguishing the part each construct plays from the mere
frequency with which it appears. A construct that is overwhelmingly a
source of positive associations reads as a putative antecedent in the
field's theories; one that is predominantly a target reads as an outcome;
one concentrated in the moderation column functions as a boundary
condition. The two supplementary tabulations reconstruct the heatmap's
underlying counts on the source and target sides separately, so the figure
can be read against exact numbers — necessary because a heatmap communicates
pattern but not precise magnitude. The analytical payoff is a first,
data-driven sketch of the nomological structure of a literature: which
constructs the field treats as causes, which as effects, and which as
contingencies. The interpretive caution is that these roles are assigned by
the directionality the extractor recovered from sentence syntax, which is
reliable for simple constructions and progressively less so for the long
coordinated sentences characteristic of dense theoretical prose; a
construct's apparent role should therefore be corroborated against the
evidence spans before it is reported.

---

## Workflow 5 — Relationship-type composition

**Research question.** What is the balance of positive, negative,
moderating, and mediating relationships asserted in a field, and what might
that composition indicate about the field's theoretical development?

**Script.**

```stata
frame lt_relations: tab relation_type
littext graph, type(distribution) outdir("$UC_OUT") saving(uc5_distribution)
frame lt_relations: tabstat confidence, by(relation_type) statistics(n mean sd min max) columns(statistics)
littext graph, type(confidence) outdir("$UC_OUT") saving(uc5_confidence)
```

**Interpretation.** The tabulation and distribution figure together
characterise the relational composition of the corpus. The composition is
substantively suggestive: a literature dominated by simple positive
associations, with few moderation or mediation claims, looks
developmentally different from one with a substantial share of contingency
and mechanism claims — the former resembling an earlier, descriptive phase
and the latter a more mature, conditional-theorising phase. The
per-type confidence summary refines this reading by showing not only how
many relationships of each type were found but how strongly each type is
evidenced: a category that is numerous but uniformly low-confidence
warrants more curation scrutiny than one that is sparse but strong. Two
qualifications are essential. First, the observed mix reflects the
extractor's pattern coverage as much as the field's content — moderation
and mediation are recovered by syntactic patterns that fire less reliably
than the simple-association patterns, so a low moderation share is
partly a measurement artefact and not solely a property of the literature.
Second, "theoretical maturity" is an interpretive frame, not a quantity the
composition measures; the figure is a prompt for that inquiry, not a verdict
on it. On the synthetic corpus the composition is a property of the
generation process and carries no disciplinary meaning.

## Workflow 6 — Co-occurrence and thematic structure

**Research question.** Which constructs cluster together thematically —
co-occurring within the same documents more than chance would predict —
even when the corpus asserts no explicit directed relationship between
them?

**Script.**

```stata
littext graph, type(cooccurrence) top(20) outdir("$UC_OUT") format(both)

capture frame drop _uc6
frame copy lt_constructs _uc6
frame _uc6: gsort -freq_doc
frame _uc6: list canonical_form freq_doc in 1/20, noobs
frame drop _uc6
```

**Interpretation.** Where the network workflow (3) and the role workflow
(4) concern *asserted, directed* relationships, this workflow concerns
*undirected association* — the tendency of constructs to appear together
irrespective of whether the text states a relationship between them. The
heatmap is built on normalised point-wise mutual information, which
corrects raw co-occurrence for the base rates of the individual
constructs, so that a high cell reflects genuine thematic affinity rather
than the mere prominence of two frequent terms. This surfaces latent
thematic structure: clusters of constructs that travel together in the
literature and may constitute an implicit research stream even absent an
explicit theoretical link. The interactive form is materially better here
than the static one, because a co-occurrence matrix is dense and the exact
pair values are legible only on hover. Analytically, the co-occurrence
view complements the relationship view: a pair that co-occurs strongly but
has no asserted relationship is a candidate gap — two constructs the field
discusses together but has not yet theorised a link between — which is
precisely the kind of opening a contribution can exploit.

---

## Workflow 7 — Temporal and cross-segment comparison (illustrative)

**Research question.** How does the extraction profile — constructs and
relationships per document — differ across publication years and across
journals; and, by extension, how would one compare the construct and
relationship profiles of two different research domains?

**A necessary caveat, stated before the script.** The bundled corpus is
synthetic and single-domain (resource-based view). A genuine *cross-domain*
comparison cannot be demonstrated on it. The year and journal cuts below
are *within* one synthetic domain; they exist to show the *mechanics* of a
comparative analysis, not to support any substantive comparative claim. The
script's final block sketches, in comments, how the identical workflow
extends to two real corpora.

**Script.**

```stata
littext graph, type(trend) outdir("$UC_OUT") saving(uc7_trend)

capture frame drop _uc7
frame copy lt_diag _uc7
frame _uc7: gen byte one = 1
frame _uc7: collapse (mean) mean_con=n_constructs_extracted mean_rel=n_relations_extracted (count) n_docs=one, by(year)
frame _uc7: list year n_docs mean_con mean_rel, noobs
frame drop _uc7

frame copy lt_diag _uc7
frame _uc7: gen byte one = 1
frame _uc7: collapse (mean) mean_con=n_constructs_extracted mean_rel=n_relations_extracted (count) n_docs=one, by(journal)
frame _uc7: gsort -n_docs
frame _uc7: list journal n_docs mean_con mean_rel in 1/15, noobs
frame drop _uc7
```

**Interpretation.** The `lt_diag` frame records, per document, the year,
the journal, and the number of constructs and relationships extracted; it
is therefore the natural basis for any segmented comparison. The trend
figure and the by-year collapse show how extraction yield moves over time,
and the by-journal collapse shows how it varies across outlets. On real
data these cuts are genuinely informative: a rising construct-per-document
yield over time can index a field's increasing conceptual density, and
systematic between-journal differences can reflect editorial scope or
abstract-writing conventions. On the synthetic corpus, however, year and
journal are generated attributes with no such meaning, so the numbers here
demonstrate only that the segmentation runs and produces sensible tables.

The genuine *cross-domain* application — comparing, say, a marketing
corpus with a strategy corpus — follows the same logic but requires two
real corpora analysed separately. The procedure is two `analyze` runs into
separate output sets, each exported and its construct table saved, followed
by an offline comparison of the two vocabularies (shared versus
domain-specific constructs) and their relation-type mixes. The
accompanying `uc7_cross_segment.do` gives this as commented, non-executed
code. A native cross-corpus comparison command — taking two saved
construct/relation sets and reporting their overlap and divergence — is a
natural candidate for a future release of the package; at present the
comparison is assembled by the analyst from the per-corpus outputs.

---

## Closing note

These seven workflows are not independent analyses to be run in isolation
but stages of a single research process: mapping the construct landscape
(1), discovering and registering candidate relationships (2), resolving
them across the construct hierarchy (3), characterising construct roles (4)
and relational composition (5), surfacing latent thematic structure (6),
and comparing across segments or, on real data, across domains (7).
Executed in sequence on a real corpus, they take a researcher from an
unstructured body of text to a curated, structured hypothesis register and
a set of figures suitable for the descriptive section of a systematic
review or a methods paper. Executed on the bundled synthetic corpus, as
here, they reproduce the entire workflow end to end and document precisely
what each command contributes — which is the purpose of this document.
