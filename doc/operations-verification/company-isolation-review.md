# Company-isolation follow-up

A regression test reproduced an ambiguity in automatic CSV activity ownership when the same provider has valid authorizations from two companies. The importer now rejects such a batch and rolls back all inserted records, mappings and ownership rows. The supplied two-company dataset is unambiguous and remains imported unchanged.

The new test checks rejection and complete rollback, including preservation of all pre-existing domain rows. No frontend changes or external services are involved in this patch.
