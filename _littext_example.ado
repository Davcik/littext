/*!
_littext_example: load the bundled synthetic example corpus.

littext ships a single synthetic corpus, themed on the resource-based
view (RBV) of the firm:

  littext_example.dta        300 abstracts (1994-2025), 18 synthetic
                             journals, 17 RBV sub-territories
  littext_example_gold.dta   1280 ground-truth relations across the
                             five relation types pos_assoc, neg_assoc,
                             moderates, mediates, assoc

Syntax:
  littext example                  /* load the 300-abstract corpus       */
  littext example, clear           /* replace data in memory             */
  littext example, gold            /* load the ground-truth relations    */
  littext example, gold clear

The corpus is SYNTHETIC. It embeds known constructs and relationships
drawn from RBV terminology, but the abstracts are not real publications
and must not be cited as bibliometric data. Because it is generated from
the same construct and dependency-pattern substrate the extractor
targets, the gold file is suitable as a controlled regression anchor but
NOT as a basis for reporting precision/recall as external validation.
*/

program define _littext_example
    version 19.0
    syntax [, Gold Clear]
    local gd = ("`gold'" != "")
    if `gd' {
        local fname "littext_example_gold.dta"
        local desc "ground-truth relations (1280 rows; pos_assoc, neg_assoc, moderates, mediates, assoc)"
    }
    else {
        local fname "littext_example.dta"
        local desc "synthetic RBV corpus (300 abstracts; demonstration only)"
    }
    _littext_resolve, subdir(data) name(`"`fname'"')
    /* Load into the default frame. A prior -littext analyze- leaves
       lt_relations as the active frame; without this, -littext example-
       would load the corpus into lt_relations (an output frame), and a
       subsequent -analyze- would look for text() in the wrong frame. */
    capture frame change default
    use `"`r(path)'"', `clear'
    di as txt "littext: loaded `desc'."
    if `gd' {
        di as txt "         Variables: article_id, source, target, relation_type, pattern, evidence"
    }
    else {
        di as txt "         Variables: article_id, year, journal, title, authors, method, sub_territory, abstract"
        di as txt "         Synthetic corpus; not for substantive citation. Analyze with, e.g.:"
        di as txt "           littext analyze, text(abstract) id(article_id) year(year) journal(journal)"
    }
end
