> Current update: `OPERATIONS_KNOWLEDGE_GUIDE.md` adds CSV company ownership, a visible knowledge base/OKF, provider review/activation, password changes and admin observability. This document records the earlier workspace increment.

# Authenticated workspaces and optional AI narration

Implemented November 4, 2026. This increment builds on the fleet/incentive/RDF slice.

## Run in zsh

From the extracted `Retail-Mesh-Workspaces-AI-MVP` directory:

```zsh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-knowledge.txt
chmod +x quickstart.sh
./quickstart.sh
```

Open http://127.0.0.1:8000 . The default application now opens the authenticated company portal. On the first run, create a local administrator, choose a password of 12-256 characters, and enter your company identity. For a demo use explicitly fictional values, for example a company named `My Demo Company (fictional)`, jurisdiction `DEMO`, and registration `SYNTHETIC-MY-DEMO-001`. No default account/password is shipped.

First setup creates a new company and administrator. It does not give that user access to the older companies already present in the baseline seed. Actual organizational identity/email verification is not performed by this local setup.

After signing in:

1. Select your company workspace.
2. Click **Prepare fictional scenario in this company**.
3. Click **Evaluate incentive**. The result should qualify for CAD 150.00 with 12 pre-sale fleet vehicles and six passed checks.
4. Inspect a run, download validated Turtle/JSON-LD, or ask about its result.
5. Add an Analyst or Provider member in the local member form to exercise roles. No email is sent. New local users use the initial password entered by the administrator; existing users keep their existing password.
6. Use **Create another company workspace** to create an independent network and repeat the scenario. Its activities, fleet assignments and awards are separate.

The base portal, sessions and evaluator use only the Python standard library. Optional RDF/SHACL packages are needed for graph export and detailed graph explanations.

## Access rules actually implemented

| Role | Allowed | Denied |
|---|---|---|
| CompanyAdmin | Own company providers/demo activities, complete evidence/runs, graph exports, scenario preparation, evaluation, membership administration, audit history | Other companies without explicit membership |
| Analyst | Own company read views, run evidence, graph exports and explanations | Preparing data, evaluating rules or managing members |
| Provider | Own provider activities and beneficiary award summaries within an authorized company | Other providers' activities/awards, full cross-provider evidence, graph exports, membership management, evaluation and external AI narration |

A membership is checked on every request; the selected company ID and supplied role are not trusted. Provider authorization must also be active. Revocation takes effect for subsequent requests even if a valid login session remains. Signing out revokes the server-side session, so copying the old cookie does not restore it.

Portal activity scope is explicitly the current company's demo source namespace. The portal does not attempt to expose every pre-existing generic table with inferred tenant ownership. General company-scoped CRUD/import for real sales, rental, service, inventory and enrollment still needs explicit ownership mapping and additional workflows.

## Session and password behavior

- PBKDF2-HMAC-SHA256 with 600,000 iterations and random salts. Plaintext passwords are never persisted.
- 256-bit random session tokens; only their SHA-256 hashes are stored server-side.
- Eight-hour server-side expiry, active-user checks and explicit session revocation.
- On POSIX systems, the database file is restricted to its owner (mode 0600) at startup.
- HttpOnly, SameSite=Strict cookies and session-bound CSRF tokens for authenticated changes.
- Same-origin/Host checks, nonces for portal scripts, frame denial and no-store responses.
- Account-based sign-in throttling after six failed attempts within 15 minutes.
- Immutable workspace audit records for membership, scenario/evaluation and explanation events. Passwords, API keys and full questions are not logged in those records.

This server binds to 127.0.0.1 and serves local HTTP. Its local session cookie is not marked Secure because it is not an HTTPS deployment. Public hosting is not implemented or authorized by this package. Production requires HTTPS, secure cookie configuration, an identity-provider/password recovery strategy, stronger operational controls and independent security review. MFA, verified company/email ownership, password reset/rotation UI and production account recovery are not implemented.

## Optional OpenAI narration

