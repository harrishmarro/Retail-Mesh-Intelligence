import sys,tempfile,unittest,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import initialize,connect,MODELS,SQL
from biz.service import mutate
class RelationalTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.db';initialize(self.path);self.c=connect(self.path)
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def reject(self,sql,args=()):
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:self.c.execute(sql,args)
 def test_all_34_relations_seeded(self):
  self.assertEqual(len(MODELS),34)
  for t in MODELS:self.assertGreater(self.c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0],0,t)
 def test_foreign_keys(self):self.assertEqual(self.c.execute('PRAGMA foreign_keys').fetchone()[0],1);self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_integrity(self):self.assertEqual(self.c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
 def test_candidate_key(self):self.reject("INSERT INTO Provider(RegistrationJurisdiction,BusinessRegistrationNumber,LegalName) SELECT RegistrationJurisdiction,BusinessRegistrationNumber,'duplicate' FROM Provider WHERE Id=1")
 def test_null_key(self):self.reject("INSERT INTO Provider(RegistrationJurisdiction,BusinessRegistrationNumber,LegalName) VALUES(NULL,'X','X')")
 def test_empty_key(self):self.reject("INSERT INTO Provider(RegistrationJurisdiction,BusinessRegistrationNumber,LegalName) VALUES('CA','  ','X')")
 def test_invalid_reference(self):self.reject("INSERT INTO Outlet(ProviderId,ExistingOutletReference,OutletName,Address) VALUES(999,'X','X','X')")
 def test_restrict_parent_deletion(self):self.reject('DELETE FROM Provider WHERE Id=1')
 def test_crud(self):
  d=dict(RegistrationJurisdiction='CA-BC',BusinessRegistrationNumber='TEST-CRUD',LegalName='Test')
  id=mutate(self.c,'Provider',d);self.assertGreater(id,3)
  mutate(self.c,'Provider',dict(LegalName='Edited'),id);self.assertEqual(self.c.execute('SELECT LegalName FROM Provider WHERE Id=?',(id,)).fetchone()[0],'Edited')
  mutate(self.c,'Provider',row_id=id,operation='delete');self.assertIsNone(self.c.execute('SELECT Id FROM Provider WHERE Id=?',(id,)).fetchone())
 def test_sql_injection_is_data(self):
  id=mutate(self.c,'Provider',dict(RegistrationJurisdiction='CA',BusinessRegistrationNumber="X'); DROP TABLE Provider;--",LegalName='Injection fixture'))
  self.assertTrue(self.c.execute('SELECT Id FROM Provider WHERE Id=?',(id,)).fetchone())
 def test_table_allowlist(self):
  with self.assertRaises(ValueError):mutate(self.c,'Provider; DROP TABLE Provider',{})
 def test_invalid_timestamp(self):
  with self.assertRaises(ValueError):mutate(self.c,'VehicleActivity',dict(ActivityKind='Sale',StartedAt='2026-99-99'),None)
 def test_nonfinite_number(self):
  with self.assertRaises(ValueError):mutate(self.c,'Sale',dict(SalePrice='NaN'),1)
 def test_rule_overlap(self):self.reject("INSERT INTO RuleVersion(IncentiveRuleId,EffectiveFrom,ConditionExpression,RewardSpecification) VALUES(1,'2026-06-01','x','x')")
 def test_bad_interval(self):self.reject("INSERT INTO ProgramEnrollment(IncentiveProgramId,ProviderId,ValidFrom,ValidTo,EnrollmentStatus) VALUES(1,1,'2027-01-01','2026-01-01','Active')")
 def test_identity_reverse_duplicate(self):self.reject("INSERT INTO CustomerIdentityLink(AccountAId,AccountBId,VerificationStatus,VerificationMethod,EvidenceReference) VALUES(2,1,'Pending','x','x')")
 def test_identity_self(self):self.reject("INSERT INTO CustomerIdentityLink(AccountAId,AccountBId,VerificationStatus,VerificationMethod,EvidenceReference) VALUES(1,1,'Pending','x','x')")
 def test_identity_verified_requires_timestamp(self):self.reject("INSERT INTO CustomerIdentityLink(AccountAId,AccountBId,VerificationStatus,VerificationMethod,EvidenceReference) VALUES(1,2,'Verified','x','x')")
 def test_subtype_totality(self):self.reject("INSERT INTO VehicleActivity(IssuingOutletId,SourceNamespace,ActivityKind,OfficialActivityReference,ActivityStatus,StartedAt,RecordedAt,CustomerAccountId,VehicleId) VALUES(1,'test','Sale','T','Open','2026-10-01T00:00:00Z','2026-10-01T00:00:00Z',1,1)")
 def test_atomic_activity(self):
  d=dict(IssuingOutletId=1,SourceNamespace='test',ActivityKind='Sale',OfficialActivityReference='AUTO-1',ActivityStatus='Completed',StartedAt='2026-10-04T00:00:00Z',RecordedAt='2026-10-04T00:00:00Z',CustomerAccountId=1,VehicleId=1,_subtype=dict(SalePrice='10',Currency='CAD',CompletedAt='2026-10-04T00:00:00Z'))
  id=mutate(self.c,'VehicleActivity',d);r=self.c.execute('SELECT SaleId FROM VehicleActivity WHERE Id=?',(id,)).fetchone();self.assertIsNotNone(r[0])
  mutate(self.c,'VehicleActivity',row_id=id,operation='delete');self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_activity_failure_rolls_back(self):
  before=self.c.execute('SELECT COUNT(*) FROM VehicleActivity').fetchone()[0]
  d=dict(IssuingOutletId=1,SourceNamespace='test',ActivityKind='Sale',OfficialActivityReference='BAD',ActivityStatus='Completed',StartedAt='2026-10-04T00:00:00Z',RecordedAt='2026-10-04T00:00:00Z',CustomerAccountId=1,VehicleId=1,_subtype=dict(SalePrice='-1',Currency='CAD',CompletedAt='2026-10-04T00:00:00Z'))
  with self.assertRaises(sqlite3.IntegrityError):mutate(self.c,'VehicleActivity',d)
  self.assertEqual(before,self.c.execute('SELECT COUNT(*) FROM VehicleActivity').fetchone()[0])
 def test_final_evaluation_immutable(self):self.reject("UPDATE EventEvaluation SET Result='Rejected' WHERE Id=1")
 def test_accepted_evidence_immutable(self):self.reject("UPDATE EventEvaluationIdentity SET EvidenceReferenceUsed='changed' WHERE Id=1")
 def test_source_evidence_immutable(self):self.reject("UPDATE VehicleActivity SET ActivityStatus='Cancelled' WHERE Id=2")
 def test_award_wrong_beneficiary(self):self.reject("UPDATE PeriodAward SET ProviderId=1 WHERE Id=1")
 def test_event_award_wrong_rule(self):self.reject('UPDATE EventAward SET IncentiveRuleId=2 WHERE Id=1')
 def test_component_minimum(self):self.reject('DELETE FROM EventAwardComponent WHERE Id=1')
 def test_journey_query(self):
  r=[dict(x) for x in self.c.execute((SQL/'04_journey.sql').read_text())];self.assertEqual(len(r),3);self.assertEqual(r[2]['ReplacementForService'],'SVC-001');self.assertNotEqual(r[2]['VIN'],r[1]['VIN'])
 def test_metric_query(self):
  r=self.c.execute((SQL/'05_metrics.sql').read_text()).fetchone();self.assertEqual(r['ContributingActivities'],1);self.assertEqual(r['MeasuredValue'],1)
 def test_awards_units_and_beneficiary(self):
  r=[dict(x) for x in self.c.execute((SQL/'06_awards.sql').read_text())];self.assertEqual([(x['Beneficiary'],x['UnitCode']) for x in r],[('Dealer A','CAD'),('Provider C Service','POINT')])
 def test_audit(self):self.assertEqual(self.c.execute((SQL/'07_audit.sql').read_text()).fetchall(),[])
 def test_extra_wrong_subtype_rejected(self):
  self.reject("INSERT INTO Service(VehicleActivityId,ServiceType,Outcome,CompletedAt) VALUES(1,'X','X','2026-10-04T00:00:00Z')")
 def test_invalid_sql_date(self):self.reject("UPDATE ProgramEnrollment SET ValidFrom='2026-02-31' WHERE Id=1")
 def test_invalid_sql_timestamp(self):self.reject("UPDATE CustomerIdentityLink SET VerifiedAt='2026-02-31T00:00:00Z' WHERE Id=1")
 def test_metric_definition_immutable(self):self.reject("UPDATE MetricDefinitionVersion SET UnitCode='changed' WHERE Id=1")
 def test_contribution_immutable(self):self.reject("UPDATE MeasurementContribution SET ContributionRole='changed' WHERE Id=1")
 def test_cash_units_consistent(self):self.reject("UPDATE EventAwardComponent SET UnitCode='POINT' WHERE Id=1")
 def test_atomic_award(self):
  with self.c:self.c.execute("INSERT INTO EventEvaluation(VehicleActivityId,RuleVersionId,Result,Reason,QualificationDate,EvaluatedAt,DecisionEvidenceReference) VALUES(3,1,'Qualified','Synthetic unit-test fixture','2026-10-03','2026-11-01T00:00:00Z','test:award')")
  d=dict(VehicleActivityId=3,IncentiveRuleId=1,AwardStatus='Issued',IssuedAt='2026-11-01T00:00:00Z',AcceptedEvaluationId=2,_component=dict(RewardType='Cash',UnitScheme='ISO4217',UnitCode='CAD',BenefitValue=25,Currency='CAD',ValidFrom='2026-11-01'))
  id=mutate(self.c,'EventAward',d)
  r=self.c.execute('SELECT FirstComponentId FROM EventAward WHERE Id=?',(id,)).fetchone();self.assertIsNotNone(r[0]);self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_outlet_cannot_redirect_beneficiary(self):self.reject('UPDATE Outlet SET ProviderId=2 WHERE Id=1')
 def test_business_identity_immutable(self):self.reject("UPDATE Provider SET BusinessRegistrationNumber='NEW-IDENTITY' WHERE Id=1")
 def test_no_overwrite(self):
  with self.assertRaises(FileExistsError):initialize(self.path)
if __name__=='__main__':unittest.main(verbosity=2)
