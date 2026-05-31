# littext RBV synthetic corpus (v0.1)

Synthetic 300-abstract corpus for testing, demonstration, and worked
examples in the `littext` Stata package. Themed on the resource-based
view of the firm and its principal extensions.

## Files

- `littext_rbv_synth_v01.xlsx` — three-sheet workbook (abstracts, gold,
  coverage_summary).
- `littext_rbv_synth_v01_abstracts.csv` — Stata-friendly mirror of the
  abstracts sheet (UTF-8, all fields quoted).
- `littext_rbv_synth_v01_gold.csv` — Stata-friendly mirror of the gold
  sheet.

## Status

This is a **synthetic** corpus. The abstracts are not real published
work. They are composed from a combinatorial substrate of constructs,
sentence templates, and structural skeletons designed to mimic the
register, length, and dependency patterns of real RBV/dynamic-
capabilities/absorptive-capacity literature. Author names are
synthetic; journal names and years are real but the author-to-journal
attribution is fictitious. The corpus is freely redistributable under
the same GPL-3.0-or-later licence as the rest of `littext`.

## Schema

### abstracts

| Column         | Type   | Description                                       |
|----------------|--------|---------------------------------------------------|
| article_id     | int    | 1-300, primary key                                |
| year           | int    | 1992-2024, weighted toward 2002-2020              |
| journal        | str    | One of 18 real management/strategy journals       |
| title          | str    | Composed title; constructs drawn from the body    |
| authors        | str    | APA-style authors; surnames synthetic             |
| method         | str    | Quantitative / Qualitative / Mixed /              |
|                |        | Meta-analysis / Experimental / Conceptual         |
| sub_territory  | str    | One of 16 RBV sub-literatures (see below)         |
| abstract       | str    | Composed abstract, mean 146 words                 |

The first 15 rows are hand-written anchor abstracts; the remaining 285
are combinatorially generated.

### gold

| Column         | Type   | Description                                       |
|----------------|--------|---------------------------------------------------|
| article_id     | int    | Foreign key to abstracts.article_id               |
| source         | str    | Source construct                                  |
| target         | str    | Target construct (for mediation/moderation rows,  |
|                |        | the target encodes the "x -> y" pair)             |
| relation_type  | str    | pos_assoc, neg_assoc, mediates, moderates, assoc  |
| pattern        | str    | A-F, the dependency-arc pattern that generated    |
|                |        | the relation (see littext's six-pattern matcher)  |
| evidence       | str    | The literal sentence in the abstract that         |
|                |        | warrants the gold-standard coding                 |

## Sub-territories

16 RBV sub-literatures are represented:

1. `classic_rbv` — Wernerfelt/Barney foundations, VRIN/VRIO, isolating mechanisms
2. `dynamic_capabilities` — Teece et al., sensing/seizing/reconfiguring
3. `absorptive_capacity` — Cohen & Levinthal lineage
4. `knowledge_based_view` — tacit/explicit knowledge as strategic resource
5. `intellectual_capital` — human/structural/relational capital
6. `social_capital` — structural/relational/cognitive dimensions
7. `alliance_capability` — relational view, alliance management capability
8. `IT_capabilities` — IT-enabled intangibles, digital capabilities
9. `resource_orchestration` — Sirmon et al., structuring/bundling/leveraging
10. `microfoundations` — managerial cognition, individual-level antecedents
11. `natural_RBV` — Hart's natural-resource-based view
12. `ambidexterity` — exploration/exploitation, structural/contextual ambidexterity
13. `emerging_market_RBV` — institutional voids, firm-specific advantages
14. `organisational_learning` — exploratory/exploitative learning
15. `innovation_outcomes` — innovation as the focal performance outcome
16. `ESG_stakeholder_RBV` — stakeholder capabilities, ESG, reputation

## Pattern coverage

All six dependency-arc patterns recognised by `littext`'s v0.2.9
matcher are exercised:

| Pattern | Description                | Count | Share  |
|---------|----------------------------|-------|--------|
| A       | Mediation / moderation     | ~317  | ~26 %  |
| B       | Finite VSO (active)        | ~222  | ~18 %  |
| C       | Passive voice              | ~72   | ~6 %   |
| D       | Nominal "effect of X on Y" | ~127  | ~10 %  |
| E       | Adjectival valence         | ~232  | ~19 %  |
| F       | Copular anchor             | ~310  | ~25 %  |

Pattern F is over-represented relative to its natural-corpus prevalence
because v0.3 development is targeted at F-pattern recovery; this corpus
should therefore provide ample test points for the v0.3 work on
sentence pre-segmentation and the F-pattern matcher.

## Stata loading

```stata
import delimited "littext_rbv_synth_v01_abstracts.csv", clear varnames(1) bindquote(strict) stripquote(yes)
save "littext_rbv_synth_v01_abstracts.dta", replace

import delimited "littext_rbv_synth_v01_gold.csv", clear varnames(1) bindquote(strict) stripquote(yes)
save "littext_rbv_synth_v01_gold.dta", replace

use "littext_rbv_synth_v01_abstracts.dta", clear
littext analyze, text(abstract) id(article_id) year(year) journal(journal)
```

## Distributional notes

- Abstracts: mean 146 words, median 135, p10=74, p90=231 (real
  reference corpus: mean 174, median 173, p10=80, p90=260). The
  synthetic centre of mass is slightly lower than the empirical
  reference, but the lower tail (short conceptual papers) and upper
  tail (long mixed-method papers) are well represented.
- Years: skewed toward 2003-2018, with thinner representation of
  pre-1998 and post-2022.
- Methods: predominantly Quantitative (~60 %); the remainder split
  across Qualitative, Conceptual, Meta-analysis, Mixed, Experimental.
- Journals: 18 outlets, with SMJ/AMJ/JoM/JMS receiving the largest
  weight.

## Known limitations

1. The corpus is generated. Real abstracts contain idiosyncratic
   construct labels, theory-citation conventions, and rhetorical
   structures that combinatorial composition cannot fully reproduce.
   Treat the corpus as a controlled testbed rather than a substitute
   for a real bibliometric resource.

2. Synonym variants are present but limited. HDBSCAN should fold
   several declared variant pairs (e.g., "absorptive capability"
   ≡ "absorptive capacity") but the synonym density is lower than
   real-world prose.

3. The first 15 abstracts are hand-written and stylistically
   distinguishable from the combinatorial 285. Stratify samples by
   `article_id >= 16` if uniform composition is required.

## Licence

GPL-3.0-or-later, matching the parent `littext` package. Free for
academic, commercial, and pedagogical use.

## Citation

When using this corpus in published work, please cite:

> Davcik, N. S. (2026). *littext: Stata module for automated construct
> and relationship discovery from research text*,
> Available at https://github.com/Davcik/littext.

