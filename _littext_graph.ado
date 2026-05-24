/*!
_littext_graph: produce figures from the current littext analysis.

Types:
  frequency     bar chart of top-k constructs by document frequency  (Stata)
  distribution  stacked bar of relationship-type distribution        (Stata)
  trend         construct frequency over publication year            (Stata)
  confidence    histogram of relationship confidence scores          (Stata)
  extraction    bar of relations by extraction method                (Stata; v0.2.7)
  map           UMAP concept map of construct embeddings             (matplotlib)
  network       force-directed relationship network                  (matplotlib)
  dendrogram    construct-cluster dendrogram                         (matplotlib)
  cooccurrence  pairwise NPMI heatmap of top-k constructs            (matplotlib; v0.2.7)
  roles         construct x relation-type heatmap                    (matplotlib; v0.2.7)

Options:
  top(#)        for heatmaps, the top-k constructs (by frequency) included
  outdir(path)  absolute path for output (default: c(pwd))
  weighted      for type(network): colour edges by confidence rather than by
                relation type (v0.2.7)
  saving(stub)  file stub (default: littext_<type>)
  replace       overwrite existing files

The Stata-native graphs use a copy-to-temp-frame idiom rather than preserve/
restore inside frame blocks. The latter is fragile: when graph hbar (or any
later command) errors, the restore never runs and subsequent commands see
corrupted frame state. Copying to a uniquely-named temp frame and dropping
it at the end is robust to errors and does not modify the source frames.
*/

program define _littext_graph
    version 19.0
    syntax , [Type(string) Top(integer 20) Saving(string) OUTdir(string) WEighted Replace NAme(string)]
    if "`type'" == "" local type "map"
    if !inlist("`type'", "frequency", "distribution", "trend", "confidence", "extraction") & ///
       !inlist("`type'", "map", "network", "dendrogram", "cooccurrence", "roles") {
        di as err "littext graph: type() must be one of:"
        di as err "  frequency, distribution, trend, confidence, extraction (Stata-native)"
        di as err "  map, network, dendrogram, cooccurrence, roles (matplotlib)"
        exit 198
    }
    capture confirm frame lt_relations
    if _rc {
        di as err "littext: no analysis results found. Run -littext analyze- first."
        exit 198
    }
    /* Resolve outdir(): default to current working directory if absent.
       If the user passed a relative path, we keep it as given but warn,
       because the user explicitly asked us to support absolute paths and
       relative ones produce hard-to-predict locations on Windows. */
    if "`outdir'" == "" {
        local outdir = c(pwd)
    }
    else {
        local first2 = substr(`"`outdir'"', 2, 1)
        local first1 = substr(`"`outdir'"', 1, 1)
        local is_abs = (`"`first2'"' == ":") | (`"`first1'"' == "/")
        if !`is_abs' {
            di as txt `"littext: outdir() looks relative; resolving against current working directory ("`c(pwd)'")."'
            local outdir `"`c(pwd)'/`outdir'"'
        }
    }
    capture mkdir `"`outdir'"'
    /* Stata-native types */
    if inlist("`type'", "frequency", "distribution", "trend", "confidence", "extraction") {
        _littext_graph_stata, type(`type') top(`top') saving(`"`saving'"') outdir(`"`outdir'"') `replace' name(`"`name'"')
        exit
    }
    /* matplotlib types: dispatch to draw_figure in littext_viz.py */
    findfile "littext.ado"
    local adopath = subinstr(`"`r(fn)'"', "littext.ado", "", .)
    local pypath = `"`adopath'python"'
    if "`saving'" == "" local saving "littext_`type'"
    local outstub `"`outdir'/`saving'"'
    local weighted_flag = ("`weighted'" != "")
    python: import sys
    python: sys.path.insert(0, r"`pypath'")
    python: from littext_viz import draw_figure
    python: draw_figure(kind="`type'", top=`top', out_stub=r"`outstub'", weighted=bool(`weighted_flag'))
    di as txt `"littext: figure saved to "`outstub'.png" and "`outstub'.pdf""'
