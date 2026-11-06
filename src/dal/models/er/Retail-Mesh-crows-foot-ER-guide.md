# Retail-Mesh: earlier layout with crow’s-foot endpoints

This version retains the earlier complete entity-box map: 26 entities, 42 named relationships, relationship-attribute ovals and the total/disjoint ISA triangle. Cardinality numbers on the relationship connections have been replaced with the requested endpoint symbols.

| Meaning | Endpoint symbol |
| --- | --- |
| 0..1 | Circle plus one bar |
| 1..1 | Two bars |
| 0..N | Circle plus crow’s foot |
| 1..N | One bar plus crow’s foot |

The symbol sits beside the entity being counted. For example, the Owns relationship has exactly-one at ParentCompany and zero-or-many at IncentiveProgram. This means a company can own zero or many programs and each program has one parent company.

The bar is included explicitly with the 1..N crow’s foot to establish the minimum of one. A bare crow’s foot alone expresses many without explicitly showing that minimum. See the [draw.io crow’s-foot notation guide](https://www.drawio.com/docs/tutorials/crows-foot-notation/).

The editable draw.io file uses native ER endpoint markers. SVG, PNG and the self-contained HTML viewer display the matching symbols. Numeric cardinalities appear only in the legend explaining the symbols, not as relationship-end labels.

The custom identity suffixes are not displayed. Underlined entity references in the compact key lists contribute the referenced entity’s complete business key; they do not introduce generated surrogate identifiers. The underlying agreed keys, source-record assumptions and business constraints are unchanged.

This is the requested presentation using the earlier entity boxes and named relationship diamonds with crow’s-foot endpoints. It should not be described as a pure Chen diagram.

## Files

- Retail-Mesh-crows-foot-ER.html: zoomable complete map; includes entity search and Show ISA.
- Retail-Mesh-crows-foot-ER.drawio: editable single-page diagram.
- Retail-Mesh-crows-foot-ER.svg: scalable complete diagram.
- Retail-Mesh-crows-foot-ER.png: high-resolution preview.
- Retail-Mesh-crows-foot-ER-validation.json: endpoint and model-fidelity checks.

All 84 entity endpoints were checked against the business model: 33 exactly-one, 3 zero-or-one, 46 zero-or-many and 2 one-or-many. Entity names, displayed keys, attributes, named relationships and ISA were preserved. The viewer controls passed simulated-DOM checks; live browser rendering is not claimed.

Business-model digest:

53a2536814273d541c82970a694439bf52b8f1e4c65f3cda41bcb804fe02bd73
