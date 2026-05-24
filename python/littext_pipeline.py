"""littext_pipeline: top-level orchestrator called from _littext_analyze.ado.

This module wires together extraction, embedding, clustering, relation
candidacy, and writing back into Stata frames via the sfi interface.

Pre-extraction text cleanup (v0.1.1):
The pipeline strips publisher boilerplate (Emerald structured-abstract section
headers, copyright trailers from major academic publishers) before any
construct extraction. This is done in _load_corpus so the cleaning is applied
uniformly regardless of how the corpus reached the pipeline.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import pandas as pd

from littext_extract import extract_constructs
from littext_embed import embed_constructs
from littext_cluster import cluster_constructs
from littext_relate import score_relations
from littext_io import write_constructs_frame, write_relations_frame, write_diag_frame
from littext_state import save_state


# Emerald-style structured-abstract section headers. These prefix substantive
# sentences but should be removed before parsing so the parser does not treat
# "Findings" as a noun chunk or as the subject of the following clause.
_EMERALD_SECTIONS = re.compile(
    r"\b(Purpose|Design/methodology/approach|Methodology|Methodology/approach|"
    r"Findings|Originality/value|Originality|Research limitations/implications|"
    r"Research limitations|Practical implications|Social implications|"
    r"Theoretical implications|Managerial implications|Implications|"
    r"Limitations|Conclusion|Conclusions|Contribution|Background|Aim|Aims|"
    r"Objective|Objectives|Approach|Results|Discussion)"
    r"\s*[:\-\u2013\u2014]\s*",
    flags=re.IGNORECASE,
)

# Copyright trailers: everything from a copyright symbol or a "Published by"
# / "All rights reserved" marker through end-of-string is stripped. We match
# from the first such marker to the end so multi-publisher trailers (e.g.
# "(c) 2019 Informa UK Ltd, trading as Taylor & Francis Group") are removed
# wholesale.
_COPYRIGHT_TAIL = re.compile(
    r"(?:\u00a9|\(c\)|Copyright\s|All rights reserved|"
    r"Published by\b|Elsevier B\.V\.|Elsevier Ltd\.?|Emerald Publishing|"
    r"Informa UK|Taylor\s*&\s*Francis|Wiley[- ]Blackwell|Springer Nature|"
    r"SAGE Publications).*$",
    flags=re.IGNORECASE | re.DOTALL,
)


def _clean_text(s: str) -> str:
    """Strip Emerald section labels and publisher copyright tails from one
    document's text. Idempotent and safe on text that contains neither."""
    if not isinstance(s, str) or not s:
        return ""
    s = _COPYRIGHT_TAIL.sub("", s)
    s = _EMERALD_SECTIONS.sub("", s)
    # Collapse whitespace runs left by the substitutions
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _load_corpus(corpus_path: str) -> pd.DataFrame:
    """Load the temp .dta written by _littext_analyze.ado and apply
    pre-extraction text cleanup (publisher boilerplate, copyright tails)."""
    df = pd.read_stata(corpus_path, convert_categoricals=False, convert_missing=False)
    n = len(df)
    if "lt_id" not in df.columns:
        df["lt_id"] = [f"D{i+1:06d}" for i in range(n)]
    df["lt_id"] = df["lt_id"].astype(str)
    if "lt_text" not in df.columns:
        df["lt_text"] = [""] * n
    df["lt_text"] = df["lt_text"].fillna("").astype(str).map(_clean_text)
    if "lt_journal" not in df.columns:
        df["lt_journal"] = [""] * n
    df["lt_journal"] = df["lt_journal"].fillna("").astype(str)
    if "lt_year" in df.columns:
        df["lt_year"] = pd.to_numeric(df["lt_year"], errors="coerce")
    else:
        df["lt_year"] = pd.Series([pd.NA] * n, dtype="Int64")
    return df