end

program define _littext_graph_stata
    version 19.0
    syntax , Type(string) [Top(integer 20) Saving(string) OUTdir(string) Replace NAme(string)]
    if "`name'" == "" local name "littext_`type'"
    local repl = ("`replace'" != "")
    if `repl' local replopt "replace"
    else local replopt ""
    frame pwf
    local origfrm = r(currentframe)
    /* Each graph type works on a uniquely-named copy of the source frame. */
    if "`type'" == "frequency" {
        capture frame drop _lt_g_freq
        frame copy lt_constructs _lt_g_freq
        frame change _lt_g_freq
        collapse (sum) freq_doc, by(canonical_form)
        gsort -freq_doc
        if _N > `top' keep if _n <= `top'
        graph hbar (asis) freq_doc, over(canonical_form, sort(1) descending label(labsize(small))) ytitle("Document frequency (summed within canonical cluster)") title("Top constructs by document frequency") name(`name', `replopt')
        frame change `origfrm'
        frame drop _lt_g_freq
    }
    else if "`type'" == "distribution" {
        capture frame drop _lt_g_dist
        frame copy lt_relations _lt_g_dist
        frame change _lt_g_dist
        contract relation_type
        gsort -_freq
        graph hbar (asis) _freq, over(relation_type, sort(1) descending) ytitle("Number of candidate relationships") title("Distribution of relationship types") name(`name', `replopt')
        frame change `origfrm'
        frame drop _lt_g_dist
    }
    else if "`type'" == "extraction" {
        /* v0.2.7: distribution of relations across extraction methods.
           Useful for inspecting which patterns (cooccur+dep:A through F)
           drove the directional rows, versus the cooccur fallback. */
        capture frame drop _lt_g_extr
        frame copy lt_relations _lt_g_extr
        frame change _lt_g_extr
        contract extraction_method
        gsort -_freq
        graph hbar (asis) _freq, over(extraction_method, sort(1) descending label(labsize(small))) ytitle("Number of candidate relationships") title("Distribution by extraction method") subtitle("cooccur = co-occurrence only (no syntactic pattern matched)") name(`name', `replopt')
        frame change `origfrm'
        frame drop _lt_g_extr
    }
    else if "`type'" == "trend" {
        capture frame drop _lt_g_trend
        frame copy lt_diag _lt_g_trend
        frame change _lt_g_trend
        capture confirm variable year
        if _rc {
            di as err "littext graph trend: no year variable in lt_diag"
            di as err "                     (did you pass year() to analyze?)"
            frame change `origfrm'
            frame drop _lt_g_trend
            exit 198
        }
        drop if missing(year)
        if _N == 0 {
            di as err "littext graph trend: no non-missing year values to plot."
            frame change `origfrm'
            frame drop _lt_g_trend
            exit 198
        }
        collapse (sum) n_constructs_extracted n_relations_extracted, by(year)
        twoway (line n_constructs_extracted year, lwidth(medthick)) (line n_relations_extracted year, lwidth(medthick) lpattern(dash)), legend(order(1 "Constructs" 2 "Relationships")) title("Extraction yield over time") xtitle("Year") ytitle("Count") name(`name', `replopt')
        frame change `origfrm'
        frame drop _lt_g_trend
    }
    else if "`type'" == "confidence" {
        capture frame drop _lt_g_conf
        frame copy lt_relations _lt_g_conf
        frame change _lt_g_conf
        histogram confidence, freq title("Distribution of candidate-relationship confidence") xtitle("Confidence") ytitle("Count") name(`name', `replopt')
        frame change `origfrm'
        frame drop _lt_g_conf
    }
    local outstub `"`outdir'/`name'"'
    quietly graph export `"`outstub'.png"', `replopt' width(1600)
    di as txt `"littext: figure saved to "`outstub'.png""'
end
