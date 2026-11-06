# Fleet / incentive / graph MVP release

November 4, 2026. This is an executable product increment, not the completed multi-tenant production application.

## Verified outcome

- Cedar Logistics fictional historical fleet: **12** qualifying vehicles before sale.
- Supported rule: `fleet_journey_v1`, pinned to sale completion, minimum 10 pre-sale vehicles and qualifying service within 30 days with verified replacement rental.
- Automatically calculated entitlement: **15,000 CAD minor units = CAD 150.00**, beneficiary Maple Motors (fictional).
- Repeat/concurrent evaluation: one stable entitlement; original snapshot replayed.
- Changed source evidence after issuance: review flag; original award and evidence remain unchanged.
- RDF graph: **175 triples**, SHACL conforms.
- SPARQL results: one award/evidence row, one replacement-journey row, one fleet-count row reporting 12, and six evaluation-check rows.
- Tests: **69 passing** with RDF dependencies installed, plus baseline and fleet HTTP acceptance checks. Browser rendering remains unverified due to the previously documented environment restrictions.

See `fleet-tests.txt`, `fleet-http-tests.txt`, `http-test-results.txt`, and `fleet-demo-evidence/` for observed results. The evidence export is based on an actual evaluator execution, not a manually written CAD150 award fixture.

## Scope boundaries

A live LLM is **not** connected. The explanation assistant runs deterministic read-only SPARQL and returns record/rule/snapshot references. Company-context checks are present for this lab; authenticated multi-tenant roles are not yet implemented. RDF is exported from immutable snapshots on demand; an always-on triple store and outbox synchronization are not implemented. Payments, reversals and a general configurable rule editor remain future work.

The earlier 34-relation ACM report remains a baseline artifact. The new application adds Fleet, FleetVehicleAssignment, IncentiveRun and SchemaMigration (38 total relations) and needs a revised submission report if these extensions are submitted for the course.
