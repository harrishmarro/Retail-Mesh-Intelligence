# Milestone 4 baseline submission readiness

This checklist and the accompanying three-page report describe the earlier 34-relation course baseline. The fleet/graph MVP adds four relations and additional features documented in FLEET_GRAPH_MVP.md; update the course report before submitting the expanded application.

## Implemented and checked

- [x] New attached ER diagram is authoritative; old repository diagram is superseded.
- [x] 26 entity relations plus eight associative relations, complete keys and constraints.
- [x] SQLite DDL, integrity triggers, deterministic seed, SELECT/join/aggregation and CRUD SQL.
- [x] Layered local web CRUD application; quickstart for macOS/Linux and Windows.
- [x] 41 isolated automated tests and actual HTTP CRUD/report/CSRF checks.
- [x] Full mapping for all 42 named relationships and machine-readable data dictionary.
- [x] ACM sigconf report source and compiled PDF with exactly 2 text pages + 1 relations page.
- [x] Architecture figure and explicitly labelled interface schematic.
- [x] AI assistance disclosure and limitations; no fabricated human review.

## Required before submitting

- [ ] Capture live browser screenshots showing form entry, successful creation/search, update, deletion and restricted deletion. Run `scripts/ui_smoke.cjs` locally after starting the app, or capture manually. Replace the schematic in the report with actual readable screenshots and recheck the three-page limit. Browser execution was blocked in the preparation environment.
- [ ] Confirm graduate-student-last ordering and final author details. The report now includes all three names and University of Victoria affiliations from the supplied presentation/background paper, in their supplied order.
- [ ] Complete the team's critical evaluation of AI-generated work and record substantive individual contributions. See AI_DISCLOSURE.md.
- [x] Current ACM sigconf class: acmart v2.21 (2026-11-01), generated from the official upstream acmart.dtx/acmart.ins. Recompile after team metadata or figures change and recheck exactly three pages.
- [ ] Add the implementation to the evaluator-accessible team repository and associate all actual member Git accounts. No remote push was performed and no contribution history was manufactured.
- [ ] Rename the outer ZIP to the complete first-name list: `4_Relational_firstname1_firstname2_[...].zip`. The prepared package is `4_Relational_Avlyn_Harish_Krishnaswamy.zip`, using the supplied first names.

## Build the PDF

From `doc/report`, with a LaTeX installation including acmart dependencies:

```sh
pdflatex -interaction=nonstopmode -halt-on-error 4_Relational_Avlyn_Harish_Krishnaswamy.tex
pdflatex -interaction=nonstopmode -halt-on-error 4_Relational_Avlyn_Harish_Krishnaswamy.tex
pdfinfo 4_Relational_Avlyn_Harish_Krishnaswamy.pdf
```

The expected total is exactly three pages, excluding any separately prepared permitted AI appendix. This draft places the required AI disclosure in accompanying Markdown; the team may add a genuine human-evaluation appendix according to the manual.