The deterministic graph answer, calculated monetary value and sources remain authoritative. Optional model text is returned in a separate `ai_narrative` field and displayed in a separately labelled panel. The model has no SQL/SPARQL execution tools, financial write tools or database connection. Its response does not replace the recorded result or source list.

No actual model request was made during preparation. The request/response adapter, reduced payload, opt-in and error fallback were tested with mocks. Live success, model availability, latency and answer quality still need validation using your own API configuration.

To enable on your own computer, with a model ID available to your API account:

```zsh
read -rs 'OPENAI_API_KEY?OpenAI API key: '
export OPENAI_API_KEY
print
export RETAIL_MESH_AI_MODEL='YOUR_AVAILABLE_MODEL_ID'
./quickstart.sh
```

Do not put a key in the source, a ZIP, the chat, browser form or shell history. The app does not load `.env` automatically. Only the presence of a configured key/model and the model ID are returned to the UI; the key is never returned.

When configured, CompanyAdmin/Analyst users can explicitly check **Use optional OpenAI narration** for a request. The UI states that the question and a reduced authorized evidence summary will be sent to OpenAI and API charges may apply. The checkbox is off by default and resets when switching workspaces/runs. Providers cannot invoke external narration.

The adapter sends a fixed-endpoint Responses API request with `store: false`, a bounded output size and no tools. The payload contains the question, deterministic answer, check summaries and source identifiers. It excludes the complete snapshot, customer account links, emails, VINs and credentials. `store: false` requests response non-storage; this is not a claim of universal zero retention or a replacement for reviewing the provider's data terms.

AI wording can still be wrong. The UI presents the authoritative evidence answer beside it. On missing configuration, timeout, API/network error or incomplete text, the deterministic answer remains available and the response reports `not_configured` or `unavailable`. No different model is silently substituted.

Official API documentation used:

- https://developers.openai.com/api/docs/guides/text
- https://developers.openai.com/api/reference/resources/responses/methods/create

Security design references:

- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

## Data migration and compatibility

Startup applies `09_fleet_engine.sql` followed by `10_workspaces.sql`. Both are additive/idempotent migrations and do not reset an existing database. The five new account/security tables are AppUser, CompanyMembership, AuthSession, LoginAttempt and WorkspaceAuditEvent. There are now **43 application relations** including migration/session/audit tables: 34 baseline + four fleet/engine relations + five workspace/security relations.

Public catalogue models can be reused across demo companies, but provider legal identities, outlet/customer records, vehicles, source namespaces, fleets, rule programs and awards are created/scoped separately. The package ships only the old synthetic baseline database, with no administrator accounts, passwords, sessions or API credentials. Local setup creates credentials only on your computer.

The old course UI and database-wide CRUD API are disabled in default portal mode. To run that explicitly unauthenticated, loopback-only educational interface:

```zsh
./quickstart.sh --legacy-demo
```

Do not treat this option as a multi-tenant system. Legacy smoke scripts pass this flag intentionally; the new workspace acceptance test runs default authenticated mode. The old 34-relation report remains a baseline artifact, not a complete report for the expanded application.

## Verification

```zsh
python3 -m unittest discover -s tests -v
python3 scripts/workspace_http_smoke.py
python3 scripts/http_smoke.py
python3 scripts/fleet_http_smoke.py
```

The complete configured suite passed **99 tests**. Recorded results are in workspace-tests.txt and workspace-http-tests.txt. Tests cover password/session handling, throttle, one-time setup, identity collision, separate company demos, cross-company denial, analyst write denial, provider redaction, role revocation, logout replay, CSRF/origin/Host checks, legacy-route denial, optional AI opt-in and mocked payload/fallback behavior. A live browser could not run in the preparation environment; no visual browser verification or screenshots are claimed.

## Next implementation priorities

Company-scoped provider applications/approval, production transaction entry/import, inventory/reservations, expanded rules, correction/settlement workflow, persistent graph projection, policy-document retrieval, and scored live-model evaluation remain future increments. These authentication and API components are a local development foundation, not a production certification.
