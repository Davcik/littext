"""littext_viz: matplotlib-based figures for littext.

The Stata-native figures (frequency, distribution, trend, confidence) are
produced by _littext_graph.ado directly. This module handles only the figures
that genuinely require a Python plotting stack: the UMAP concept map, the
relationship network, and the cluster dendrogram.

All figures are saved to PNG (300 dpi) and PDF (vector) so that the user has
both raster and publication-quality outputs without re-running the pipeline.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd

# matplotlib is imported lazily inside the draw functions because importing it
# at module-load time slows down -littext analyze- unnecessarily.


def _save_both(fig, out_stub: str) -> None:
    fig.savefig(out_stub + ".png", dpi=300, bbox_inches="tight")
    fig.savefig(out_stub + ".pdf", bbox_inches="tight")


def draw_figure(kind: str, top: int = 20, out_stub: str = "littext_figure",
                weighted: bool = False) -> None:
    """Dispatch to the requested figure type using cached pipeline state.

    v0.2.7: new kinds `cooccurrence` and `roles` are heatmaps; the
    `weighted` flag enables continuous-confidence edge colouring in
    `network`.
    """
    from littext_state import load_state
    state = load_state()
    constructs_df = state["constructs_df"]
    embeddings = state["construct_embeddings"]
    relations_df = state["relations_df"]

    if kind == "map":
        _draw_concept_map(constructs_df, embeddings, top=top, out_stub=out_stub)
    elif kind == "network":
        _draw_network(constructs_df, relations_df, top=top, out_stub=out_stub,
                      weighted=weighted)
    elif kind == "dendrogram":
        _draw_dendrogram(constructs_df, embeddings, top=top, out_stub=out_stub)
    elif kind == "cooccurrence":
        _draw_cooccurrence(constructs_df, relations_df, top=top, out_stub=out_stub)
    elif kind == "roles":
        _draw_roles(constructs_df, relations_df, top=top, out_stub=out_stub)
    else:
        raise ValueError(f"unknown figure kind: {kind}")


def _draw_concept_map(constructs_df: pd.DataFrame, embeddings: np.ndarray, top: int, out_stub: str) -> None:
    import warnings
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # UMAP issues a UserWarning when random_state is set, advising that
    # parallelism is disabled for reproducibility. We set random_state
    # deliberately for that reason; the warning is therefore expected and
    # adds noise to Stata's results window.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="umap")
        import umap

    if len(constructs_df) < 5:
        # Not enough points for UMAP; draw a placeholder
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Too few constructs for a concept map\n(need at least 5).",
                ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    n_neighbors = min(15, max(2, len(constructs_df) - 1))
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="umap")
        reducer = umap.UMAP(n_components=2, n_neighbors=n_neighbors, min_dist=0.1, metric="cosine", random_state=42)
        coords = reducer.fit_transform(embeddings)

    cf = constructs_df.copy().reset_index(drop=True)
    cf["x"] = coords[:, 0]
    cf["y"] = coords[:, 1]

    fig, ax = plt.subplots(figsize=(10, 8))
    clusters = cf["cluster_id"].unique()
    cmap = plt.get_cmap("tab20")
    for k, cl in enumerate(clusters):
        sub = cf[cf["cluster_id"] == cl]
        ax.scatter(sub["x"], sub["y"], s=20 + 4 * sub["freq_doc"].clip(upper=20),
                   color=cmap(k % 20), alpha=0.7, edgecolors="white", linewidths=0.5)
    # Label top-`top` constructs by frequency
    top_cf = cf.sort_values("freq_doc", ascending=False).head(top)
    for _, row in top_cf.iterrows():
        ax.annotate(row["canonical_form"], (row["x"], row["y"]),
                    fontsize=9, alpha=0.85, xytext=(3, 3), textcoords="offset points")
    ax.set_title("Concept map of extracted constructs (UMAP projection)")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save_both(fig, out_stub)
    plt.close(fig)


def _draw_network(constructs_df: pd.DataFrame, relations_df: pd.DataFrame, top: int,
                  out_stub: str, weighted: bool = False) -> None:
    """Force-directed network of candidate relationships.

    v0.2.7: when `weighted=True`, edges are coloured continuously by
    confidence using a viridis colourmap rather than by relation type.
    This is option D in the v0.2.7 design discussion - useful when the
    user cares about the strength of relationships more than their
    syntactic type.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx

    if len(relations_df) == 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No candidate relationships to plot.", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    rels = (
        relations_df
        .sort_values("confidence", ascending=False)
        .drop_duplicates(subset=["source", "target", "relation_type"])
        .head(top * 4)
    )
    g = nx.DiGraph()
    color_map = {
        "pos_assoc": "#1b7837",
        "neg_assoc": "#c51b7d",
        "moderates": "#fdb863",
        "mediates":  "#5e3c99",
        "causes":    "#b35806",
        "assoc":     "#888888",
    }
    for _, r in rels.iterrows():
        g.add_edge(r["source"], r["target"],
                   weight=float(r["confidence"]),
                   rel_type=r["relation_type"],
                   color=color_map.get(r["relation_type"], "#888888"))

    if g.number_of_nodes() == 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Empty relationship graph.", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    degree_sorted = sorted(g.degree, key=lambda x: x[1], reverse=True)
    keep_nodes = set(n for n, _ in degree_sorted[: max(top, 5)])
    g = g.subgraph(keep_nodes).copy()

    pos = nx.spring_layout(g, seed=42, k=0.9)
    fig, ax = plt.subplots(figsize=(11, 9))

    if weighted:
        # v0.2.7: edges coloured continuously by confidence (viridis).
        import matplotlib.cm as cm
        from matplotlib.colors import Normalize
        weights = [g[u][v]["weight"] for u, v in g.edges()]
        if weights:
            wmin, wmax = min(weights), max(weights)
            norm = Normalize(vmin=wmin, vmax=wmax)
            cmap = cm.get_cmap("viridis")
            colours = [cmap(norm(w)) for w in weights]
            widths = [1.0 + 4.0 * w for w in weights]
            nx.draw_networkx_edges(g, pos, edge_color=colours, width=widths,
                                   alpha=0.85, arrows=True, arrowsize=10, ax=ax)
            # Colourbar
            sm = cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.02)
            cbar.set_label("Edge confidence")
        title_suffix = " (edges by confidence)"
    else:
        # Original v0.2 behaviour: edges by relation-type colour
        for rel_type, color in color_map.items():
            edges = [(u, v) for u, v, d in g.edges(data=True) if d["rel_type"] == rel_type]
            if not edges:
                continue
            widths = [1.0 + 4.0 * g[u][v]["weight"] for u, v in edges]
            nx.draw_networkx_edges(g, pos, edgelist=edges, edge_color=color,
                                   width=widths, alpha=0.7, arrows=True, arrowsize=10, ax=ax)
        title_suffix = " (edges by relation type)"

    nx.draw_networkx_nodes(g, pos, node_size=400, node_color="#dddddd",
                           edgecolors="#444444", linewidths=0.8, ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=9, ax=ax)

    if not weighted:
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color=color_map[k], lw=2, label=k)
            for k in ["pos_assoc", "neg_assoc", "moderates", "mediates", "causes", "assoc"]
        ]
        ax.legend(handles=legend_elements, loc="lower right", fontsize=8, frameon=False)

    ax.set_title("Candidate construct-relationship network" + title_suffix)
    ax.set_axis_off()
    _save_both(fig, out_stub)
    plt.close(fig)


