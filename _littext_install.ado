/*!
_littext_install: verify that the Python environment has the required packages.

The verbose path additionally imports each package to read its version; this is slow on the first call (sentence-
transformers + torch can take 30-90s cold on Windows), and is therefore done
only when the user explicitly requests it via the verbose option.
*/

program define _littext_install
    version 19.0
    syntax [, Quiet Verbose]
    local q = ("`quiet'" != "")
    local v = ("`verbose'" != "")
    if !`q' di as txt "littext: checking Python environment..."
    capture python query
    if _rc {
        di as err "littext: Python is not configured in Stata."
        di as txt `"Run -python set exec "C:\path\to\python.exe"- (use your actual path)."'
        exit 198
    }
    _littext_resolve, subdir(python) name(littext_run.py)
    local pypath `"`r(dir)'"'
    python: import sys, os
    python: _pypath_abs = os.path.abspath(r"`pypath'")
    python: sys.path.insert(0, _pypath_abs) if _pypath_abs not in sys.path else None
    capture python: from littext_env import check_environment, report_environment
    if _rc {
        di as err `"littext: cannot import littext_env from `pypath'"'
        di as txt "The littext Python modules could not be imported; reinstall the package."
        exit 198
    }
    /* Only run the (slow, importing) verbose report when the user asks for it. */
    if `v' python: report_environment(verbose=True)
    /* Always run the cheap (non-importing) check; it returns a bool to Stata via Macro. */
    python: from sfi import Macro
    python: Macro.setLocal("pyok", "1" if check_environment() else "0")
    if "`pyok'" != "1" {
        di as err "littext: one or more required Python packages are missing."
        di as txt "Install them in the Python environment that Stata is bound to:"
        di as txt "  pip install spacy sentence-transformers hdbscan scikit-learn umap-learn matplotlib networkx pandas"
        di as txt "  python -m spacy download en_core_web_sm"
        di as txt "(Run -littext install, verbose- to see exactly which package is missing.)"
        exit 198
    }
    if !`q' di as txt "littext: environment OK."
end
