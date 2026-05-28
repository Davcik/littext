"""littext_hierarchy: detect IS-A subsumption among canonical constructs.

Synonym clustering (in littext_cluster) operates over symmetric similarity
and folds near-synonyms into a single canonical_form. IS-A subsumption is
anti-symmetric and tree-like and is therefore not recovered by clustering.
This module assigns hierarchy information to each canonical form as a
second pass over the clustering output.

Two detection rules are applied in sequence:

  Rule 1 (right-substring rule):
    Canonical form C has parent P if and only if all three hold:
      (a) P appears at the right edge of C, aligned to whole-token
          boundaries (so 'brand equity' qualifies as a parent of
          'consumer-based brand equity' but the standalone token
          'equity' does not, because 'brand equity' is the longer
          token-aligned right substring);
      (b) Both C and P appear as canonical forms in the current run;
      (c) freq_doc(P) >= freq_doc(C). A parent should be at least as
          well-attested as its subtype.
    Longest matching parent wins.

  Rule 2 (hyphenated-prefix rule):
    Any canonical form of the shape 'X-based Parent', 'X-driven Parent',
    'X-led Parent', or 'X-oriented Parent' is admitted as a child of
    Parent regardless of the freq_doc condition. The motivating case is
    the branding literature on 'financial-based brand equity': in a
    specialist corpus the subtype's document frequency may exceed the
    umbrella construct's. Rule 1 would refuse the parent assignment;
    rule 2 overrides this.

Output columns added to the constructs DataFrame:

  parent_canonical  (str)  -- canonical form of immediate IS-A parent,
                              or empty string if the construct is a root
  hierarchy_depth   (int)  -- 0 for roots, 1 for direct children, etc.
  is_root           (int)  -- 1 if construct is a root, 0 otherwise

The module exposes one public function, `assign_hierarchy`, which the
top-level pipeline (littext_pipeline.run_pipeline) calls between
cluster_constructs and score_relations.

Note on language: this module is English-specific. English noun
compounds place the syntactic and semantic head at the right edge with
modifiers stacking leftward, so the right-substring rule reflects a
structural regularity of the language. Languages with leftward
headedness (e.g. some Semitic languages) would require the mirror-image
rule. Users analysing non-English corpora should pass
disable_hierarchy=True (handled by the caller).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


# Hyphenated-prefix patterns that admit the construct as a child of the
# right-context noun phrase, irrespective of freq_doc. The match is on
# the construct's full canonical form; the captured Parent is the
# remainder after the prefix.
_HYPHEN_PREFIX_RE = re.compile(
    r"^[a-z][a-z\-]*-(based|driven|led|oriented)\s+(.+)$",
    flags=re.IGNORECASE,
)


def _normalise(s: str) -> str:
    """Lowercase and collapse internal whitespace, preserving hyphens."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _token_aligned_right_substring(parent: str, child: str) -> bool:
    """True iff parent is a right-anchored, token-aligned substring of child.

    Token alignment: parent must begin at a word boundary in child, and
    must end at the end of child. 'brand equity' is a token-aligned
    right substring of 'consumer-based brand equity'; 'equity' is also a
    token-aligned right substring, so the caller's longest-match logic
    will prefer the longer parent.
    """
    if not parent or not child or parent == child:
        return False
    if len(parent) >= len(child):
        return False
    if not child.endswith(parent):
        return False
    # Character immediately before the match must be whitespace (a token
    # boundary). Hyphens count as part of the preceding token, not as a
    # boundary: 'equity' is NOT a token-aligned right substring of
    # 'employee-equity' because there is no whitespace immediately
    # before 'equity'. This is intentional: hyphenated compounds are
    # single lexical units in marketing prose.
    boundary_char = child[len(child) - len(parent) - 1]
    return boundary_char == " "


def _detect_hyphen_prefix_parent(child: str) -> Optional[str]:
    """If child matches the hyphenated-prefix pattern, return the
    candidate parent (the substring after the prefix). Otherwise None.
    """
    m = _HYPHEN_PREFIX_RE.match(child)
    if not m:
        return None
    return m.group(2).strip()


