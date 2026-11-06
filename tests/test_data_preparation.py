"""Verify independent semantic review, reproducibility and the delivered dataset contract."""
import hashlib,json,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from biz.csv_import import read_archive
from biz.prepare_data import prepare
from biz.data_quality import review,index,metric_value
from cmn.dates import billable_days,intended_local_to_utc
from cmn.paths import RAW_DATA,PREPARED_CSV,DEFAULT_DB
from cmn.accounts import migrate
from dal.database import connect
from biz.knowledge.base import export_bundle

class PreparedDatasetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw,_=read_archive(RAW_DATA/'RetailMesh_CSV_Files.zip');cls.prepared,_=read_archive(PREPARED_CSV)
 def test_raw_findings_remain_visible_and_prepared_semantics_pass(self):
  raw=review(self.raw);after=review(self.prepared)
  self.assertEqual(raw['source_rows'],559);self.assertEqual(raw['counts']['error'],23);self.assertEqual(after['source_rows'],574);self.assertEqual(after['issues'],[])
 def test_archive_is_reproducible_and_raw_is_unchanged(self):
  original=RAW_DATA/'RetailMesh_CSV_Files.zip';before=hashlib.sha256(original.read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as temp:
   output=Path(temp)/'reviewed.zip';rows,log=prepare(original,output)
   self.assertEqual(rows,self.prepared);self.assertEqual(output.read_bytes(),PREPARED_CSV.read_bytes());self.assertEqual(len(log['changes']),277)
  self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),before)
 def test_all_measurements_reconcile_owning_completed_activities(self):
  d=index(self.prepared);self.assertEqual(len(self.prepared['PerformanceMeasurement']),105)
  from decimal import Decimal
  for measurement in self.prepared['PerformanceMeasurement']:
   self.assertEqual(Decimal(measurement['MeasuredValue']),metric_value(d,measurement),measurement['Id'])
 def test_declined_identity_evidence_is_not_forged_verified(self):
  outcomes={r['Id']:r['Result'] for r in self.prepared['EventEvaluation']};self.assertEqual(outcomes,{'1':'Qualified','2':'Qualified','3':'Qualified','4':'Rejected','5':'Rejected'})
  for row in self.prepared['EventEvaluationIdentity']:self.assertEqual(row['VerificationOutcomeUsed'],'Verified')
 def test_ceiling_days_and_vancouver_dst_are_explicit(self):
  self.assertEqual(billable_days('2026-07-01T12:00:00Z','2026-07-02T12:00:01Z'),2)
  self.assertEqual(intended_local_to_utc('2026-07-01T09:00:00Z'),'2026-07-01T16:00:00Z')
  self.assertEqual(intended_local_to_utc('2026-01-01T09:00:00Z'),'2026-01-01T17:00:00Z')
 def test_delivered_database_is_clean_and_foreign_keys_hold(self):
  c=connect(DEFAULT_DB)
  try:
   self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[]);self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
   self.assertEqual(c.execute('SELECT COUNT(*) FROM ImportedRecord').fetchone()[0],574);self.assertEqual(c.execute('SELECT COUNT(*) FROM AppUser').fetchone()[0],0)
   self.assertEqual(c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0],56)
  finally:c.close()
 def test_company_exports_are_valid_without_engine_runs(self):
  c=connect(DEFAULT_DB)
  try:
   self.assertEqual(c.execute('SELECT COUNT(*) FROM IncentiveRun').fetchone()[0],0)
   import io
   for cid in (1,2):
    with zipfile.ZipFile(io.BytesIO(export_bundle(c,cid,{'Role':'CompanyAdmin','ProviderId':None}))) as archive:
     self.assertIn('manifest.json',archive.namelist());self.assertIn('records.jsonld',archive.namelist())
  finally:c.close()
 def test_required_submission_directories_and_entrypoint_exist(self):
  for name in ('data/raw','data/preprocessed','src/libs','src/cmn','src/ui','src/biz','src/dal/models/er','src/dal/models/relational/sql','src/dal/models/semantic','doc','src/main.py','README.md','requirements.txt','CITATION.cff','LICENSE'):self.assertTrue((ROOT/name).exists(),name)
