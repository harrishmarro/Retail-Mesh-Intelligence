# Local fleet lab API

This is a single-user loopback demonstration, without authentication. It is not a production tenant API. The company context comes from the server's fictional scenario; clients cannot choose another company through these routes.

All POST requests use JSON and the page's X-CSRF-Token header.

| Method | Route | Request / response |
|---|---|---|
| POST | /api/demo/prepare | Empty object; idempotently creates the fictional journey and returns context IDs. Does not preload an award. |
| POST | /api/demo/evaluate | Empty object; executes the rule for the prepared scenario, returning result, six checks, historical count, snapshot hash and issued award ID or rejection. |
| GET | /api/demo/status | Prepared context and up to 20 immutable run summaries. |
| GET | /api/demo/graph?run_id=1&format=turtle | Exports the selected company-scoped immutable run as validated Turtle. |
| GET | /api/demo/graph?run_id=1&format=json-ld | Same snapshot as validated JSON-LD. |
| POST | /api/demo/ask | `{"run_id":1,"question":"Why did Maple Motors receive CAD 150?"}`; returns deterministic graph-query explanation, source references and validation status. |

Run IDs depend on the database. Use the returned run_id rather than assuming 1. Graph export/query endpoints return an installation message if the optional knowledge dependencies are unavailable. Unknown/other-company runs are rejected; the original generic SQL CRUD allowlist does not expose direct IncentiveRun editing.