def _build_parent_map(
    canonicals: List[str],
    doc_freq: Dict[str, int],
) -> Dict[str, str]:
    """Return a mapping child_canonical -> parent_canonical, empty when
    no parent is admitted. Both keys and values are lowercase-normalised
    canonical forms.

    Rule application order:
      1. For each candidate child, try the hyphenated-prefix rule first;
         if it returns a candidate parent that exists in `canonicals`,
         use it (this overrides the freq_doc check of rule 1).
      2. Otherwise, find the longest right-substring parent in
         `canonicals` whose freq_doc satisfies the prior.
    """
    canon_set = set(canonicals)
    # Pre-sort canonicals by descending length to support longest-match
    # in rule 1 without re-sorting per iteration.
    sorted_by_len = sorted(canonicals, key=lambda s: -len(s))

    parent_map: Dict[str, str] = {}
    for child in canonicals:
        # Rule 2 first
        hyphen_candidate = _detect_hyphen_prefix_parent(child)
        if hyphen_candidate is not None and hyphen_candidate in canon_set:
            parent_map[child] = hyphen_candidate
            continue
        # Rule 1: longest right-substring match
        for parent in sorted_by_len:
            if parent == child:
                continue
            if not _token_aligned_right_substring(parent, child):
                continue
            # freq_doc prior
            if doc_freq.get(parent, 0) < doc_freq.get(child, 0):
                continue
            parent_map[child] = parent
            break
    return parent_map


def _walk_depth(child: str, parent_map: Dict[str, str], max_depth: int = 16) -> int:
    """Compute hierarchy depth by walking parent chain. Bounded to
    max_depth to defend against the (impossible-by-construction but
    cheap-to-guard) case of a cycle."""
    depth = 0
    cur = child
    seen = {cur}
    for _ in range(max_depth):
        parent = parent_map.get(cur, "")
        if not parent:
            return depth
        depth += 1
        cur = parent
        if cur in seen:
            # Cycle (should be impossible because every parent is shorter
            # than its child); treat as root to avoid infinite loop.
            return depth - 1
        seen.add(cur)
    return depth


def assign_hierarchy(constructs_df: pd.DataFrame) -> pd.DataFrame:
    """Add parent_canonical, hierarchy_depth, is_root columns to
    constructs_df. Returns a new DataFrame (does not mutate input).

    The input is expected to have the columns produced by
    cluster_constructs: surface_form, canonical_form, cluster_id,
    freq_doc, freq_total, construct_id.

    Behaviour on an empty DataFrame: returns the DataFrame with the
    three new columns present but empty.

    Behaviour when canonical_form is missing: returns the input
    unchanged with the three new columns added as defaults (empty
    parent, depth 0, is_root 1). This permits the function to be a
    no-op safety net.
    """
    if constructs_df is None or len(constructs_df) == 0:
        out = constructs_df.copy() if constructs_df is not None else pd.DataFrame()
        out["parent_canonical"] = pd.Series(dtype="object")
        out["hierarchy_depth"] = pd.Series(dtype="int64")
        out["is_root"] = pd.Series(dtype="int64")
        return out

    out = constructs_df.copy().reset_index(drop=True)

    if "canonical_form" not in out.columns:
        # Defensive: cluster_constructs guarantees this column, but if
        # the function is called on an unclustered frame just mark
        # everything as roots.
        out["parent_canonical"] = ""
        out["hierarchy_depth"] = 0
        out["is_root"] = 1
        return out

    # Build canonical -> doc_freq map. doc_freq is summed across all
    # rows sharing a canonical_form (because surface variants in one
    # cluster all contribute to the canonical's document presence).
    out["_canon_norm"] = out["canonical_form"].astype(str).map(_normalise)

    # Aggregate freq_doc per canonical. Use the maximum surface-form
    # freq_doc within each cluster as the canonical's doc frequency,
    # which is conservative (does not double-count documents that
    # contain two surface variants of the same construct).
    canon_freq = (
        out.groupby("_canon_norm", as_index=False)["freq_doc"]
           .max()
           .rename(columns={"freq_doc": "_canon_freq"})
    )
    doc_freq: Dict[str, int] = {
        row["_canon_norm"]: int(row["_canon_freq"])
        for _, row in canon_freq.iterrows()
    }

    canonicals: List[str] = sorted({c for c in out["_canon_norm"] if c})

    # Apply rules
    parent_map = _build_parent_map(canonicals, doc_freq)

    # Resolve depth and root status, and pre-compute each canonical's
    # hierarchy root (used by the Stata graph layer's level(root)
    # option without requiring a per-row chain walk).
    depth_cache: Dict[str, int] = {}
    root_cache: Dict[str, str] = {}
    for c in canonicals:
        depth_cache[c] = _walk_depth(c, parent_map)
        # Walk to root
        root = c
        seen = {root}
        for _ in range(16):
            parent = parent_map.get(root, "")
            if not parent or parent in seen:
                break
            root = parent
            seen.add(root)
        root_cache[c] = root

    # Project results back to the per-construct rows
    out["parent_canonical"] = out["_canon_norm"].map(
        lambda c: parent_map.get(c, "")
    )
    out["hierarchy_depth"] = out["_canon_norm"].map(
        lambda c: depth_cache.get(c, 0)
    ).astype(int)
    out["is_root"] = (out["parent_canonical"] == "").astype(int)
    out["canonical_root"] = out["_canon_norm"].map(
        lambda c: root_cache.get(c, c)
    )

    # Restore the parent_canonical and canonical_root to original case
    canon_case_map: Dict[str, str] = {}
    for _, row in out[["canonical_form", "_canon_norm"]].iterrows():
        norm = row["_canon_norm"]
        if norm and norm not in canon_case_map:
            canon_case_map[norm] = row["canonical_form"]
    out["parent_canonical"] = out["parent_canonical"].map(
        lambda p: canon_case_map.get(p, p) if p else ""
    )
    out["canonical_root"] = out["canonical_root"].map(
        lambda r: canon_case_map.get(r, r) if r else ""
    )

    out = out.drop(columns=["_canon_norm"])
    return out


