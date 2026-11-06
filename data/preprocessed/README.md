# Prepared data

`RetailMesh_Reviewed_CSV_Data.zip` and `csv/` contain the reviewed 574-domain-row synthetic dataset. `retail_mesh.db` is its clean ingested runtime database, with 56 tables and zero shipped user accounts. `quality/` contains both audit reports, source/target hashes, a field-level change log and import mapping/counts. `knowledge_exports/` contains company-specific OKF snapshots (IDs 1 and 2). See `../../doc/DATA_REVIEW.md` for decisions, rates, thresholds and regeneration commands. Do not treat these authored fixtures as actual customer transactions or settled incentives.
