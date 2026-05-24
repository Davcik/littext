/*!
_littext_example: load a bundled synthetic corpus.

The corpora are named by size:
  littext_example30.dta         30 abstracts; fast smoke testing
  littext_example200.dta        200 abstracts; full demonstration corpus
  littext_example_gold30.dta    74 ground-truth relations for the n=30 corpus
  littext_example_gold200.dta   477 ground-truth relations for the n=200 corpus

Syntax:
  littext example                    /* defaults to n(30), the small corpus    */
  littext example, n(30)             /* explicit small                          */
  littext example, n(200)            /* full demonstration corpus               */
  littext example, n(30) gold        /* ground-truth relations for n=30         */
  littext example, n(200) gold       /* ground-truth relations for n=200        */

All corpora are synthetic. They embed known constructs and relationships
drawn from real digital-marketing, branding, and business-ethics terminology,
but they are NOT real publications and must not be cited as bibliometric data.
*/

program define _littext_example
    version 19.0
    syntax [, N(integer 30) Gold Clear]
    if !inlist(`n', 30, 200) {
        di as err "littext example: n() must be 30 or 200 (got `n')"
        exit 198
    }
    local cl = ("`clear'" != "")
    local gd = ("`gold'" != "")
    if `cl' clear
    findfile "littext.ado"
    local adopath = subinstr(`"`r(fn)'"', "littext.ado", "", .)
    local datapath = `"`adopath'data"'
    if `gd' {
        local fname "littext_example_gold`n'.dta"
        if `n' == 30  local desc "ground-truth relationships for the n=30 corpus (74 rows)"
        if `n' == 200 local desc "ground-truth relationships for the n=200 corpus (477 rows)"
    }
    else {
        local fname "littext_example`n'.dta"
        if `n' == 30  local desc "small synthetic corpus (n=30 abstracts; for fast iteration)"
        if `n' == 200 local desc "full synthetic corpus (n=200 abstracts; demonstration)"
    }
    use `"`datapath'/`fname'"', `clear'
    di as txt "littext: loaded `desc'."
    if !`gd' {
        di as txt "         Variables: article_id, year, journal, title, abstract"
        di as txt "         This corpus is synthetic and not for substantive citation."
    }
end
