# Workspace and AI-ready MVP release

November 4, 2026.

## Implemented

- Authenticated default portal with one-time local administrator/company setup.
- Salted password hashes, hashed expiring session tokens, logout revocation and sign-in throttling.
- CompanyAdmin, Analyst and Provider access rules checked per request.
- Separate company-specific fleet scenarios, activities, rules, awards and graph lookups.
- Provider-only activity/award summaries with full cross-provider evidence and graph export restricted to company readers.
- Immediate membership/provider-authorization revocation on subsequent requests.
- Session-bound CSRF, origin/Host checks, nonce-based portal scripts and immutable audit records.
- Optional OpenAI Responses narration of a reduced authorized evidence summary, with explicit per-request opt-in and deterministic fallback.
- Legacy database-wide CRUD disabled in default mode, available only via explicit --legacy-demo.

## Observed validation

- **99 tests passed**, including the original relational/fleet/graph checks and new session/authorization/AI-adapter tests.
- Default-mode HTTP acceptance passed two-company isolation, role denials, membership revocation, provider redaction, CSRF/origin/Host protection, old-cookie replay denial, disabled legacy routes and unconfigured AI fallback.
- Both legacy HTTP acceptance scripts still pass under their explicit legacy flag.
- Portal JavaScript syntax checked; no use of innerHTML for results or localStorage/sessionStorage for tokens.
- No live model request or live browser rendering verification was performed. Narration adapter tests used mocks and do not establish model availability, answer quality, latency or cost.

## Not yet implemented

Production identity verification, email/MFA/password recovery, publicly hosted HTTPS, general company-scoped transaction CRUD/import, provider application approval, persistent graph synchronization, policy-document retrieval, model quality evaluation, forecasting, settlement and reversals. The legacy 34-relation report remains historical; the expanded app now has 43 relations including infrastructure tables.

The ZIP includes no configured administrator, sessions or API credentials. Set up your own local account and see WORKSPACES_AI_MVP.md before enabling external narration.
