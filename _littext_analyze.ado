/*!
_littext_analyze: run the construct/relationship pipeline on the current dataset.

The entire Python pipeline runs via a single `python script` invocation. This
avoids two problems that the previous designs encountered:

  (1) Stata 19.5's per-line `python:` bridge has overhead and, on Windows, can
      put the Stata-Python integration into a state where consecutive python:
      calls hang silently. `python script` crosses the bridge exactly once.

  (2) The multi-line `python: ... end` block form cannot be used inside
      `program define` because the `end` keyword collides with the program's
      own `end`, causing a parser error at .ado load time.

The script at python/littext_run.py reads its parameters from Stata locals
via sfi.Macro.getLocal(), so backslashes in Windows tempfile paths do not
need to be escaped via Stata macro expansion.

Output: three Stata frames left in memory
  lt_constructs   - canonical constructs with frequency and cluster info
  lt_relations    - candidate construct relationships with confidence scores
  lt_diag         - per-document diagnostics
*/

program define _littext_analyze, eclass
    version 19.0
    syntax , Text(varname) [Id(varname) Year(varname) Journal(varname) Unit(string) EMBedmodel(string) MINFreq(string) MAXRelations(integer 100000) ADDSentiment Quiet Saving(string) Replace]
    if "`unit'" == "" local unit "sentence"
    if !inlist("`unit'", "sentence", "abstract", "paragraph") {
        di as err "littext: unit() must be sentence, abstract, or paragraph"
        exit 198
    }
    if "`embedmodel'" == "" local embedmodel "all-MiniLM-L6-v2"
    /* v0.2.6: corpus-size-aware min_freq default.
       For small corpora (under 50 abstracts) the default is 1, which keeps
       single-document constructs in the candidate frame so the relation
       matcher can exercise them. For larger corpora the default returns to
       2, which acts as a noise filter against single-document artefacts.
       The user-supplied minfreq() option overrides in either case. */
    qui count
    local n_docs = r(N)
    local minfreq_user = "`minfreq'"
    if "`minfreq'" == "" {
        if `n_docs' < 50 local minfreq = 1
        else             local minfreq = 2
    }
    else {
        capture confirm integer number `minfreq'
        if _rc {
            di as err "littext: minfreq() must be a non-negative integer"
            exit 198
        }
        if `minfreq' < 1 {
            di as err "littext: minfreq() must be at least 1"
            exit 198
        }
    }
    local addsent = ("`addsentiment'" != "")
    local q = ("`quiet'" != "")
    if "`id'" == "" {
        tempvar autoid
        gen long `autoid' = _n
        local id "`autoid'"
    }
    /* Stage 1: cheap environment check (sub-millisecond; uses find_spec). */
    if !`q' di as txt "[1/5] littext: env check..."
    _littext_install, quiet
    /* Stage 2: resolve package paths. */
    if !`q' di as txt "[2/5] littext: resolving package path..."
    findfile "littext.ado"
    local adopath = subinstr(`"`r(fn)'"', "littext.ado", "", .)
    local pypath = `"`adopath'python"'
    local runscript = `"`pypath'/littext_run.py"'
    /* v0.2.6: print the min_freq setting and the rationale so the user knows
       what filter was applied. Suppressed under quiet. */
    if !`q' {
        if "`minfreq_user'" != "" {
            di as txt "littext: minfreq=`minfreq' (user-specified)"
        }
        else if `n_docs' < 50 {
            di as txt "littext: minfreq=1 (default for small corpora: `n_docs' documents < 50)"
            di as txt "        Single-document constructs are retained; suppress noise by passing minfreq(2)."
        }
        else {
            di as txt "littext: minfreq=2 (default for corpora of `n_docs' documents)"
        }
    }
    /* Stage 3: marshal the corpus to a temporary .dta. */
    if !`q' di as txt "[3/5] littext: marshalling corpus to temporary .dta..."
    tempfile corpus_dta
    preserve
    keep `id' `text' `year' `journal'
    rename `text' lt_text
    rename `id' lt_id
    capture confirm string variable lt_id
    if _rc tostring lt_id, replace force
    if "`year'" != "" rename `year' lt_year
    else gen lt_year = .
    if "`journal'" != "" rename `journal' lt_journal
    else gen str1 lt_journal = ""
    qui save "`corpus_dta'", replace
    restore
    /* Stage 4: create the three output frames so Python can populate them. */
    if !`q' di as txt "[4/5] littext: creating output frames..."
    capture frame drop lt_constructs
    capture frame drop lt_relations
    capture frame drop lt_diag
    frame create lt_constructs
    frame create lt_relations
    frame create lt_diag
    /* Stage 5: run the pipeline. This is a single bridge crossing.
       The Python script reads pypath, corpus_dta, unit, embedmodel, minfreq,
       maxrelations, addsent, and q from Stata locals via sfi.Macro. */
    if !`q' di as txt "[5/5] littext: running pipeline (single bridge crossing; spaCy + sentence-transformers load lazily on first run, ~30-120s)..."
    python script `"`runscript'"'
    if !`q' di as txt "littext: pipeline returned; finalising..."
    frame lt_relations: qui count
    local nrel = r(N)
    frame lt_constructs: qui count
    local ncon = r(N)
    if "`saving'" != "" {
        local repl = ("`replace'" != "") * 1
        if `repl' local replopt "replace"
        else local replopt ""
        frame lt_constructs: save "`saving'_constructs.dta", `replopt'
        frame lt_relations:  save "`saving'_relations.dta",  `replopt'
        frame lt_diag:       save "`saving'_diag.dta",       `replopt'
        if !`q' di as txt "littext: results also written to '`saving'_*.dta'"
    }
    frame change lt_relations
    if !`q' {
        di as txt ""
        di as txt "littext: analysis complete."
        di as txt "  Constructs extracted: `ncon'"
        di as txt "  Candidate relationships: `nrel'"
        di as txt "  Active frame: lt_relations  (also available: lt_constructs, lt_diag)"
        di as txt ""
        di as txt "Try:  list source target relation_type confidence in 1/10"
        di as txt "      tab relation_type"
        di as txt "      littext graph, type(map)"
    }
    ereturn local cmd = "littext analyze"
    ereturn local unit = "`unit'"
    ereturn local embed_model = "`embedmodel'"
    ereturn scalar n_constructs = `ncon'
    ereturn scalar n_relations  = `nrel'
end
