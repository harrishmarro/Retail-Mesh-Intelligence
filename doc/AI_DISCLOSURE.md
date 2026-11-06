# AI assistance and required human evaluation

ChatGPT/Codex assisted with ER-to-relational mapping, Python/SQL/HTML/JavaScript implementation, synthetic fixtures, automated tests, documentation and report drafting on November 3, 2026. The attached new ER package was the design authority. The old repository diagram was excluded.

## Checks actually performed

- Extracted all 26 entity definitions and business keys from the supplied draw.io file.
- Mapped 42 named relationships and eight many-to-many relationships to 34 relations.
- Executed schema, integrity triggers and seed on fresh SQLite databases.
- Passed 41 isolated automated database/application tests and an HTTP smoke test.
- Compiled the ACM-style report and checked its exact three-page length and rendered layout.
- Attempted browser execution. The browser download initially failed; an official Chrome runtime was obtained but could not start due to process/socket restrictions. Consequently, no live browser screenshots or visual CRUD verification are claimed. The schematic in the report is explicitly labelled.

## Critical observations for the team to evaluate

1. Surrogate Ids simplify references; mandatory UNIQUE constraints preserve the proposed natural identities. These business keys still need confirmation against actual source-system records.
2. Bidirectional deferred composite FKs enforce exactly one owned Sale/Rental/Service subtype. This requires atomic transactions and is more complex than a simple subtype table FK. Inspect the SQL and test rollback behavior independently.
3. Stable award keys use an unversioned rule; accepted evaluations retain the exact version. This prevents double awards but does not implement payment reversals or redemption histories.
4. Identity snapshots preserve the evidence used at insertion, while live identity links may later change. There is no automatic global-customer merge or arbitrary transitive identity inference.
5. Policy conditions and rewards are stored, not executed. Synthetic qualifications are manual fixtures. The team must not describe this as a complete automated incentive engine.
6. Program eligibility, enrollment windows and capability authorization need human assessment for arbitrary new evaluations. They are represented, not universally certified by this prototype.
7. SQLite NUMERIC and the local HTTP server are suitable for demonstration, not production financial accounting or internet deployment.

## Human evaluation — must be completed by the actual team

- Reviewer names and roles: **not supplied**.
- Independent reproduction environment and date: **not supplied**.
- Business-key validation against real records: **not performed here**.
- Team critique, corrections and acceptance/rejection of AI suggestions: **must be written by the team**.
- Substantive individual contributions and Git account associations: **must reflect actual work; no history has been fabricated**.

This document records AI assistance; it does not impersonate the required human evaluation.

## November 4 implementation increment

AI assistance also produced the fleet/automatic-incentive/RDF slice documented in FLEET_GRAPH_MVP.md. The combined suite passed 69 tests with optional knowledge dependencies installed. The CAD 150 outcome was calculated by the supported rule from recorded fictional evidence, and the 175-triple graph passed SHACL validation. This does not establish human review, real policy correctness, production tenant security or live LLM integration. The explanation feature uses deterministic SPARQL, not a remote AI model.

## Authenticated workspace increment

AI assisted with local authentication/authorization, portal UI, scoped demo isolation, security/API tests and an optional OpenAI Responses adapter. The adapter was tested with mock responses, not live credentials. No real API call, payment, human review or production security certification is claimed. The default portal requires accounts; the old unauthenticated UI is an explicit legacy mode.


## Operations and knowledge increment

AI assistance was used to implement and test the CSV importer, knowledge/OKF projection, provider review/activation, password changes, observability and React views. The supplied CSV archive is user-provided synthetic source data. Its recorded manual-review evaluations were preserved, not represented as AI or engine-generated decisions. Registry verification and invitation email delivery were not performed. The original course report remains historical; current implementation boundaries and observed checks are documented in OPERATIONS_KNOWLEDGE_GUIDE.md and operations-verification/.