def _draw_dendrogram(constructs_df: pd.DataFrame, embeddings: np.ndarray, top: int, out_stub: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import linkage, dendrogram
    from scipy.spatial.distance import pdist

    if len(constructs_df) < 3:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Too few constructs for a dendrogram\n(need at least 3).",
                ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    # Restrict to top-K constructs to keep the figure legible
    cf = constructs_df.copy().reset_index(drop=True)
    cf["__idx__"] = cf.index
    top_idx = cf.sort_values("freq_doc", ascending=False).head(max(top, 10))["__idx__"].tolist()
    sub_emb = embeddings[top_idx]
    sub_labels = cf.loc[top_idx, "canonical_form"].tolist()
    dist = pdist(sub_emb, metric="cosine")
    z = linkage(dist, method="average")

    fig, ax = plt.subplots(figsize=(10, max(6, 0.25 * len(sub_labels))))
    dendrogram(z, labels=sub_labels, orientation="left", leaf_font_size=9, color_threshold=0.3 * z[:, 2].max(), ax=ax)
    ax.set_title("Construct-cluster dendrogram (cosine distance, average linkage)")
    ax.set_xlabel("Cosine distance")
    _save_both(fig, out_stub)
    plt.close(fig)


def _draw_cooccurrence(constructs_df: pd.DataFrame, relations_df: pd.DataFrame,
                       top: int, out_stub: str) -> None:
    """v0.2.7 (option A): pairwise NPMI heatmap of top-k constructs.

    Rows and columns are the top-k canonical constructs (by document
    frequency, summed within cluster). Cell colour encodes the
    relationship confidence between each pair, derived from the
    relations frame. Diagonal cells are masked.

    This is the standard text-mining co-occurrence heatmap, useful for
    exploratory landscape inspection. It complements the network graph:
    the network shows discrete edges between high-confidence pairs;
    the heatmap shows the full pairwise landscape including weak
    relationships.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if len(constructs_df) == 0 or len(relations_df) == 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Not enough data for a co-occurrence heatmap.",
                ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    # Aggregate to canonical-form level (constructs frame may have multiple
    # surface forms per canonical cluster).
    canon_freq = (
        constructs_df.groupby("canonical_form")["freq_doc"].sum()
        .sort_values(ascending=False)
    )
    top_constructs = canon_freq.head(top).index.tolist()
    n = len(top_constructs)
    if n < 2:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, f"Only {n} canonical constructs - heatmap requires >=2.",
                ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    # Build the matrix: max confidence between each pair (relations may
    # contain multiple rows per pair from different sentences; we take the
    # highest confidence as the cell value because the lower-confidence
    # rows are typically duplicates).
    idx = {c: i for i, c in enumerate(top_constructs)}
    M = np.full((n, n), np.nan)
    for _, r in relations_df.iterrows():
        s, t = r["source"], r["target"]
        if s in idx and t in idx:
            i, j = idx[s], idx[t]
            conf = float(r["confidence"])
            # Symmetric: cell (i,j) and (j,i) both get the max confidence
            if np.isnan(M[i, j]) or conf > M[i, j]:
                M[i, j] = conf
            if np.isnan(M[j, i]) or conf > M[j, i]:
                M[j, i] = conf
    # Mask the diagonal
    np.fill_diagonal(M, np.nan)

    # Plot
    fig_w = max(8, 0.4 * n + 4)
    fig_h = max(6, 0.4 * n + 3)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    cmap = plt.get_cmap("YlOrRd")
    cmap.set_bad(color="#f0f0f0")  # NaN cells in light grey
    im = ax.imshow(M, cmap=cmap, vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(top_constructs, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(top_constructs, fontsize=8)
    ax.set_title(f"Construct co-occurrence (top {n} by document frequency)")
    cbar = fig.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label("Maximum pair confidence")
    plt.tight_layout()
    _save_both(fig, out_stub)
    plt.close(fig)


def _draw_roles(constructs_df: pd.DataFrame, relations_df: pd.DataFrame,
                top: int, out_stub: str) -> None:
    """v0.2.7 (option B): construct x relation-type heatmap.

    Rows are top-k canonical constructs, columns are the six relation
    types (pos_assoc, neg_assoc, moderates, mediates, causes, assoc).
    Cell values are counts of how many times each construct participated
    in each relation type (in either source or target role).

    Substantively informative: surfaces the syntactic ROLE each construct
    tends to play in the corpus, distinguishing e.g. constructs that are
    mostly mediators from those that are mostly outcomes.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if len(constructs_df) == 0 or len(relations_df) == 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Not enough data for a roles heatmap.",
                ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    canon_freq = (
        constructs_df.groupby("canonical_form")["freq_doc"].sum()
        .sort_values(ascending=False)
    )
    top_constructs = canon_freq.head(top).index.tolist()
    n = len(top_constructs)
    if n < 1:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No canonical constructs.",
                ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        _save_both(fig, out_stub)
        plt.close(fig)
        return

    rel_types = ["pos_assoc", "neg_assoc", "moderates", "mediates", "causes", "assoc"]
    idx = {c: i for i, c in enumerate(top_constructs)}
    M = np.zeros((n, len(rel_types)), dtype=int)
    for _, r in relations_df.iterrows():
        rt = r["relation_type"]
        if rt not in rel_types:
            continue
        col = rel_types.index(rt)
        for endpoint in (r["source"], r["target"]):
            if endpoint in idx:
                M[idx[endpoint], col] += 1

    fig_w = max(7, 1.0 * len(rel_types) + 4)
    fig_h = max(6, 0.35 * n + 3)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    cmap = plt.get_cmap("Blues")
    im = ax.imshow(M, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(rel_types)))
    ax.set_yticks(range(n))
    ax.set_xticklabels(rel_types, rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(top_constructs, fontsize=8)
    ax.set_title(f"Construct roles by relation type (top {n})")
    # Annotate cells with their counts (only non-zero)
    for i in range(n):
        for j in range(len(rel_types)):
            v = M[i, j]
            if v > 0:
                # White text on dark cells, black text on light cells
                threshold = M.max() * 0.5
                color = "white" if v > threshold else "black"
                ax.text(j, i, str(v), ha="center", va="center",
                        fontsize=8, color=color)
    cbar = fig.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label("Participation count")
    plt.tight_layout()
    _save_both(fig, out_stub)
    plt.close(fig)
