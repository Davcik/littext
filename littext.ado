*! version 0.2.9  24may2026  littext: automated construct discovery from academic text
*! Author: Nebojsa S. Davcik
*! License: GPL-3.0-or-later
*!
*! See CHANGELOG.md for the full release history.
*!
*! littext is a Stata command for automated extraction of candidate construct
*! relationships from corpora of academic text (titles, abstracts, full texts).
*! It uses sentence-transformer embeddings, dependency parsing, and co-occurrence
*! statistics to generate a register of candidate relationships of the form
*! "X is associated with Y", "X moderates Z on Y", etc.

program define littext, eclass
    version 19.0
    gettoken subcmd 0 : 0, parse(" ,")
    if `"`subcmd'"' == "" {
        di as err "littext: no subcommand specified"
        di as txt ""
        di as txt "Subcommands:"
        di as txt "  {bf:littext analyze}   run the construct/relationship pipeline on a corpus"
        di as txt "  {bf:littext graph}     produce a figure from the most recent analysis"
        di as txt "  {bf:littext example}   load the bundled synthetic corpus"
        di as txt "  {bf:littext install}   verify the Python environment"
        di as txt ""
        di as txt "See {bf:help littext} for details."
        exit 198
    }
    if "`subcmd'" == "analyze"      _littext_analyze `0'
    else if "`subcmd'" == "graph"   _littext_graph `0'
    else if "`subcmd'" == "example" _littext_example `0'
    else if "`subcmd'" == "install" _littext_install `0'
    else {
        di as err "littext: unknown subcommand '`subcmd''"
        di as txt "Valid subcommands: analyze, graph, example, install"
        exit 198
    }
end
