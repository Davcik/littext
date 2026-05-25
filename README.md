# littext

**Automated construct discovery and relationship inference from academic text, for Stata**

`littext` is a Stata package that extracts candidate construct relationships
from a corpus of text (titles, abstracts, full texts). Its intended
user is the scholar who has assembled an unstructured
corpus and wants to generate candidate relationships of the form
"X is associated with Y", "X moderates the effect of Z on Y", etc., that can
later be hand-curated into a formal systematic-literature-review coding
scheme.

`littext` is the second of a two-package project. Its sister package,
`litdiscover`, supports systematic literature reviews from researcher-curated
corpora with manually coded constructs. `littext` has a different purpose:
automated extraction from raw academic text, without manual coding.

--- 

## Installation

### 1. Python environment

`littext` requires Stata 19's Python integration. From Stata:

    python set exec "C:\path\to\python.exe"
    python query

Python 3.13 or 3.14 is recommended on Windows. On Python 3.14, ensure your
spaCy install resolves a `blis` wheel (blis 1.3.3 or later provides cp314
wheels on PyPI).

Install the required Python packages into the environment Stata is bound to:

    pip install spacy sentence-transformers hdbscan scikit-learn umap-learn matplotlib networkx pandas vaderSentiment
    python -m spacy download en_core_web_sm

### 2. Stata package

Place the contents of this directory anywhere on the filesystem, then add it
to Stata's adopath. For development:

    adopath + "D:\YOUR_FOLDER\YOUR_FOLDER\littext"

For end-user installation (post-SSC):

    ssc install littext

### 3. Verify

From Stata:

    littext install, verbose

This will print the Python version, the executable path, and the status of each
required package.

## Quick start

    use my_corpus.dta, clear
    littext analyze, text(abstract) id(article_id) year(year) journal(journal)
    list source target relation_type confidence in 1/20
    tab relation_type
    littext graph, type(map)
    littext graph, type(network)

To try the bundled synthetic corpus instead:

    littext example, clear
    littext analyze, text(abstract) id(article_id) year(year) journal(journal)

## Output

Three Stata frames are left in memory after `littext analyze`:

- `lt_constructs`: extracted constructs with frequency and synonym-cluster info
- `lt_relations`: candidate relationships with confidence scores and evidence
- `lt_diag`: per-document diagnostics

No files are written to disk unless you pass `saving(stub)`.

## Visualisations

Seven figure types are available via `littext graph, type(...)`:

| Type | Renderer | Output |
|---|---|---|
| `frequency`     | Stata-native | top-k constructs by document frequency |
| `distribution`  | Stata-native | distribution of relation types |
| `trend`         | Stata-native | extraction yield over years |
| `confidence`    | Stata-native | histogram of confidence scores |
| `map`           | matplotlib   | UMAP concept map of constructs |
| `network`       | matplotlib   | force-directed relationship network |
| `dendrogram`    | matplotlib   | hierarchical construct clustering |

## File layout

    littext/
    ├── littext.ado                Master dispatcher
    ├── littext.sthlp              Help file
    ├── _littext_install.ado       Environment check
    ├── _littext_analyze.ado       Main analysis
    ├── _littext_graph.ado         Visualization dispatcher
    ├── _littext_example.ado       Example-data loader
    ├── python/                    Python pipeline
    │   ├── __init__.py
    │   ├── littext_env.py
    │   ├── littext_pipeline.py
    │   ├── littext_extract.py
    │   ├── littext_embed.py
    │   ├── littext_cluster.py
    │   ├── littext_relate.py
    │   ├── littext_io.py
    │   ├── littext_state.py
    │   └── littext_viz.py
    ├── data/
    │   ├── make_example.py        Synthetic-corpus generator
    │   ├── littext_example.dta    Synthetic abstracts (n = 200)
    │   └── littext_example_gold.dta  Ground-truth relations (n = 477)
    ├── tests/
    │   └── littext_smoke.do       End-to-end smoke test
    └── README.md

## Synthetic corpus

`data/littext_example.dta` contains 200 synthetic abstracts spanning 2005-2025,
six synthetic journals, and three substantive domains (digital marketing,
branding, business ethics). The abstracts embed 477 ground-truth relationships
balanced across the five directional relation types (pos_assoc, neg_assoc,
moderates, mediates, causes). The corpus is **synthetic** and must not be
cited as a real bibliometric resource. Its purpose is end-to-end testing,
example illustration in the help file, and SSC submission demonstration.

## Methodological notes

`littext` uses noun-chunk extraction (via spaCy `en_core_web_sm`),
sentence-transformer embeddings (default `all-MiniLM-L6-v2`; the
`allenai/specter2` model is preferable for scholarly text), HDBSCAN synonym
clustering, normalised pointwise mutual information for the relationship
candidacy, and a small dependency-pattern lexicon for relationship valence.

The package distinguishes between **relationship valence** (positive,
negative, moderating, mediating, causal; always computed; stored in
`relation_type`) and **affective sentiment** (VADER polarity of the evidence
text; optional via `addsentiment`; stored in `text_polarity`). These are
different constructs; do not treat the second as a measure of the first.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history. The current
release is **v0.2.9**; the v0.1.x series ran from v0.1.0 through v0.1.3.

---

## Citation

When citing `littext` in academic work, please use:

> Davcik, N. S. 2026. *LITTEXT: Stata module for automated construct and relationship discovery from research text.* 
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

