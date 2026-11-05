> Current workflows and permissions: [ROLE_WORKFLOW_GUIDE.md](ROLE_WORKFLOW_GUIDE.md). Current layout and commands: [README.md](../README.md). Earlier UI evidence below is historical.

# React + Redux frontend

Current operations increment: see [OPERATIONS_KNOWLEDGE_GUIDE.md](OPERATIONS_KNOWLEDGE_GUIDE.md). Knowledge base, provider onboarding, password changes and observability are now implemented; the verification notes below describe the earlier React-only increment.

This increment replaces the default authenticated portal with a React 19 / TypeScript application. Redux Toolkit and React Redux manage the authenticated session, selected company, scoped records, evaluation, explanation, filters and UI state. Python/SQLite APIs and the new ER-based domain model remain the data authority.

## Run the included build (zsh)

```zsh
cd ~/Downloads/Retail-Mesh-React-Redux-MVP
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-knowledge.txt
chmod +x quickstart.sh
./quickstart.sh
```

Open http://127.0.0.1:8000. Create the first local administrator and company, prepare the fictional scenario, then evaluate the rule. No default credentials or API key are packaged. Node is unnecessary for the included production build. Python 3.10+ is required; graph dependencies enable Knowledge explanations and RDF exports.

## Develop the frontend

Use Node 22.12+ and npm. In a second terminal, with the Python application running on port 8000:

```zsh
cd src/ui/react
npm ci
npm run dev
```

Open the Vite URL printed in the terminal. Its loopback-only development proxy forwards `/api` and normalizes Origin to the local Python server. Keep this development proxy local. The production application serves the build and API from the same origin.

```zsh
npm test
npm run build
```

The build writes `src/ui/react-dist/` from the project root. Keep this directory when distributing the Python application. Rebuilding requires npm dependencies and network access for the initial install. The lockfile records resolved dependencies. Run `npx prettier --write src` within frontend to format source changes.

## Screens and behavior

- Overview: derived counts, loaded qualified awards grouped by currency, sale/service/rental journey and next action.
- Vehicle activities: searchable, type-filtered records with explicit source references.
- Incentives: saved evaluations, qualification checks, frozen evidence and beneficiary amounts.
- Provider network: recorded operations and loaded awards within the active membership scope.
- Knowledge & AI: recorded decision explanation, graph exports, bounded questions and optional AI narration.
- Team members: administrator-only local member creation and named access-revocation confirmation.
- Workspace settings: company context, role boundaries and narration configuration.

The application includes loading, empty, failure and retry states, keyboard-capable Radix controls, visible focus, a skip link, a mobile navigation drawer, local IBM Plex fonts and reduced-motion handling. Dense tables scroll inside their containers on narrow screens. GSAP is limited to scoped interaction feedback with hook/context cleanup.

Passwords stay in form-local requests, outside Redux state/actions. Redux DevTools are disabled and state is not persisted in localStorage. Company changes clear scoped records immediately; request IDs and company/run checks discard stale responses. Logout, expired sessions, membership removal and role changes clear prior scoped data. Server-side authorization remains mandatory.

## Verification

Observed November 4, 2026:

- 22 frontend tests passed: 12 Redux tests and 10 component tests.
- TypeScript and Vite production build passed; vendor and motion chunks split.
- 99 backend unit tests passed.
- Authenticated HTTP smoke passed: company isolation, role checks, CSRF/origin/host checks, revocation and unconfigured AI fallback.
- React HTTP smoke passed: root shell, CSP, JS/CSS/font MIME types and encoded traversal denial.
- Taste source lint: 0 FAIL, 4 WARN. These flag a run-ID label, monospace record references and two actual overlay shadows; they are retained intentionally.

Browser verification remains pending. Local Chromium failed with an OS socket restriction; a separate static React preview could not be opened because the cloud browser disallows file URLs. No live browser, responsive rendering, visual accessibility or screenshot approval is claimed. Component tests run in jsdom and do not substitute for those checks. Test logs are in `doc/react-verification/`.

## Boundaries

This is a local MVP. Transaction records are fictional; public real-world reference facts remain separately sourced in `REAL_WORLD_REFERENCE_DATA.md`. Public dealer self-registration, arbitrary sales/rental entry, payments, production hosting and ongoing graph synchronization are roadmap work. The existing course CRUD screen remains available only with `--legacy-demo` and does not use this React redesign. The historical course report and old screenshots are not evidence of the React UI. The user-supplied new ER remains authoritative; the repository's old ER was not used to redesign the domain.

OpenAI narration needs server-side configuration and per-request opt-in; no live model call was tested. 21st.dev generation was unavailable without its API key. See `UI_DESIGN_NOTES.md` for design-resource provenance and limitations.
