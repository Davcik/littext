# littext RBV synthetic corpus (v1.0)

Synthetic 300-abstract corpus for testing, demonstration, and worked
examples in the `littext` Stata package. Themed on the resource-based
view of the firm and its principal extensions.

## Status

This is a **synthetic** corpus. The abstracts are not real published
work. They are composed from a combinatorial substrate of constructs,
sentence templates, and structural skeletons designed to mimic the
register, length, and dependency patterns of real RBV/dynamic-
capabilities/absorptive-capacity literature. Author names are
synthetic; journal names and years are real but the author-to-journal
attribution is fictitious. The corpus is freely redistributable under
the same GPL-3.0-or-later license as the rest of `littext`.

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

## Pattern coverage

All six dependency-arc patterns recognised by `littext`'s 
matcher are exercised:

| Pattern | Description                | Count | Share  |
|---------|----------------------------|-------|--------|
| A       | Mediation / moderation     | ~317  | ~26 %  |
| B       | Finite VSO (active)        | ~222  | ~18 %  |
| C       | Passive voice              | ~72   | ~6 %   |
| D       | Nominal "effect of X on Y" | ~127  | ~10 %  |
| E       | Adjectival valence         | ~232  | ~19 %  |
| F       | Copular anchor             | ~310  | ~25 %  |

## Known limitations

1. The corpus is generated. Real abstracts contain idiosyncratic
   construct labels, theory-citation conventions, and rhetorical
   structures that combinatorial composition cannot fully reproduce.
   Treat the corpus as a controlled testbed rather than a substitute
   for a real bibliometric resource.

2. Synonym variants are present but limited. 

3. The first 15 abstracts are hand-written and stylistically
   distinguishable from the combinatorial 285. 

## Licence

GPL-3.0-or-later, matching the parent `littext` package. Free for
academic, commercial, and pedagogical use.

## Citation

When using this corpus in published work, please cite:

> Davcik, N. S. (2026). *LITTEXT: Stata module for automated construct
> and relationship discovery from research text*,
> Available at https://github.com/Davcik/littext.

