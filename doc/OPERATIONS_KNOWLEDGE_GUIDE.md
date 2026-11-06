# Current operations and knowledge guide

The current release uses 56 non-system tables and 574 reviewed synthetic domain rows. Follow [START_HERE](../START_HERE.md), [role/workflow guide](ROLE_WORKFLOW_GUIDE.md), [data review](DATA_REVIEW.md) and the [OKF contract](../src/dal/models/semantic/okf/README.md).

Knowledge base reads the company-scoped relational source directly and can export JSON-LD/Turtle plus vocabulary, shapes, schema and a hashed manifest. It needs no engine demo run. Administrator, operator and analyst have access; provider access is denied at the API and UI. Provider incentive explanations use separate scoped policy retrieval.

## Existing installations

Back up the current SQLite file with the app stopped. Start the updated source against that file to apply additive migrations, including the CompanyOperator role and nullable public applicant creator. IDs and existing rows are preserved; constraint upgrades check foreign keys before commit. Current new provider applications use public signup. Existing history stays available.

The default import action selects the reviewed archive. Do not merge the revised sample into an existing original sample import expecting replacement: the importer preserves identities and rejects conflicting candidate keys. To compare versions safely, keep the existing database and build a separate reviewed database with `python3 scripts/build_reviewed_database.py --output data/preprocessed/review-comparison.db`, then run `python3 src/main.py --db data/preprocessed/review-comparison.db --port 8001`. Existing real edits are never silently overwritten.

Claims and concerns have immutable event/message histories, scoped reads and version checks. Review decisions require explicit reviewer notes. Acceptance creates provider access through private activation, not a preset password. Workspace access requests are reviewed conversations; only an administrator performs workspace creation and grants.

## Verification limits

Automated Python, React and local HTTP checks exercise the implemented workflows. Live external email, business verification, LLM calls, hosted deployment and browser screenshot verification are not claimed. Historical evidence in other milestone documents retains its original scope. Latest checks are in `doc/current-verification/`.