def roll_up_constructs(
    constructs_df: pd.DataFrame,
    level: str = "leaf",
) -> pd.DataFrame:
    """Return a copy of constructs_df with canonical_form remapped
    according to the requested level.

    level:
      "leaf" -- no remapping; constructs returned at maximum specificity.
      "root" -- each construct's canonical_form replaced by its hierarchy
                root (the topmost ancestor).
      An integer N (passed as a string) -- collapse to depth N; for
                deeper constructs, walk up the parent chain to depth N.

    The function does not aggregate frequencies; the caller is
    responsible for any post-roll-up groupby. The function exists as a
    pure mapping step so that visualisation code can choose to display
    constructs at varying specificity without recomputing the pipeline.
    """
    if constructs_df is None or len(constructs_df) == 0:
        return constructs_df

    out = constructs_df.copy().reset_index(drop=True)

    if level == "leaf":
        return out

    if "parent_canonical" not in out.columns:
        # No hierarchy information available; return unchanged.
        return out

    # Build parent map from the DataFrame itself
    canon_to_parent: Dict[str, str] = {}
    canon_to_depth: Dict[str, int] = {}
    for _, row in out.iterrows():
        c = _normalise(row["canonical_form"])
        canon_to_parent[c] = _normalise(row.get("parent_canonical", ""))
        canon_to_depth[c] = int(row.get("hierarchy_depth", 0))

    if level == "root":
        target_depth = 0
    else:
        try:
            target_depth = int(level)
        except (TypeError, ValueError):
            raise ValueError(
                f"level must be 'leaf', 'root', or an integer; got {level!r}"
            )
        if target_depth < 0:
            raise ValueError(f"level must be non-negative; got {target_depth}")

    def _walk_to_depth(canon: str) -> str:
        c = _normalise(canon)
        # Walk up while current depth > target depth
        while canon_to_depth.get(c, 0) > target_depth:
            parent = canon_to_parent.get(c, "")
            if not parent:
                break
            c = parent
        return c

    # We need the displayed canonical_form to be in its original case.
    # Build a normalised -> display map.
    case_map: Dict[str, str] = {}
    for _, row in out.iterrows():
        c_norm = _normalise(row["canonical_form"])
        if c_norm and c_norm not in case_map:
            case_map[c_norm] = row["canonical_form"]

    out["canonical_form"] = out["canonical_form"].apply(
        lambda c: case_map.get(_walk_to_depth(c), c)
    )
    return out
