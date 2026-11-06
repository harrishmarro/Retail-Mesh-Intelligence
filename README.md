# Retail-Mesh Intelligence

## 1. Intro / overview

A vehicle retail, rental and service application for parent companies and their provider networks. React, TypeScript and Redux Toolkit power the portal; Python and SQLite implement accounts, company scopes, onboarding, incentive evidence and knowledge exports.

The **new uploaded ER model** in `src/dal/models/er/` is the design authority. The old repository ER is superseded. The original 34 domain relations are extended for the fleet engine, authentication and provider operations: **56 non-system tables** in the delivered database. This is a local coursework prototype.

The included database has **574 reviewed synthetic domain records**, two companies, seven providers and 35 activities, ingested from `data/preprocessed/RetailMesh_Reviewed_CSV_Data.zip`. The original 559-record input remains intact under `data/raw/`. No user accounts, passwords or API keys are preconfigured. See [data review](doc/DATA_REVIEW.md).

## 2. Illustrative sample

1. Start the app and create the first administrator with **Start with the 2 supplied companies** selected.
2. Choose a company. Inspect activities and recorded awards; cash and points stay separate.
3. In workspace settings, enable public provider signup and copy its separate signup URL. Add a CompanyOperator under Team members.
4. An applicant submits business, contact, outlet, capability, program and evidence details. No provider login is created yet.
5. The operator starts review, validates all three evidence checks and chooses **Changes needed**, **Rejected** or **Accepted**. Changes can be resubmitted through the private tracking page.
6. An accepted applicant sets a password through their private activation page, then signs in through the normal login page. They receive only their own provider dashboard, claims, assistant and concerns.
7. Providers request workspace access through concerns. Only administrators create workspaces; approval of a request never silently grants access.

[Role and workflow guide](doc/ROLE_WORKFLOW_GUIDE.md) covers permissions and activation. Administrators manage their assigned companies; operators have delegated review duties. Knowledge graph browsing and OKF export are available to administrators, operators and analysts. Providers use a scoped incentive chatbot and cannot access the graph.

## 3. Prerequisites / package requirements

Python 3.10+ with SQLite and `venv`. Install `requirements.txt`, which includes graph validation and timezone dependencies. Node.js and npm are needed only to rebuild the included React production build. Frontend versions are locked in `src/ui/react/package-lock.json`.

## 4. Installation guide

From the extracted project folder, in zsh or bash:

```zsh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
chmod +x quickstart.sh
./quickstart.sh
```

Windows: create/activate a Python virtual environment, install the same requirements, then run `quickstart.bat`. The server binds to `127.0.0.1`; open [http://127.0.0.1:8000](http://127.0.0.1:8000). Use `./quickstart.sh --port 8001` for another port. Existing databases are never overwritten at startup. A new custom `--db` path uses the historical small engine fixture; to recreate the reviewed dataset use the explicit builder below.

## 5. Quickstart / reproduction

The default database is `data/preprocessed/retail_mesh.db`. First setup claims the two unowned sample companies for the first administrator. Normal sign-in serves administrators, operators, analysts and accepted providers. Administrators can grant another company administrator access through Team members.

```zsh
# Reproduce reviewed CSVs and audit evidence without modifying raw input
python3 scripts/prepare_reviewed_data.py
# Build a NEW reviewed database; refuses an existing output path
python3 scripts/build_reviewed_database.py --output data/preprocessed/reproduced.db
# Run independently against that database
python3 src/main.py --db data/preprocessed/reproduced.db --port 8001
# Tests use disposable databases
python3 -m unittest discover -s tests -v
# Optional frontend development
cd src/ui/react
npm ci
npm test -- --run
npm run build
```

The live knowledge base is a read-only relational projection, available without an incentive-engine run. Company OKF snapshots are included in `data/preprocessed/knowledge_exports/`. Each contains JSON-LD, Turtle, schema, vocabulary, SHACL validation and a hashed manifest. [Semantic contract](src/dal/models/semantic/okf/README.md) explains agent consumption and provenance. “OKF” is the project's Open Knowledge Format, not a claimed external certification.

| Location | Purpose |
| --- | --- |
| `data/raw/` | Unmodified input ZIP, original DB snapshot, previous exports |
| `data/preprocessed/` | Reviewed CSVs, ingested DB, audits and company OKF snapshots |
| `src/libs/` | Notes on customized external libraries; none currently forked |
| `src/cmn/` | Shared accounts, migrations, dates and paths |
| `src/ui/react/`, `src/ui/react-dist/` | React/Redux source and included build |
| `src/ui/portal.py` | Authenticated/public HTTP routes |
| `src/biz/` | Onboarding, claims, concerns, CSV preparation, knowledge and incentive logic |
| `src/dal/` | Database access and models |
| `src/dal/models/er/` | New conceptual ER artifacts |
| `src/dal/models/relational/sql/` | DDL, migrations and DML examples |
| `src/dal/models/semantic/` | Semantic vocabulary, shapes and interchange contract |
| `src/main.py` | Main entry point |
| `doc/` | Instructions, reference image, reports and evidence |
| `scripts/`, `tests/` | Reproduction, import/export and checks |

Claims are review requests; approval does not issue an award or payment. The provider assistant deterministically explains enrolled rules and own claim status, with sources. Optional administrator/analyst AI narration is configuration-dependent; no live external model call is claimed. Registration checks are recorded operator validation, not an external identity-verification integration. Email delivery, forgotten-password recovery and settlement are future work. Existing users can change passwords and revoke prior sessions. Tracking and activation links are private credentials. Historical reports under `doc/` describe their original milestones; this README and the new guides describe the current build.

## 6. Citation

Use [CITATION.cff](CITATION.cff) and the project repository: [Retail-Mesh-Intelligence](https://github.com/harrishmarro/Retail-Mesh-Intelligence). Add verified team authors and the final release identifier before academic submission; no DOI or individual contributions are invented. [AI disclosure](doc/AI_DISCLOSURE.md) and [submission checklist](doc/SUBMISSION_CHECKLIST.md) retain the coursework requirements.

## 7. License

New implementation code is covered by [LICENSE](LICENSE) / [LICENSE-implementation](LICENSE-implementation). Existing repository content, professor references and third-party assets retain their own terms. Synthetic transaction data is for demonstration; [real-world references](doc/REAL_WORLD_REFERENCE_DATA.md) are explanatory background, not real customer transactions.
