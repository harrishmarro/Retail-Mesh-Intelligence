import sys,tempfile,unittest,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import initialize,connect
from biz.incentives import migrate as migrate_engine,evaluate,get_run
from biz.demo import prepare
from biz import workspaces
from cmn import accounts
PASS='Testing-Passphrase-2026'
def profile(n):return dict(email=f'owner{n}@example.invalid',display_name=f'Owner {n}',password=PASS,company_name=f'Fictional Company {n}',jurisdiction='DEMO',registration=f'SYNTHETIC-WORKSPACE-{n}')
class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'app.db';initialize(self.path);self.c=connect(self.path);migrate_engine(self.c);accounts.migrate(self.c);self.uid,self.cid=accounts.bootstrap(self.c,profile(1))
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def second(self):
  with self.c:
   uid=accounts.create_user(self.c,profile(2)['email'],'Owner 2',PASS);cid=accounts.create_company(self.c,uid,profile(2))
  return uid,cid
 def test_password_hash_and_verification(self):
  h=self.c.execute('SELECT PasswordHash FROM AppUser WHERE Id=?',(self.uid,)).fetchone()[0];self.assertNotIn(PASS,h);self.assertTrue(accounts.verify_password(PASS,h));self.assertFalse(accounts.verify_password('wrong',h))
 def test_password_minimum(self):
  with self.assertRaises(ValueError):accounts.hash_password('short')
 def test_setup_is_single_use(self):
  with self.assertRaises(accounts.AuthError):accounts.bootstrap(self.c,profile(2))
  self.assertEqual(self.c.execute('SELECT COUNT(*) FROM AppUser').fetchone()[0],1)
 def test_salts_are_random(self):self.assertNotEqual(accounts.hash_password(PASS),accounts.hash_password(PASS))
 def test_login_session_never_exposes_hash(self):
  token,csrf=accounts.login(self.c,profile(1)['email'],PASS);s=accounts.session(self.c,token);self.assertEqual(s['Id'],self.uid);self.assertEqual(s['CsrfToken'],csrf);self.assertNotIn('PasswordHash',s)
  row=self.c.execute('SELECT TokenHash FROM AuthSession').fetchone()[0];self.assertNotEqual(row,token)
 def test_bad_password_and_unknown_user_same_message(self):
  messages=[]
  for username in [profile(1)['email'],'unknown@example.invalid']:
   with self.assertRaises(accounts.AuthError) as e:accounts.login(self.c,username,'wrong-password')
   messages.append(str(e.exception))
  self.assertEqual(messages[0],messages[1])
 def test_login_rotates_session_and_csrf(self):
  first,csrf1=accounts.login(self.c,profile(1)['email'],PASS);second,csrf2=accounts.login(self.c,profile(1)['email'],PASS)
  self.assertNotEqual(first,second);self.assertNotEqual(csrf1,csrf2)
 def test_logout_revokes_session(self):
  token,_=accounts.login(self.c,profile(1)['email'],PASS);accounts.logout(self.c,accounts.session(self.c,token))
  with self.assertRaises(accounts.AuthError):accounts.session(self.c,token)
 def test_expired_session_fails(self):
  token,_=accounts.login(self.c,profile(1)['email'],PASS)
  with self.c:self.c.execute('UPDATE AuthSession SET ExpiresAt=0')
  with self.assertRaises(accounts.AuthError):accounts.session(self.c,token)
 def test_disabled_user_session_fails(self):
  token,_=accounts.login(self.c,profile(1)['email'],PASS)
  with self.c:self.c.execute("UPDATE AppUser SET Status='Disabled' WHERE Id=?",(self.uid,))
  with self.assertRaises(accounts.AuthError):accounts.session(self.c,token)
 def test_login_throttle(self):
  for _ in range(6):
   with self.assertRaises(accounts.AuthError):accounts.login(self.c,profile(1)['email'],'bad')
  with self.assertRaises(accounts.AuthError) as e:accounts.login(self.c,profile(1)['email'],PASS)
  self.assertEqual(e.exception.status,429)
 def test_membership_cannot_be_forged(self):
  uid,cid=self.second()
  with self.assertRaises(accounts.AuthError):accounts.require_company(self.c,self.uid,cid)
  self.assertEqual([m['company_id'] for m in accounts.memberships(self.c,self.uid)],[self.cid])
 def test_cannot_claim_existing_company(self):
  uid,_=self.second()
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:accounts.create_company(self.c,uid,profile(1))
  with self.assertRaises(accounts.AuthError):accounts.require_company(self.c,uid,self.cid)
 def test_two_workspace_demos_isolated(self):
  uid,cid=self.second();one=prepare(self.c,self.cid);two=prepare(self.c,cid)
  r1=evaluate(self.c,self.cid,one['activity_id'],one['rule_id']);r2=evaluate(self.c,cid,two['activity_id'],two['rule_id']);self.assertNotEqual(r1['event_award_id'],r2['event_award_id'])
  for user,company,other in [(self.uid,self.cid,r2),(uid,cid,r1)]:
   membership=accounts.require_company(self.c,user,company);s=workspaces.summary(self.c,company,membership);self.assertEqual(len(s['activities']),3);self.assertEqual(len(s['providers']),3);self.assertEqual(len(s['runs']),1)
   with self.assertRaises(ValueError):get_run(self.c,company,other['run_id'])
 def test_workspace_demo_preparation_idempotent(self):
  a=prepare(self.c,self.cid);b=prepare(self.c,self.cid);self.assertEqual(a,b)
 def test_analyst_cannot_evaluate_or_manage_members(self):
  uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='analyst@example.invalid',display_name='Analyst',password=PASS,role='Analyst'))
  with self.assertRaises(accounts.AuthError):accounts.require_company(self.c,uid,self.cid,['CompanyAdmin'])
  with self.assertRaises(accounts.AuthError):accounts.add_member(self.c,uid,self.cid,dict(email='x@example.invalid',role='CompanyAdmin'))
 def test_member_revocation_takes_effect_with_existing_session(self):
  uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='analyst@example.invalid',display_name='Analyst',password=PASS,role='Analyst'));token,_=accounts.login(self.c,'analyst@example.invalid',PASS);accounts.revoke_member(self.c,self.uid,self.cid,uid)
  user=accounts.session(self.c,token)
  with self.assertRaises(accounts.AuthError):accounts.require_company(self.c,user['Id'],self.cid)
 def test_existing_member_password_not_reset_by_another_admin(self):
  uid,cid=self.second();accounts.add_member(self.c,self.uid,self.cid,dict(email=profile(2)['email'],role='Analyst',password='Different-passphrase-2026'))
  token,_=accounts.login(self.c,profile(2)['email'],PASS);self.assertEqual(accounts.session(self.c,token)['Id'],uid)
 def test_provider_scope_and_redacted_run(self):
  ctx=prepare(self.c,self.cid);r=evaluate(self.c,self.cid,ctx['activity_id'],ctx['rule_id']);uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='partner@example.invalid',display_name='Partner',password=PASS,role='Provider',provider_id=r['beneficiary_id']))
  membership=accounts.require_company(self.c,uid,self.cid);s=workspaces.summary(self.c,self.cid,membership);self.assertEqual(len(s['providers']),1);self.assertEqual(len(s['activities']),1);self.assertEqual(s['activities'][0]['ActivityKind'],'Sale');self.assertEqual(len(s['runs']),1)
  self.assertNotIn('evidence',workspaces.public_run(r,membership))
 def test_rental_provider_cannot_read_sale_award(self):
  ctx=prepare(self.c,self.cid);r=evaluate(self.c,self.cid,ctx['activity_id'],ctx['rule_id']);rental=self.c.execute("SELECT ProviderId FROM ProviderAuthorization WHERE ParentCompanyId=? AND ProviderId!=? ORDER BY ProviderId LIMIT 1",(self.cid,r['beneficiary_id'])).fetchone()[0]
  uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='rental@example.invalid',display_name='Rental',password=PASS,role='Provider',provider_id=rental));m=accounts.require_company(self.c,uid,self.cid)
  self.assertEqual(workspaces.summary(self.c,self.cid,m)['runs'],[])
  with self.assertRaises(accounts.AuthError):workspaces.public_run(r,m)
 def test_provider_requires_company_authorization(self):
  with self.assertRaises(accounts.AuthError):accounts.add_member(self.c,self.uid,self.cid,dict(email='p@example.invalid',display_name='P',password=PASS,role='Provider',provider_id=1))
 def test_provider_authorization_revocation_applies_immediately(self):
  ctx=prepare(self.c,self.cid);r=evaluate(self.c,self.cid,ctx['activity_id'],ctx['rule_id']);uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='partner@example.invalid',display_name='Partner',password=PASS,role='Provider',provider_id=r['beneficiary_id']))
  accounts.require_company(self.c,uid,self.cid)
  with self.c:self.c.execute("UPDATE ProviderAuthorization SET AuthorizationStatus='Suspended' WHERE ParentCompanyId=? AND ProviderId=?",(self.cid,r['beneficiary_id']))
  with self.assertRaises(accounts.AuthError):accounts.require_company(self.c,uid,self.cid)
 def test_cannot_revoke_or_demote_self(self):
  with self.assertRaises(ValueError):accounts.revoke_member(self.c,self.uid,self.cid,self.uid)
  with self.assertRaises(ValueError):accounts.add_member(self.c,self.uid,self.cid,dict(email=profile(1)['email'],role='Analyst'))
 def test_audit_is_immutable_and_no_passwords(self):
  audit=' '.join(str(tuple(r)) for r in self.c.execute('SELECT * FROM WorkspaceAuditEvent'));self.assertNotIn(PASS,audit)
  with self.assertRaises(sqlite3.IntegrityError):
   with self.c:self.c.execute("UPDATE WorkspaceAuditEvent SET Action='forged'")
 def test_legacy_demo_still_works_after_workspace_seed(self):
  prepare(self.c,self.cid);legacy=prepare(self.c);self.assertNotEqual(legacy['company_id'],self.cid)
