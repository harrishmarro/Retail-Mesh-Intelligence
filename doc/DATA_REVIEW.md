# Reviewed synthetic dataset

The supplied data contained plausible entities but inconsistent evaluation timing, evidence and benefits. The original archive is preserved byte-for-byte at `data/raw/RetailMesh_CSV_Files.zip`. `data/raw/original_import_snapshot.db` preserves the prior imported database. The reviewed archive and ingested default DB are under `data/preprocessed/`.

| Check | Original | Reviewed |
| --- | --- | --- |
| Domain rows across 34 relations | 559 | 574 |
| Companies / providers / activities | 2 / 7 / 35 | 2 / 7 / 35 |
| Semantic errors under sample checks | 23 | 0 |
| Warnings | 53 | 0 |
| Informational findings | 34 | 0 |
| Performance measurements reconciled | 105 | 105 |

All 105 original measurements reconcile their original metric definitions; the audit does not claim otherwise. The raw RecordedAt-before-completion findings are informational because creation and final recording can differ. The reviewed fixture explicitly records completion snapshots five minutes after the activity end.

## Findings and preparation decisions

- Four qualified event decisions occurred before cited source completion, measurement or identity availability. Evaluation dates now follow evidence availability.
- Eight of nine original award component sets differed from their declared policies. Reviewed awards use the explicit sample benefit definitions, keeping CAD and points separate.
- Event identity snapshots were missing; a revoked rental proof was still treated as qualified. Verified direct snapshots are added when valid. The revoked rental and pending service proof now lead to rejected events. Rejections cite the actual source links in their reason; the schema only stores Verified identity snapshots, so no false verification is inserted.
- Seven period identity snapshots were unrelated to cited Q3 activities. Their evidence now corresponds to the period population.
- Thirty-five activity starts fell outside the documented local business hours when parsed as UTC. For this synthetic correction only, original clock readings are assumed to be intended Vancouver local time, then converted to UTC with DST. This is a documented modeling assumption, not proof of the original author's intent.
- Ten replacement rental returns greatly exceeded service completion without an extension reason. The sample now uses service start plus 30 minutes for collection and service end plus one hour for return. Illustrative daily CAD 89/94 rates use ceiling elapsed 24-hour units. These are authored demonstration rates, not market quotations.
- Unsupported charging-specific descriptions and a vehicle-class description were replaced with consistent generic/hybrid/safety service descriptions. Vehicle identities are preserved.
- Period policies now state measurable criteria: sales at least one completion and CAD 50,000 sales; rental at least two replacement rentals and four billable days; service at least two completions. Sales benefit is CAD 250 plus 500 points; qualifying rental/service benefit is 500 points. Company event benefits are CAD 150/175 plus 300 points.

Reviewed event outcomes: three qualified, two rejected. Period outcomes: six qualified, one rejected. The open CAD 72 rental quote stays provisional and is excluded from completed activity/revenue metrics. These are offline synthetic fixture decisions, not real approvals, live engine runs or payment settlements.

The field-level change log records 277 changed source rows, including additions. Records are regenerated deterministically; the derived JourneyOverview is rebuilt from owning records, not ingested as another domain table.

## Reproduce and inspect

```zsh
python3 scripts/prepare_reviewed_data.py
python3 scripts/build_reviewed_database.py --output data/preprocessed/reproduced.db
```

The builder refuses to overwrite an existing database, starts without historical seed data, imports the reviewed archive and validates foreign keys. The included DB has 56 tables and zero user accounts. Review `data/preprocessed/quality/raw_audit.json`, `reviewed_audit.json`, `change_log.json` and `import-result.json`. The change log includes original/prepared SHA-256 values and explicit assumptions.

`data/preprocessed/csv/` exposes the same reviewed CSV files for examination. `knowledge_exports/` contains company-specific validated OKF snapshots with source CSV IDs and import provenance. The public reference facts in `REAL_WORLD_REFERENCE_DATA.md` are background only; no supplied synthetic customer/vehicle transaction is relabeled real-world data.
