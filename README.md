# littext

**Automated construct discovery and relationship inference from academic text, for Stata**

`littext` is a Stata package that extracts candidate construct relationships
from a corpus of text (titles, abstracts, full texts). Its intended
user is the scholar who has assembled an unstructured
corpus and wants to generate candidate relationships of the form
"X is associated with Y", "X moderates the effect of Z on Y", etc., that can
later be hand-curated into a formal systematic literature review coding
scheme.

`litdiscover` is a sister package supporting systematic literature reviews
from researcher-curated corpora with manually coded constructs. `littext`
has a different purpose: automated extraction from raw academic text, without
manual coding.

---

## Installation

### 1. Python environment

`littext` requires Stata 19's Python integration. From Stata:

    python set exec "C:\path\to\python.exe"
    python query

Python 3.14 is recommended on Windows. 

Install the required Python packages into the environment Stata is bound to:

    pip install spacy sentence-transformers hdbscan scikit-learn umap-learn matplotlib networkx plotly pandas numpy vaderSentiment
    python -m spacy download en_core_web_sm

`vaderSentiment` is required only for the optional `addsentiment` option;
the rest are mandatory.

### 2. Stata package

**Development / local use.** Place the package directory anywhere on the
filesystem and add the directory that contains the `.ado` files to Stata's
adopath:

    adopath + "D:\path\to\littext"

**End-user installation from GitHub:**

    net from "https://raw.githubusercontent.com/Davcik/littext/main/"
    net describe littext
    net install littext

**End-user installation from GitHub — single-archive fallback.**
On some managed or institutional networks, a TLS-inspecting firewall or
security proxy resets connections during the rapid sequence of per-file
requests that `net install` issues from a raw GitHub source. The symptom
is an intermittent `r(603)` ("could not copy ...") that lands on a
*different* file on each attempt, even though every file is present and
individually reachable. The package is not at fault in this case; the
network link is dropping one request out of the burst. When this occurs,
retrieve the entire package in a single request and install from the
extracted folder:

1. Download the repository archive (a single request) and save it locally:
   `https://github.com/Davcik/littext/archive/refs/heads/main.zip`
2. Extract it. This yields a folder `littext-main` containing `stata.toc`,
   `littext.pkg`, and the complete package tree.
3. Install from that folder:

       net from "C:\path\to\littext-main"
       net install littext, replace

The installed result is identical to a successful network `net install`;
only the transport differs (one archive fetch in place of roughly thirty
per-file fetches).

**End-user installation from SSC (after SSC submission):**

    ssc install littext

### 3. Verify

From Stata:

    littext install, verbose

This prints the Python version, the executable path, and the status of each
required package.

## Quick start

    use my_corpus.dta, clear
    littext analyze, text(abstract) id(article_id) year(year) journal(journal)
    frame lt_relations: list source target relation_type confidence in 1/20
    frame lt_relations: tab relation_type
    littext graph, type(map) outdir("D:/figs")
    littext graph, type(network) outdir("D:/figs")

## Output

Three Stata frames are left in memory after `littext analyze`:

- `lt_constructs`: extracted constructs with frequency and synonym-cluster info
- `lt_relations`: candidate relationships with confidence scores and evidence
- `lt_diag`: per-document diagnostics

No files are written to disk unless you pass `saving(stub)`.

To hand off the candidate relationships for manual curation, export them as a
hypothesis register (sorted strongest-first, no curation columns added):

    littext export, outdir("D:/register") format(both)
    littext export, outdir("D:/register") minconf(0.7) type(pos_assoc neg_assoc) top(200)

`format()` accepts `csv`, `xlsx`, or `both`. Filters (`minconf()`, `type()`,
`top()`) make a large candidate set reviewable; `columns()` overrides the
default essentials-plus-provenance column set.

## Visualisations

Ten figure types are available via `littext graph, type(...)`:

| Type | Renderer | Output |
|---|---|---|
| `frequency`     | Stata-native | top-k constructs by document frequency |
| `distribution`  | Stata-native | distribution of relation types |
| `trend`         | Stata-native | extraction yield over years |
| `confidence`    | Stata-native | histogram of confidence scores |
| `extraction`    | Stata-native | distribution by extraction method |
| `map`           | matplotlib   | UMAP concept map of constructs |
| `network`       | matplotlib   | force-directed relationship network |
| `dendrogram`    | matplotlib   | hierarchical construct clustering |
| `cooccurrence`  | matplotlib   | pairwise NPMI heatmap of top-k constructs |
| `roles`         | matplotlib   | construct x relation-type heatmap |

