# Retail-Mesh Open Knowledge Format (OKF), version 1.0.0

This project-specific interchange contract uses standard JSON-LD 1.1, RDF/Turtle, JSON Schema and SHACL. “OKF” here means Open Knowledge Format for this project; it does not claim certification against an external OKF standard or confer an open-data license.

The live knowledge base is a read-only projection of the relational source of truth. Open **Knowledge base** in the portal, search any source record, follow its relations, and download the active company's OKF ZIP. It is available before any automated incentive run. Graph access is limited to CompanyAdmin, CompanyOperator and Analyst. Providers use the restricted policy chatbot, claims and concerns; they cannot browse or export the graph.

Each export is an explicit snapshot, not a continuously synchronized graph server. `manifest.json` lists scope, schema version and SHA-256 for each file. `records.jsonld` contains the graph plus provenance metadata; `graph.ttl` contains the same record graph. Never combine different company exports without explicit access authorization. The example.org namespace is a project vocabulary, not a resolvable production registry.

`rm:sourceTable` and `rm:sourceRowId` identify live database records. `rm:sourceCsvId` retains the uploaded CSV ID after database ID remapping; `rm:importSha256` identifies the import. Blank CSV fields become NULL. Contact data, auth tables and review applications are omitted from exports. Shared provider master records can occur in multiple company projections, but each URI is company-scoped.

Reviewed sample Event/Period decisions are calculated offline by the reproducible preparation script under explicit sample policies, separately from online IncentiveRun records and real business approvals. Original input decisions remain archived. Their financial component `BenefitValue` uses the stated unit directly; it is not an integer minor-unit amount. No fleet history is fabricated from CSV sale records. The original journey overview is a derived report and is reproduced as the JourneyOverview SQL view, not inserted as an additional stored domain table.