def run_pipeline(
    corpus_path: str,
    unit: str = "sentence",
    embed_model: str = "all-MiniLM-L6-v2",
    min_freq: int = 2,
    max_relations: int = 100_000,
    add_sentiment: bool = False,
    quiet: bool = False,
) -> None:
    """End-to-end pipeline.

    See module docstring for parameter semantics.
    """
    import sys as _sys
    import time as _time

    def log(msg: str) -> None:
        # Always flush so messages appear in Stata's window as they happen
        print(f"  littext: {msg}", flush=True)
        try:
            _sys.stdout.flush()
        except Exception:
            pass

    t0 = _time.time()
    log("(a) loading corpus from temp .dta...")
    corpus = _load_corpus(corpus_path)
    log(f"    -> {len(corpus)} documents loaded  ({_time.time()-t0:.1f}s)")

    t1 = _time.time()
    log("(b) loading spaCy en_core_web_sm (first call may take ~5-15s)...")
    # Trigger spaCy import explicitly so the user sees the pause
    import spacy as _spacy
    _ = _spacy.load("en_core_web_sm", disable=["ner"])
    log(f"    -> spaCy loaded ({_time.time()-t1:.1f}s)")

    t2 = _time.time()
    log("(c) segmenting and extracting candidate constructs...")
    constructs_df, units_df = extract_constructs(corpus, unit=unit, min_freq=min_freq)
    log(f"    -> {len(constructs_df)} candidate constructs in {len(units_df)} units  ({_time.time()-t2:.1f}s)")

    t3 = _time.time()
    log(f"(d) loading sentence-transformer model '{embed_model}' (first call downloads ~90MB if not cached)...")
    construct_embeddings = embed_constructs(constructs_df["surface_form"].tolist(), model_name=embed_model)
    log(f"    -> embeddings shape {construct_embeddings.shape}  ({_time.time()-t3:.1f}s)")

    t4 = _time.time()
    log("(e) clustering constructs with HDBSCAN...")
    constructs_df = cluster_constructs(constructs_df, construct_embeddings)
    n_canon = constructs_df["canonical_form"].nunique()
    log(f"    -> {n_canon} canonical clusters  ({_time.time()-t4:.1f}s)")

    t5 = _time.time()
    log("(f) scoring candidate relationships...")
    relations_df = score_relations(
        units_df=units_df,
        constructs_df=constructs_df,
        max_relations=max_relations,
        add_sentiment=add_sentiment,
    )
    log(f"    -> {len(relations_df)} candidate relationships  ({_time.time()-t5:.1f}s)")

    t6 = _time.time()
    log("(g) building diagnostics and writing Stata frames...")
    diag_df = _build_diagnostics(corpus, units_df, constructs_df, relations_df)
    write_constructs_frame(constructs_df)
    write_relations_frame(relations_df)
    write_diag_frame(diag_df)
    log(f"    -> frames populated  ({_time.time()-t6:.1f}s)")

    save_state(
        constructs_df=constructs_df,
        construct_embeddings=construct_embeddings,
        relations_df=relations_df,
        diag_df=diag_df,
    )
    log(f"done. total {_time.time()-t0:.1f}s")


def _build_diagnostics(corpus, units_df, constructs_df, relations_df):
    """Per-document diagnostic counts."""
    # Constructs per doc
    cpd = units_df.merge(
        constructs_df[["construct_id"]].drop_duplicates(),
        on="construct_id",
        how="inner",
    )
    n_con = cpd.groupby("doc_id")["construct_id"].nunique().rename("n_constructs_extracted")
    n_rel = relations_df.groupby("doc_id").size().rename("n_relations_extracted")
    out = corpus[["lt_id", "lt_year", "lt_journal"]].rename(columns={"lt_id": "doc_id", "lt_year": "year", "lt_journal": "journal"})
    out = out.merge(n_con, left_on="doc_id", right_index=True, how="left")
    out = out.merge(n_rel, left_on="doc_id", right_index=True, how="left")
    out[["n_constructs_extracted", "n_relations_extracted"]] = (
        out[["n_constructs_extracted", "n_relations_extracted"]].fillna(0).astype(int)
    )
    return out
