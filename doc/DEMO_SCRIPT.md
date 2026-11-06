# Repeatable evaluation script (approximately five minutes)

1. Extract the submission ZIP and start `./quickstart.sh --db data/marker-demo.db` (Windows: `quickstart.bat --db data/marker-demo.db`). Use a new filename for a fresh run; existing databases are preserved.
2. Open http://127.0.0.1:8000 and inspect Provider. Add CA-BC / MARKER-001 / Marker Demo. Save and search MARKER-001. The generated Id should appear.
3. Edit that record to Marker Demo Updated. Save; the same Id must remain. Delete it and search again; there should be no matching records.
4. Clear search and try deleting Dealer A. The application must show a foreign-key error and retain the record.
5. Inspect Customer journey: three rows, original VIN in sale/service, different VIN in rental, explicit replacement link to SVC-001.
6. Inspect Provider metrics: one service measurement, one source contribution.
7. Inspect Award ledger: 100 CAD assigned to Dealer A, 10 POINT to Provider C. Explain why another provider contributing evidence does not receive the sale award.
8. Inspect EventEvaluationIdentity and CustomerIdentityLink: account assertions are local and explicit; stored outcome, timestamp and evidence reference are retained in the evaluation evidence.
9. Try editing an accepted identity evidence row: an immutable-evidence error should appear. Cancel the form.
10. Inspect Integrity audit: zero problems. Stop the app and execute `python3 -m unittest discover -s tests -v`; expect 41 passing isolated tests.

Capture readable screenshots at steps 2–4 and 5–7; do not replace actual evidence with the supplied schematic. The optional Playwright script automates a synthetic provider flow and screenshot capture on a machine with a working Chromium runtime.
