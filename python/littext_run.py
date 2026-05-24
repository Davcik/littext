"""littext_run: single-entry script invoked by _littext_analyze.ado via `python script`.

This script is the v0.1 solution to a Stata-Python bridge issue: on Stata 19.5
Windows, many consecutive `python:` (line-mode) calls can put the bridge into
a state where it stops forwarding output and Stata commands stop responding.
The fix is to do all Python work in a single bridge crossing, which is what
`python script` provides.

This file expects the following Stata locals to be set by the calling .ado
(read via sfi.Macro.getLocal):
  pypath        absolute path to the package's python/ subdirectory
  corpus_dta    path to the temporary .dta written by the calling .ado
  unit          unit of analysis ("sentence", "abstract", or "paragraph")
  embedmodel    sentence-transformers model name
  minfreq       minimum document frequency for constructs (as string)
  maxrelations  cap on candidate relationships (as string)
  addsent       "1" to add VADER polarity, "0" to skip
  q             "1" for quiet, "0" for verbose

The script populates three pre-existing Stata frames (lt_constructs,
lt_relations, lt_diag) via sfi.Frame. The calling .ado is responsible for
creating those frames before invoking this script.
"""

from __future__ import annotations

import os
import sys
import traceback


def _main() -> None:
    # Quiet environment settings before anything heavy is imported
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    from sfi import Macro

    # Resolve the package's python/ folder and make it importable
    pypath = os.path.abspath(Macro.getLocal("pypath"))
    if pypath not in sys.path:
        sys.path.insert(0, pypath)

    # Read all parameters from Stata locals
    corpus_path  = Macro.getLocal("corpus_dta")
    unit         = Macro.getLocal("unit") or "sentence"
    embed_model  = Macro.getLocal("embedmodel") or "all-MiniLM-L6-v2"
    min_freq     = int(Macro.getLocal("minfreq") or "2")
    max_relations = int(Macro.getLocal("maxrelations") or "100000")
    add_sent     = bool(int(Macro.getLocal("addsent") or "0"))
    quiet        = bool(int(Macro.getLocal("q") or "0"))

    if not quiet:
        print(f"  [py] entry: corpus={corpus_path!r}", flush=True)
        print(f"  [py]        unit={unit}  embed={embed_model}  minfreq={min_freq}", flush=True)
        print(f"  [py]        max_relations={max_relations}  add_sentiment={add_sent}", flush=True)

    # Import the pipeline and run it. Imports happen here (one bridge crossing),
    # so any spaCy / sentence-transformers cold-load cost is paid inside this
    # single Stata-Python call.
    from littext_pipeline import run_pipeline
    run_pipeline(
        corpus_path=corpus_path,
        unit=unit,
        embed_model=embed_model,
        min_freq=min_freq,
        max_relations=max_relations,
        add_sentiment=add_sent,
        quiet=quiet,
    )


try:
    _main()
except Exception:
    # Print the full traceback so the user can see it in Stata's results window.
    print("littext: ERROR during pipeline execution:", flush=True)
    print(traceback.format_exc(), flush=True)
    raise
