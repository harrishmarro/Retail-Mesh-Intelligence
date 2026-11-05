import sys,tempfile,unittest,sqlite3,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import initialize,connect
from biz.demo import prepare
from biz.incentives import evaluate,get_run,migrate

GRAPH_DEPS_AVAILABLE=bool(importlib.util.find_spec('rdflib') and importlib.util.find_spec('pyshacl'))
class FleetEngineTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'fleet.db';initialize(self.path);self.c=connect(self.path);self.ctx=prepare(self.c)
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def run_rule(self):return evaluate(self.c,self.ctx['company_id'],self.ctx['activity_id'],self.ctx['rule_id'],evaluated_at='2026-11-04T12:00:00Z')
 def scalar(self,q,args=()):return self.c.execute(q,args).fetchone()[0]
 def subject(self):return self.c.execute('SELECT * FROM VehicleActivity WHERE Id=?',(self.ctx['activity_id'],)).fetchone()
 def test_qualifies_and_creates_150_cash(self):
  r=self.run_rule();self.assertEqual(r['result'],'Qualified');self.assertEqual(r['fleet_count_before_sale'],12);self.assertEqual(r['reward']['amount_minor'],15000)
  a=self.c.execute('SELECT * FROM EventAwardComponent WHERE EventAwardId=?',(r['event_award_id'],)).fetchone();self.assertEqual((a['BenefitValue'],a['Currency']),(150,'CAD'));self.assertIn('Maple Motors',r['beneficiary']);self.assertTrue(all(x['passed'] for x in r['checks']))
 def test_duplicate_run_does_not_duplicate_award(self):
  a=self.run_rule();b=self.run_rule();self.assertEqual(a['run_id'],b['run_id']);self.assertTrue(b['replayed']);self.assertFalse(b['review_required']);self.assertEqual(self.scalar('SELECT COUNT(*) FROM IncentiveRun'),1)
 def test_prepare_and_migration_idempotent(self):
  count=self.scalar('SELECT COUNT(*) FROM Vehicle');self.assertEqual(prepare(self.c)['company_id'],self.ctx['company_id']);migrate(self.c);self.assertEqual(self.scalar('SELECT COUNT(*) FROM Vehicle'),count)
 def test_low_historical_fleet_rejects(self):
  with self.c:self.c.execute("UPDATE FleetVehicleAssignment SET ValidFrom='2026-10-02T00:00:00Z' WHERE Id IN (SELECT Id FROM FleetVehicleAssignment ORDER BY Id LIMIT 4)")
  r=self.run_rule();self.assertEqual(r['fleet_count_before_sale'],8);self.assertEqual(r['result'],'Rejected');self.assertIsNone(r['event_award_id'])
 def test_newly_sold_vehicle_not_counted(self):self.assertEqual(self.run_rule()['fleet_count_before_sale'],12)
 def test_revoked_identity_rejects(self):
  with self.c:self.c.execute("UPDATE CustomerIdentityLink SET VerificationStatus='Revoked',RevokedAt='2026-11-01T00:00:00Z' WHERE AccountAId=?",(self.subject()['CustomerAccountId'],))
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_future_verification_not_accepted(self):
  with self.c:self.c.execute("UPDATE CustomerIdentityLink SET VerifiedAt='2027-01-01T00:00:00Z' WHERE AccountAId=?",(self.subject()['CustomerAccountId'],))
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_missing_enrollment_rejects(self):
  with self.c:self.c.execute("UPDATE ProgramEnrollment SET EnrollmentStatus='Suspended' WHERE IncentiveProgramId=(SELECT IncentiveProgramId FROM IncentiveRule WHERE Id=?)",(self.ctx['rule_id'],))
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_missing_rental_capability_rejects(self):
  with self.c:self.c.execute("UPDATE CapabilityAuthorization SET AuthorizationStatus='Suspended' WHERE ProviderAuthorizationId IN (SELECT Id FROM ProviderAuthorization WHERE ParentCompanyId=?) AND CapabilityId=(SELECT Id FROM Capability WHERE ExistingCapabilityDesignation='Rental')",(self.ctx['company_id'],))
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_rental_after_service_rejects(self):
  with self.c:self.c.execute("UPDATE Rental SET ReturnedAt='2026-10-13T00:00:00Z' WHERE VehicleActivityId=(SELECT Id FROM VehicleActivity WHERE SourceNamespace='demo.northstar' AND ActivityKind='Rental')")
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_service_outside_30_day_window_rejects(self):
  with self.c:self.c.execute("UPDATE Service SET CompletedAt='2026-11-02T17:00:00Z' WHERE VehicleActivityId=(SELECT Id FROM VehicleActivity WHERE SourceNamespace='demo.northstar' AND ActivityKind='Service')")
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_cancelled_sale_rejects(self):
  with self.c:self.c.execute("UPDATE VehicleActivity SET ActivityStatus='Cancelled' WHERE Id=?",(self.ctx['activity_id'],))
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_rejected_can_be_corrected_then_qualify(self):
  with self.c:self.c.execute("UPDATE ProgramEnrollment SET EnrollmentStatus='Suspended' WHERE IncentiveProgramId=(SELECT IncentiveProgramId FROM IncentiveRule WHERE Id=?)",(self.ctx['rule_id'],))
  first=self.run_rule()
  with self.c:self.c.execute("UPDATE ProgramEnrollment SET EnrollmentStatus='Active' WHERE IncentiveProgramId=(SELECT IncentiveProgramId FROM IncentiveRule WHERE Id=?)",(self.ctx['rule_id'],))
  second=self.run_rule();self.assertEqual(first['result'],'Rejected');self.assertEqual(second['result'],'Qualified');self.assertNotEqual(first['run_id'],second['run_id'])
 def test_snapshot_immutable_after_source_change(self):
  first=self.run_rule()
  with self.c:self.c.execute("UPDATE CustomerIdentityLink SET VerificationStatus='Revoked',RevokedAt='2026-11-01T00:00:00Z' WHERE AccountAId=?",(self.subject()['CustomerAccountId'],))
  replay=self.run_rule();self.assertTrue(replay['review_required']);self.assertTrue(replay['replayed']);self.assertEqual(replay['event_award_id'],first['event_award_id']);self.assertEqual(get_run(self.c,self.ctx['company_id'],first['run_id'])['input_hash'],first['input_hash'])
 def test_cross_company_rule_blocked(self):
  with self.assertRaises(ValueError):evaluate(self.c,1,self.ctx['activity_id'],self.ctx['rule_id'])
 def test_cross_company_run_blocked(self):
  r=self.run_rule()
  with self.assertRaises(ValueError):get_run(self.c,1,r['run_id'])
 def test_snapshot_cannot_be_mutated(self):
  self.run_rule()
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:self.c.execute("UPDATE IncentiveRun SET Result='Rejected'")
 def test_unknown_rule_operation_rejected(self):
  with self.c:self.c.execute("UPDATE RuleVersion SET ConditionExpression='{}' WHERE IncentiveRuleId=?",(self.ctx['rule_id'],))
  with self.assertRaises(ValueError):self.run_rule()
 def test_fractional_minor_units_rejected(self):
  with self.c:self.c.execute('UPDATE RuleVersion SET RewardSpecification=? WHERE IncentiveRuleId=?',(json.dumps({'amount_minor':1.5,'currency':'CAD'}),self.ctx['rule_id']))
  with self.assertRaises(ValueError):self.run_rule()
 def test_overlapping_assignment_rejected(self):
  row=self.c.execute('SELECT * FROM FleetVehicleAssignment LIMIT 1').fetchone()
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:self.c.execute('INSERT INTO FleetVehicleAssignment(FleetId,VehicleId,ValidFrom,EvidenceReference) VALUES(?,?,?,?)',(row['FleetId'],row['VehicleId'],'2026-06-01T00:00:00Z','duplicate'))
 def test_engine_award_value_is_immutable(self):
  r=self.run_rule()
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:self.c.execute('UPDATE EventAwardComponent SET BenefitValue=999 WHERE EventAwardId=?',(r['event_award_id'],))
 def test_future_record_not_available_at_cutoff(self):
  with self.c:self.c.execute("UPDATE VehicleActivity SET RecordedAt='2027-01-01T00:00:00Z' WHERE Id=?",(self.ctx['activity_id'],))
  self.assertEqual(self.run_rule()['result'],'Rejected')
 def test_concurrent_evaluation_has_one_entitlement(self):
  from concurrent.futures import ThreadPoolExecutor
  def work(_):
   c=connect(self.path)
   try:return evaluate(c,self.ctx['company_id'],self.ctx['activity_id'],self.ctx['rule_id'],evaluated_at='2026-11-04T12:00:00Z')
   finally:c.close()
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(work,range(2)))
  self.assertEqual(results[0]['event_award_id'],results[1]['event_award_id']);self.assertEqual(self.scalar('SELECT COUNT(*) FROM IncentiveRun'),1)
 @unittest.skipUnless(GRAPH_DEPS_AVAILABLE,'Install requirements-knowledge.txt to run RDF/SHACL tests')
 def test_graph_roundtrip_validation_query_and_answer(self):
  from biz.knowledge.graph import build_graph,validate_graph,graph_answer
  from rdflib import Graph
  r=self.run_rule();g=build_graph(r);self.assertTrue(validate_graph(g)['conforms']);self.assertEqual(len(g),len(Graph().parse(data=g.serialize(format='turtle'),format='turtle')))
  self.assertEqual(len(g),len(Graph().parse(data=g.serialize(format='json-ld'),format='json-ld')))
  answer=graph_answer(r,'Why CAD 150?');self.assertIn('CAD 150.00',answer['answer']);self.assertFalse(answer['live_llm']);self.assertEqual(len(answer['checks']),6)
 @unittest.skipUnless(GRAPH_DEPS_AVAILABLE,'Install requirements-knowledge.txt to run RDF/SHACL tests')
 def test_graph_fleet_count_matches_relational_snapshot(self):
  from biz.knowledge.graph import build_graph
  r=self.run_rule();g=build_graph(r)
  n=int(next(iter(g.query('PREFIX rm:<https://example.org/retail-mesh/vocab#> SELECT (COUNT(DISTINCT ?v) AS ?n) WHERE {?m a rm:FleetMembershipEvidence;rm:vehicle ?v.}')))[0])
  self.assertEqual(n,r['fleet_count_before_sale']);self.assertEqual(n,12)
 @unittest.skipUnless(GRAPH_DEPS_AVAILABLE,'Install requirements-knowledge.txt to run RDF/SHACL tests')
 def test_qualified_graph_without_award_is_invalid(self):
  from biz.knowledge.graph import build_graph,validate_graph
  from rdflib import Namespace,RDF
  rm=Namespace('https://example.org/retail-mesh/vocab#');g=build_graph(self.run_rule());g.remove((None,RDF.type,rm.ProviderAward));self.assertFalse(validate_graph(g)['conforms'])
 @unittest.skipUnless(GRAPH_DEPS_AVAILABLE,'Install requirements-knowledge.txt to run RDF/SHACL tests')
 def test_invalid_graph_is_rejected(self):
  from biz.knowledge.graph import build_graph,validate_graph
  from rdflib import Namespace
  rm=Namespace('https://example.org/retail-mesh/vocab#');g=build_graph(self.run_rule());g.remove((None,rm.currency,None));self.assertFalse(validate_graph(g)['conforms'])
 @unittest.skipUnless(GRAPH_DEPS_AVAILABLE,'Install requirements-knowledge.txt to run RDF/SHACL tests')
 def test_rejected_graph_does_not_invent_award(self):
  from biz.knowledge.graph import graph_answer
  with self.c:self.c.execute("UPDATE VehicleActivity SET ActivityStatus='Cancelled' WHERE Id=?",(self.ctx['activity_id'],))
  answer=graph_answer(self.run_rule(),'why award?');self.assertIn('No award was issued',answer['answer'])
if __name__=='__main__':unittest.main(verbosity=2)