The five matplotlib types also render as interactive Plotly HTML via
`format(html)` (or `format(both)` for static + interactive). Interactive
figures support hover, zoom, and pan, and by default are self-contained
(open offline in any browser); pass `embed(cdn)` for small CDN-linked
files. Example: `littext graph, type(network) outdir("D:/figs") format(html)`.

## File layout

    littext/
    ├── littext.ado                Master dispatcher
    ├── litt.ado                   Short-form alias
    ├── littext.sthlp              Help file
    ├── litt.sthlp                 Alias help (copy of littext.sthlp)
    ├── _littext_install.ado       Python-environment check / installer
    ├── _littext_analyze.ado       Main analysis driver
    ├── _littext_graph.ado 	   Visualization dispatcher
    ├── _littext_export.ado        Hypothesis-register export
    ├── _littext_example.ado       Example-data loader
    ├── littext.pkg                net install manifest
    ├── stata.toc                  net install table of contents
    ├── LICENSE                    GPL-3.0-or-later
    ├── README.md
    ├── CHANGELOG.md
    ├── CITATION.cff
    ├── python/                    Python pipeline (force-installed)
    │   ├── __init__.py
    │   ├── littext_env.py         Environment helpers (inferred from name)
    │   ├── littext_run.py         Pipeline entry point (inferred from name)
    │   ├── littext_pipeline.py    Orchestration
    │   ├── littext_extract.py     spaCy noun-chunk construct extraction
    │   ├── littext_embed.py       Sentence-transformer embeddings
    │   ├── littext_cluster.py     HDBSCAN synonym clustering
    │   ├── littext_hierarchy.py   Construct-hierarchy detection
    │   ├── littext_cleaners.py    texttype() cleaning regimes
    │   ├── littext_relate.py      Co-occurrence + dependency-pattern relations
    │   ├── littext_io.py          Stata-frame I/O
    │   ├── littext_state.py       Run-state helpers (inferred from name)
    │   └── littext_viz.py         matplotlib figures
    ├── data/                      		Synthetic corpus
    │   ├── littext_example.dta         	300 abstracts (loaded by littext example)
    │   └── littext_rbv_synth_v01_README.md     schema and provenance
    └── usecases/                  		Worked research workflows
        └── USECASES.md                 	narrative walkthrough of seven workflows

## Synthetic corpus

The `data/` directory contains a synthetic corpus themed on the
resource-based view of the firm: 300 abstracts in `littext_example.dta`
(see `data/littext_rbv_synth_v01_README.md` for the schema and
provenance). The corpus is **synthetic** and must not be cited as a real
bibliometric resource; its purpose is end-to-end testing, example
illustration, and submission demonstration.

The bundled example is wired to `littext_example.dta` (300 abstracts).
Load and analyze it with:

    littext example, clear
    littext analyze, text(abstract) id(article_id) year(year) journal(journal)

The relation types the extractor can emit are `pos_assoc`, `neg_assoc`,
`moderates`, `mediates`, `causes`, and `assoc`.

## Methodological notes

`littext` uses noun-chunk extraction (via spaCy `en_core_web_sm`),
sentence-transformer embeddings (default `all-MiniLM-L6-v2`; the
`allenai/specter2` model is preferable for scholarly text), HDBSCAN synonym
clustering, normalized pointwise mutual information for the relationship
candidacy, and a small dependency-pattern lexicon for relationship valence.

The package distinguishes between **relationship valence** (positive,
negative, moderating, mediating, causal; always computed; stored in
`relation_type`) and **affective sentiment** (VADER polarity of the evidence
text; optional via `addsentiment`; stored in `text_polarity`). These are
different constructs; do not treat the second as a measure of the first.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history. The current
release is **v1.0.0**.

---

## Citation

When citing `littext` in academic work, please use:

> Davcik, N. S. 2026. *LITTEXT: Stata module for automated construct discovery and relationship inference from academic text.*
> Available at:
> [https://github.com/Davcik/littext](https://github.com/Davcik/littext)

A [CITATION.cff](CITATION.cff) file is provided in the repository
root for GitHub's "Cite this repository" feature and for ingestion
by reference managers such as Zotero, Mendeley, and JabRef.

---

## License

`littext` is released under the
[GNU General Public License version 3 or later](https://www.gnu.org/licenses/gpl-3.0.html)
(GPL-3.0-or-later). You may redistribute and modify it under the
terms of that license; modified versions and larger works that
incorporate `littext` must also be released under GPL-3 or
later. See [LICENSE](LICENSE) for the full text.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

---

## Author

**Nebojsa S. Davcik**
EM Normandie Business School, Oxford, UK
ORCID: [0000-0003-1041-8788](https://orcid.org/0000-0003-1041-8788)
Email: davcik {@} live.com
