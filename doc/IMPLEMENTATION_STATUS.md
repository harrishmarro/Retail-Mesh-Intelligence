# Current implementation and planned application

Updated November 4, 2026.

| Capability | Status in this ZIP |
|---|---|
| React + Redux frontend | Implemented, 22 jsdom component/store tests and production build passed; live visual/browser verification pending |
| Supplied CSV ingestion | 559 records imported into 34 domain tables; atomic/idempotent importer, ID provenance and company ownership |
| Visible company knowledge base and OKF | Source browser, relationship graph, scoped questions, JSON-LD/Turtle/schema/agent-guide export implemented |
| Provider validation and onboarding | Admin-initiated staged applications, evidence checks, approval and one-time activation implemented; external validation/email/self-registration remain planned |
| Password changes | Current-password verification, throttling, hash update and all-session revocation implemented; forgotten-password recovery remains planned |
| Multi-company observability | Admin-membership-scoped counts, benefits, onboarding, request telemetry and audit view implemented |
| New 26-entity ER mapped to 34 SQLite relations | Implemented |
| Local web forms, search, create/update/delete | Implemented; HTTP tested, live browser verification pending |
| Synthetic connected sale/service/replacement-rental journey | Implemented |
| Joined provider metrics, award ledger and integrity audit | Implemented |
| Foreign keys, business keys, subtype consistency, evidence protections | Implemented; 41 baseline relational tests plus fleet, security and operations tests (see verification logs) |
| Team author metadata in ACM report | Updated from the supplied presentation/background |
| Full product plan and proposed model extensions | Included in Application-Plan.md |
| Public real-world reference facts with sources | Included separately; not claimed as transaction data |
| Historical fleet model and presentation's 12-vehicle scenario | Implemented through Fleet/FleetVehicleAssignment and idempotent demo preparation |
| Automatic CAD 150 qualification and calculation | Implemented for the supported fleet_journey_v1 rule; baseline fixture awards remain separate |
| Multi-company authentication and isolation | Local account/session and company-role portal implemented for the scoped demo workflows; production identity/hosting and general CRUD ownership remain pending |
| RDF/OWL ontology and SPARQL | Demo ontology, validated RDF/JSON-LD snapshot export and SPARQL queries implemented; persistent graph synchronization/service still planned |
| Graph retrieval and explanation | Deterministic query explanations implemented; optional OpenAI narration adapter is configurable and mock-tested. Live-model validation and forecasting remain pending |
| Settlement, reversals and customer benefit redemption | Planned |

The application plan extends the current implementation; it does not claim those extensions have already been built. The current executable schema remains aligned to the new uploaded ER package. The obsolete repository ER diagram is excluded from this package.

See FLEET_GRAPH_MVP.md for exact extension boundaries. The course report remains the earlier baseline report.

Current increment: see OPERATIONS_KNOWLEDGE_GUIDE.md. Default mode is authenticated; the legacy course demo requires an explicit startup flag. Expanded schema has 50 non-system tables and a derived JourneyOverview view.
