import sys,tempfile,unittest,json,sqlite3,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import initialize,connect
from biz.incentives import migrate
from biz.csv_import import ingest
from cmn import accounts
from biz import onboarding,provider_signup as signup,provider_services as services
PASS='Provider-Flow-Passphrase-2026'
class ProviderFlowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'flow.db';initialize(self.path,seed=False);self.c=connect(self.path);migrate(self.c);accounts.migrate(self.c);ingest(self.c,ROOT/'data/preprocessed/RetailMesh_Reviewed_CSV_Data.zip');self.admin,self.cid=accounts.bootstrap(self.c,dict(email='admin@example.invalid',display_name='Admin',password=PASS,manage_imported=True));self.operator=accounts.add_member(self.c,self.admin,self.cid,dict(email='operator@example.invalid',display_name='Operator',password=PASS,role='CompanyOperator'));self.code=signup.configure(self.c,self.admin,self.cid,{'enabled':True})['public_code']
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def data(self):return dict(code=self.code,legal_name='Public Applicant (fictional)',jurisdiction='DEMO',registration='PUBLIC-001',contact_name='Applicant',contact_email='applicant@example.invalid',contact_phone='+1 250 555 0199',outlet_name='Main',outlet_address='Synthetic address',capabilities=['VehicleSale'],program_ids=[1],website='https://example.invalid',supporting_evidence='synthetic:registration; synthetic:contact-authority; synthetic:capability-record')
 def submitted(self):
  result=signup.submit(self.c,self.data());status=signup.applicant_status(self.c,result['tracking_token']);return result,status
 def reviewing(self):
  result,status=self.submitted();onboarding.transition(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=status['Version'],state='UnderReview'));return result,signup.applicant_status(self.c,result['tracking_token'])
 def accepted(self):
  result,status=self.reviewing()
  for code in onboarding.CHECKS:
   row=self.c.execute('SELECT Version FROM ProviderApplication WHERE Id=?',(status['Id'],)).fetchone();onboarding.record_check(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=row[0],check_code=code,evidence_reference='synthetic:review:'+code))
  status=signup.applicant_status(self.c,result['tracking_token']);signup.review_application(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=status['Version'],decision='Accepted',note='Business and contact evidence reviewed',program_ids=[1]));return result,signup.applicant_status(self.c,result['tracking_token'])
 def provider_user(self,provider_id=1,email='provider@example.invalid'):
  return accounts.add_member(self.c,self.admin,self.cid,dict(email=email,display_name='Provider',password=PASS,role='Provider',provider_id=provider_id))
 def claim_data(self):return dict(rule_id=2,period_start='2026-07-01',period_end='2026-10-01',statement='Please review my quarterly incentive',evidence_reference='synthetic:claim:quarter',requested_amount='250.00',currency='CAD')
 def test_public_submit_stages_only_and_returns_private_tracking(self):
  count=self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0];result,status=self.submitted();self.assertEqual(status['State'],'Submitted');self.assertIsNone(self.c.execute('SELECT CreatedBy FROM ProviderApplication WHERE Id=?',(status['Id'],)).fetchone()[0]);self.assertEqual(count,self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0]);self.assertFalse(status['activation_available']);self.assertNotIn(result['tracking_token'],str(list(self.c.execute('SELECT TokenHash FROM ProviderApplicationAccess'))))
 def test_disabled_intake_is_not_public(self):
  signup.configure(self.c,self.admin,self.cid,{'enabled':False})
  with self.assertRaises(accounts.AuthError):signup.submit(self.c,self.data())
 def test_operator_cannot_enable_public_intake(self):
  with self.assertRaises(accounts.AuthError):signup.configure(self.c,self.operator,self.cid,{'enabled':True})
 def test_wrong_tracking_token_has_no_application_access(self):
  self.submitted()
  with self.assertRaises(accounts.AuthError):signup.applicant_status(self.c,'unrelated-token-'+('x'*30))
 def test_operator_acceptance_requires_validation(self):
  result,status=self.reviewing()
  with self.assertRaises(ValueError):signup.review_application(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=status['Version'],decision='Accepted',note='Not enough checks yet'))
  self.assertEqual(signup.applicant_status(self.c,result['tracking_token'])['State'],'UnderReview')
 def test_changes_needed_applicant_edits_and_resubmits(self):
  result,status=self.reviewing();signup.review_application(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=status['Version'],decision='Changes needed',note='Correct the outlet address'));status=signup.applicant_status(self.c,result['tracking_token']);self.assertEqual(status['decision'],'Changes needed');self.assertEqual(status['review_note'],'Correct the outlet address');signup.resubmit(self.c,{**self.data(),'token':result['tracking_token'],'version':status['Version'],'outlet_address':'Corrected synthetic address'});self.assertEqual(signup.applicant_status(self.c,result['tracking_token'])['State'],'Submitted')
 def test_rejection_does_not_create_provider_or_account(self):
  result,status=self.reviewing();signup.review_application(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=status['Version'],decision='Rejected',note='Required registration evidence could not be validated'));status=signup.applicant_status(self.c,result['tracking_token']);self.assertEqual(status['decision'],'Rejected');self.assertIsNone(status['ProviderId']);self.assertFalse(self.c.execute("SELECT 1 FROM AppUser WHERE Email='applicant@example.invalid'").fetchone())
 def test_acceptance_enrols_then_applicant_activates_own_account(self):
  result,status=self.accepted();self.assertEqual(status['decision'],'Accepted');self.assertTrue(status['activation_available']);onboarding.activate(self.c,result['tracking_token'],PASS);token,_=accounts.login(self.c,'applicant@example.invalid',PASS);user=accounts.session(self.c,token);m=accounts.require_company(self.c,user['Id'],self.cid);self.assertEqual(m['ProviderId'],status['ProviderId']);self.assertTrue(services.claim_options(self.c,user['Id'],self.cid)['rules'])
 def test_provider_cannot_review_applications(self):
  uid=self.provider_user();result,status=self.reviewing()
  with self.assertRaises(accounts.AuthError):signup.review_application(self.c,uid,self.cid,dict(application_id=status['Id'],version=status['Version'],decision='Rejected',note='forged review'))
 def test_cross_company_review_denied(self):
  result,status=self.reviewing()
  with self.assertRaises(accounts.AuthError):signup.review_application(self.c,self.operator,2,dict(application_id=status['Id'],version=status['Version'],decision='Rejected',note='wrong company'))
 def test_claim_is_scoped_and_creates_no_award(self):
  uid=self.provider_user();before=self.c.execute('SELECT COUNT(*) FROM PeriodAward').fetchone()[0];claim=services.submit_claim(self.c,uid,self.cid,self.claim_data());self.assertEqual(services.claims(self.c,uid,self.cid)['claims'][0]['Status'],'Submitted');self.assertEqual(before,self.c.execute('SELECT COUNT(*) FROM PeriodAward').fetchone()[0]);row=self.c.execute('SELECT * FROM IncentiveClaim WHERE Id=?',(claim['claim_id'],)).fetchone();self.assertEqual(row['ProviderId'],1);self.assertEqual(row['RequestedAmountMinor'],25000)
 def test_provider_cannot_view_other_providers_claims(self):
  first=self.provider_user();second=self.provider_user(3,'rental@example.invalid');claim=services.submit_claim(self.c,first,self.cid,self.claim_data());self.assertEqual(services.claims(self.c,second,self.cid)['claims'],[])
  with self.assertRaises(accounts.AuthError):services.claim_row(self.c,second,self.cid,claim['claim_id'])
 def test_event_claim_rejects_another_provider_activity(self):
  uid=self.provider_user();data={**self.claim_data(),'rule_id':1,'activity_id':25}
  with self.assertRaises(accounts.AuthError):services.submit_claim(self.c,uid,self.cid,data)
 def test_operator_returns_claim_and_provider_resubmits(self):
  uid=self.provider_user();claim=services.submit_claim(self.c,uid,self.cid,self.claim_data());cid=claim['claim_id'];services.review_claim(self.c,self.operator,self.cid,dict(claim_id=cid,version=1,status='UnderReview',note='Review started'));services.review_claim(self.c,self.operator,self.cid,dict(claim_id=cid,version=2,status='ChangesNeeded',note='Attach a better source reference'));services.submit_claim(self.c,uid,self.cid,{**self.claim_data(),'claim_id':cid,'version':3,'evidence_reference':'synthetic:corrected'});row=services.claims(self.c,uid,self.cid)['claims'][0];self.assertEqual(row['Status'],'Submitted');self.assertEqual(len(row['history']),4)
 def test_provider_cannot_approve_own_claim(self):
  uid=self.provider_user();claim=services.submit_claim(self.c,uid,self.cid,self.claim_data())
  with self.assertRaises(accounts.AuthError):services.review_claim(self.c,uid,self.cid,dict(claim_id=claim['claim_id'],version=1,status='Approved',note='self approval'))
 def test_concern_response_is_private_and_tracked(self):
  uid=self.provider_user();other=self.provider_user(3,'other-provider@example.invalid');concern=services.concern_action(self.c,uid,self.cid,dict(subject='How was my incentive calculated?',message='Please explain the volume threshold'));self.assertEqual(services.concerns(self.c,other,self.cid)['concerns'],[]);services.concern_action(self.c,self.operator,self.cid,dict(concern_id=concern['concern_id'],version=1,status='Resolved',message='The policy requires two qualifying completed services'));row=services.concerns(self.c,uid,self.cid)['concerns'][0];self.assertEqual(row['Status'],'Resolved');self.assertEqual(len(row['messages']),2)
 def test_concern_cannot_link_another_provider_claim(self):
  first=self.provider_user();second=self.provider_user(3,'rental@example.invalid');claim=services.submit_claim(self.c,first,self.cid,self.claim_data())
  with self.assertRaises(accounts.AuthError):services.concern_action(self.c,second,self.cid,dict(subject='forged',message='bad claim link',claim_id=claim['claim_id']))
 def test_provider_chat_cites_own_policy_without_graph(self):
  uid=self.provider_user();answer=services.chat(self.c,uid,self.cid,{'question':'How is my incentive calculated?'});self.assertFalse(answer['live_llm']);self.assertTrue(answer['sources']);self.assertIn('500',answer['answer']);self.assertNotIn('@graph',answer)
 def test_workspace_request_never_creates_or_grants_a_workspace(self):
  uid=self.provider_user();before=self.c.execute('SELECT COUNT(*) FROM ParentCompany').fetchone()[0];memberships=accounts.memberships(self.c,uid);request=services.concern_action(self.c,uid,self.cid,dict(kind='WorkspaceAccess',workspace_name='Requested company',subject='Workspace access request',message='Please review a new workspace request'));row=services.concerns(self.c,uid,self.cid)['concerns'][0];self.assertEqual(row['Kind'],'WorkspaceAccess');self.assertEqual(before,self.c.execute('SELECT COUNT(*) FROM ParentCompany').fetchone()[0]);self.assertEqual(memberships,accounts.memberships(self.c,uid));self.assertTrue(request['concern_id'])
 def test_claim_history_is_append_only(self):
  uid=self.provider_user();services.submit_claim(self.c,uid,self.cid,self.claim_data())
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:self.c.execute("UPDATE IncentiveClaimEvent SET Message='overwritten'")
 def test_old_database_constraints_upgrade_without_losing_rows(self):
  old=Path(self.tmp.name)/'old.db';shutil.copyfile(ROOT/'data/raw/original_import_snapshot.db',old);connection=connect(old)
  try:
   counts={t:connection.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['Provider','VehicleActivity','EventAward','ImportedRecord']};accounts.migrate(connection);self.assertIn('CompanyOperator',connection.execute("SELECT sql FROM sqlite_master WHERE name='CompanyMembership'").fetchone()[0]);self.assertEqual(counts,{t:connection.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in counts});self.assertEqual(connection.execute('PRAGMA foreign_key_check').fetchall(),[])
  finally:connection.close()
 def test_old_memberships_applications_checks_and_invitations_survive_upgrade(self):
  old=Path(self.tmp.name)/'populated-old.db';shutil.copyfile(ROOT/'data/raw/original_import_snapshot.db',old);c=connect(old)
  try:
   with c:
    uid=accounts.create_user(c,'old-admin@example.invalid','Old administrator',PASS);cid=c.execute('SELECT MIN(Id) FROM ParentCompany').fetchone()[0]
    c.execute("INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role) VALUES(?,?,'CompanyAdmin')",(uid,cid))
    c.execute("INSERT INTO ProviderApplication(ParentCompanyId,LegalName,RegistrationJurisdiction,BusinessRegistrationNumber,ContactName,ContactEmail,OutletName,OutletAddress,CapabilitiesJson,State,CreatedBy,CreatedAt,UpdatedAt) VALUES(?,'Legacy application','DEMO','UPGRADE-1','Legacy contact','old-provider@example.invalid','Legacy outlet','Synthetic','[\"VehicleSale\"]','UnderReview',?,1,1)",(cid,uid));aid=c.execute('SELECT MAX(Id) FROM ProviderApplication').fetchone()[0]
    c.execute("INSERT INTO ProviderValidationCheck(ApplicationId,CheckCode,EvidenceReference,ReviewedBy,ReviewedAt) VALUES(?,'business_registration','synthetic:old-check',?,1)",(aid,uid));c.execute("INSERT INTO ProviderInvitation(ApplicationId,TokenHash,CreatedBy,CreatedAt,ExpiresAt) VALUES(?,'preserve-old-token-hash',?,1,9999999999)",(aid,uid))
   before={t:[tuple(r) for r in c.execute('SELECT * FROM '+t)] for t in ('CompanyMembership','ProviderValidationCheck','ProviderInvitation')};application_before=dict(c.execute('SELECT * FROM ProviderApplication WHERE Id=?',(aid,)).fetchone());accounts.migrate(c)
   for table,rows in before.items():self.assertEqual(rows,[tuple(r) for r in c.execute('SELECT * FROM '+table)])
   after=dict(c.execute('SELECT * FROM ProviderApplication WHERE Id=?',(aid,)).fetchone())
   self.assertEqual(application_before,{k:after[k] for k in application_before});self.assertEqual(after['RequestedProgramsJson'],'[]');self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[]);self.assertEqual(c.execute('PRAGMA foreign_keys').fetchone()[0],1)
   with c:c.execute("INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role) VALUES(?,?,'CompanyOperator')",(uid,c.execute('SELECT MAX(Id) FROM ParentCompany').fetchone()[0]))
  finally:c.close()
 def test_acceptance_rolls_back_provider_if_enrollment_fails(self):
  result,status=self.reviewing()
  for code in onboarding.CHECKS:
   version=self.c.execute('SELECT Version FROM ProviderApplication WHERE Id=?',(status['Id'],)).fetchone()[0];onboarding.record_check(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=version,check_code=code,evidence_reference='synthetic:rollback-check'))
  version=self.c.execute('SELECT Version FROM ProviderApplication WHERE Id=?',(status['Id'],)).fetchone()[0];count=self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0]
  self.c.execute("CREATE TRIGGER test_enrollment_failure BEFORE INSERT ON ProgramEnrollment BEGIN SELECT RAISE(ABORT,'simulated enrollment failure'); END")
  with self.assertRaises(sqlite3.IntegrityError):signup.review_application(self.c,self.operator,self.cid,dict(application_id=status['Id'],version=version,decision='Accepted',note='Checks reviewed',program_ids=[1]))
  self.assertEqual(self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0],count);self.assertEqual(signup.applicant_status(self.c,result['tracking_token'])['State'],'UnderReview');self.assertEqual(self.c.execute('SELECT COUNT(*) FROM ProviderInvitation WHERE ApplicationId=?',(status['Id'],)).fetchone()[0],0)
