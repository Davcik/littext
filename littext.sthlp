{smcl}
{* *! version 0.1.0  17may2026}{...}
{title:Title}

{phang}
{bf:littext} {hline 2} Automated construct discovery and relationship
inference from academic text

{pstd}
The short alias {bf:litt} is provided for interactive use; the two commands
are functionally identical.

{title:Syntax}

{p 8 16 2}
{bf:littext analyze} {cmd:,} {opt t:ext(varname)} [ {it:options} ]

{p 8 16 2}
{bf:littext graph} {cmd:,} [ {opt t:ype(string)} {opt top(#)}
{opt out:dir(string)} {opt we:ighted} {opt sav:ing(string)} {opt rep:lace} ]

{p 8 16 2}
{bf:littext example} [ {cmd:,} {opt n(#)} {opt gold} {opt clear} ]

{p 8 16 2}
{bf:littext install} [ {cmd:,} {opt q:uiet} {opt v:erbose} ]

{title:Description}

{pstd}
{bf:littext} extracts candidate construct relationships from an unstructured
corpus of academic text (titles, abstracts, full texts). It is intended for
the exploratory researcher who has assembled a large corpus and wants to
generate candidate relationships of the form "X is associated with Y",
"X moderates the effect of Z on Y", etc., that can then be hand-curated into
a formal systematic-literature-review coding scheme.

{pstd}
The pipeline is: spaCy noun-chunk extraction; sentence-transformer embedding
of candidate constructs; HDBSCAN clustering into synonym groups; co-occurrence-
based relation candidacy with normalised PMI scoring; dependency-pattern
matching for relationship valence.

{pstd}
Results are returned in three Stata frames left in memory:

{p 8 12 2}{bf:lt_constructs}  -  one row per extracted construct{p_end}
{p 8 12 2}{bf:lt_relations}   -  one row per candidate relationship{p_end}
{p 8 12 2}{bf:lt_diag}        -  one row per source document with diagnostics{p_end}

{pstd}
After {bf:littext analyze} returns, you are placed in frame {bf:lt_relations}.
Files on disk are produced only if you pass {opt sav:ing()}.

{title:Options for {cmd:littext analyze}}

{phang}
{opt t:ext(varname)} (required) - the variable in the current dataset that
holds the document text. May be a {bf:str#} or {bf:strL} variable.

{phang}
{opt i:d(varname)} - a per-document identifier. If omitted, {bf:_n} is used.

{phang}
{opt y:ear(varname)} - publication year (numeric). Used for the trend graph
and stored in {bf:lt_diag}.

{phang}
{opt j:ournal(varname)} - outlet name (string). Stored in {bf:lt_diag} for
comparative analysis.

{phang}
{opt u:nit(string)} - unit of analysis for relationship candidacy. One of
{bf:sentence} (default; high precision), {bf:abstract} (high recall),
{bf:paragraph}.

{phang}
{opt emb:edmodel(string)} - name of the sentence-transformers model used for
construct embeddings. Default {bf:all-MiniLM-L6-v2}. For scholarly text the
preferred alternative is {bf:allenai/specter2}.

{phang}
{opt minf:req(#)} - minimum document frequency for a candidate construct to
be retained. v0.2.6 default: {bf:1} for corpora with fewer than 50
documents (single-document constructs are kept so the relation matcher
can exercise them); {bf:2} for corpora of 50 or more documents (acts as
a noise filter). Override by passing the option explicitly; the resolved
value and its rationale are printed at run time.

{phang}
{opt maxr:elations(#)} - cap on the number of candidate relationships
written to {bf:lt_relations} (highest-confidence first). Default {bf:100000}.

{phang}
{opt addsentiment} - additionally compute VADER affective polarity on each
evidence sentence and store it in {bf:text_polarity}. Note: this is
{it:affective sentiment} of the text, NOT {it:relationship valence}.
Relationship valence is always computed and stored in {bf:relation_type}.

{phang}
{opt q:uiet} - suppress progress output.

{phang}
{opt sav:ing(string)} - if specified, the three frames are also saved as
{it:stub}_constructs.dta, {it:stub}_relations.dta, {it:stub}_diag.dta.

{phang}
{opt rep:lace} - allow overwriting existing files when {opt sav:ing()} is used.

{title:Options for {cmd:littext graph}}

{phang}
{opt t:ype(string)} - figure type. One of:

{p 8 12 2}{bf:frequency}     - bar chart of top-k constructs (Stata-native){p_end}
{p 8 12 2}{bf:distribution}  - distribution of relation types (Stata-native){p_end}
{p 8 12 2}{bf:trend}         - extraction yield over years (Stata-native){p_end}
{p 8 12 2}{bf:confidence}    - histogram of confidence scores (Stata-native){p_end}
{p 8 12 2}{bf:extraction}    - distribution by extraction method (Stata-native){p_end}
{p 8 12 2}{bf:map}           - UMAP concept map (matplotlib; default){p_end}
{p 8 12 2}{bf:network}       - relationship network (matplotlib){p_end}
{p 8 12 2}{bf:dendrogram}    - construct-cluster dendrogram (matplotlib){p_end}
{p 8 12 2}{bf:cooccurrence}  - pairwise NPMI heatmap of top-k constructs (matplotlib){p_end}
{p 8 12 2}{bf:roles}         - construct x relation-type heatmap (matplotlib){p_end}

{phang}
{opt top(#)} - number of top constructs or relationships to display.
Default {bf:20}. For heatmaps, controls the matrix dimensions.

{phang}
{opt we:ighted} - for {bf:type(network)} only: colour edges continuously by
confidence (viridis) rather than discretely by relation type. Useful when
edge strength matters more than syntactic type.

{phang}
{opt out:dir(string)} - directory where figure files will be written.
Accepts an absolute path (e.g. {bf:"D:\projects\figures"}). If omitted or
given as a relative path, the current Stata working directory ({bf:c(pwd)})
is used; the resolved absolute path is always printed so the user knows
where the files were saved.

{phang}
{opt sav:ing(string)} - output file stub for matplotlib figures (PNG and PDF
are written). For Stata-native graphs, the file is saved as PNG via
{cmd:graph export}.

{title:Stata frames produced}

{pstd}
{bf:lt_constructs}: construct_id, surface_form, canonical_form, cluster_id,
freq_doc, freq_total.

{pstd}
{bf:lt_relations}: rel_id, doc_id, unit_id, source, target,
source_construct_id, target_construct_id, relation_type, confidence,
extraction_method, evidence_text, text_polarity.

{pstd}
{bf:lt_diag}: doc_id, year, journal, n_constructs_extracted,
n_relations_extracted.

{title:relation_type vocabulary}

{phang}
{bf:pos_assoc}  - positive association (X increases/enhances/predicts Y){p_end}
{phang}
{bf:neg_assoc}  - negative association (X reduces/attenuates Y){p_end}
{phang}
{bf:moderates}  - X moderates the relationship between two others{p_end}
{phang}
{bf:mediates}   - X mediates the effect of one construct on another{p_end}
{phang}
{bf:causes}     - X causes / leads to Y{p_end}
{phang}
{bf:assoc}      - non-directional or unclassified co-occurrence{p_end}

{title:Examples}

{pstd}For fast development and smoke-testing (30 abstracts; runs in seconds):{p_end}

{phang}{cmd:. littext example, clear}{p_end}
{phang}{cmd:. littext analyze, text(abstract) id(article_id) year(year) journal(journal)}{p_end}

{pstd}For the full demonstration corpus (200 abstracts):{p_end}

{phang}{cmd:. littext example, n(200) clear}{p_end}
{phang}{cmd:. littext analyze, text(abstract) id(article_id) year(year) journal(journal)}{p_end}
{phang}{cmd:. list source target relation_type confidence in 1/10}{p_end}
{phang}{cmd:. tab relation_type}{p_end}
{phang}{cmd:. littext graph, type(map)}{p_end}
{phang}{cmd:. littext graph, type(network) top(25)}{p_end}
{phang}{cmd:. littext graph, type(distribution)}{p_end}

{pstd}To inspect the ground-truth relationships embedded in a corpus:{p_end}

{phang}{cmd:. littext example, n(30) gold clear}{p_end}
{phang}{cmd:. list source target relation_type in 1/15}{p_end}

{title:Sentiment analysis: a note}

{pstd}
{bf:littext} draws a clear line between two distinct constructs that are often
conflated in marketing applications:

{phang}
1. {it:Relationship valence} is the sign of the directional relationship
between two constructs (X positively/negatively related to Y). This is always
computed and stored in {bf:relation_type}. It is essential to the purpose of
the package; a hypothesis register that cannot distinguish "X increases Y"
from "X reduces Y" is not a hypothesis register.{p_end}

{phang}
2. {it:Affective sentiment} is the emotional polarity of a piece of text, in
the sense of VADER, LIWC, or the NRC Emotion Lexicon. This is meaningful for
consumer-text corpora (reviews, tweets) but largely uninformative for academic
abstracts. {bf:littext} computes it only on request via {opt addsentiment} and
stores it in {bf:text_polarity}.{p_end}

{pstd}
Users should not treat {bf:text_polarity} as a measure of relationship sign.

{title:Requirements}

{pstd}
Stata 19 or higher with Python integration configured. Python 3.13 or 3.14
recommended on Windows; spaCy on Python 3.14 requires {bf:blis 1.3.3} or
higher. Required Python packages: spacy, sentence-transformers, hdbscan,
scikit-learn, umap-learn, matplotlib, networkx, pandas, numpy. The spaCy
model {bf:en_core_web_sm} must be downloaded once via
{cmd:python -m spacy download en_core_web_sm}.

{title:Limitations of v0.1}

{pstd}
{bf:littext} v0.1 uses noun-chunk extraction rather than a domain-trained NER
model, and co-occurrence + dependency-pattern matching rather than a trained
relation extractor. It is therefore best understood as a candidate-generation
tool whose output requires manual curation before being treated as a coding
scheme. Quantitative precision/recall figures should not be reported against
the bundled synthetic corpus.

{title:Author}

{pstd}
(Your name and affiliation)

{title:References}

{pstd}
Bouma, G. (2009). Normalized (pointwise) mutual information in collocation
extraction. {it:Proceedings of GSCL}, 31-40.

{pstd}
Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based
TF-IDF procedure. {it:arXiv:2203.05794}.

{pstd}
Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model
for sentiment analysis of social media text. {it:ICWSM}, 8(1), 216-225.

{pstd}
Li, J., Larsen, K. R., & Abbasi, A. (2020). TheoryOn: A design framework and
system for unlocking behavioral knowledge through ontology learning. {it:MIS
Quarterly}, 44(4), 1733-1772.

{pstd}
McInnes, L., Healy, J., & Astels, S. (2017). hdbscan: Hierarchical density
based clustering. {it:Journal of Open Source Software}, 2(11), 205.

{pstd}
McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold
Approximation and Projection. {it:arXiv:1802.03426}.

{pstd}
Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using
Siamese BERT-networks. {it:EMNLP-IJCNLP}, 3982-3992.