class NarrationTests(unittest.TestCase):
 def base(self):return {'answer':'Maple received CAD 150.00.','checks':[{'name':'fleet','passed':True}],'sources':[{'type':'IncentiveRun','id':1}],'mode':'deterministic_graph_query'}
 def test_no_call_without_explicit_opt_in(self):
  from biz.ai.explanations import narrate
  from unittest.mock import Mock
  transport=Mock();r=narrate(self.base(),'why',transport=transport);transport.assert_not_called();self.assertEqual(r['ai_status'],'not_requested')
 def test_unconfigured_falls_back(self):
  from biz.ai.explanations import narrate
  from unittest.mock import patch
  with patch.dict('os.environ',{},clear=True):r=narrate(self.base(),'why',enabled=True)
  self.assertEqual(r['ai_status'],'not_configured');self.assertEqual(r['answer'],self.base()['answer'])
 def test_mock_responses_narrative_preserves_authoritative_answer(self):
  from biz.ai.explanations import narrate
  from unittest.mock import patch
  captured=[]
  def transport(payload):captured.append(payload);return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'All checks passed.'}]}]}
  with patch.dict('os.environ',{'OPENAI_API_KEY':'mock-not-a-real-key','RETAIL_MESH_AI_MODEL':'mock-model'},clear=True):r=narrate(self.base(),'Explain this result',enabled=True,transport=transport)
  self.assertTrue(r['live_llm']);self.assertEqual(r['answer'],self.base()['answer']);self.assertEqual(r['sources'],self.base()['sources']);self.assertFalse(captured[0]['store']);self.assertNotIn('tools',captured[0]);self.assertNotIn('mock-not-a-real-key',json.dumps(captured[0]))
 def test_malformed_provider_response_falls_back(self):
  from biz.ai.explanations import narrate
  from unittest.mock import patch
  with patch.dict('os.environ',{'OPENAI_API_KEY':'mock-secret','RETAIL_MESH_AI_MODEL':'mock-model'},clear=True):r=narrate(self.base(),'why',enabled=True,transport=lambda payload:None)
  self.assertEqual(r['ai_status'],'unavailable');self.assertEqual(r['answer'],self.base()['answer'])
 def test_transport_failure_does_not_expose_credentials(self):
  from biz.ai.explanations import narrate
  from unittest.mock import patch
  def transport(_):raise ValueError('secret should not be returned')
  with patch.dict('os.environ',{'OPENAI_API_KEY':'mock-secret','RETAIL_MESH_AI_MODEL':'mock-model'},clear=True):r=narrate(self.base(),'why',enabled=True,transport=transport)
  self.assertEqual(r['ai_status'],'unavailable');self.assertNotIn('secret',json.dumps(r));self.assertFalse(r['live_llm'])
if __name__=='__main__':unittest.main(verbosity=2)
