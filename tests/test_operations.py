import csv,hashlib,io,json,sqlite3,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import initialize,connect,MODELS
from biz.incentives import migrate
from cmn import accounts
from biz import onboarding,observability,workspaces
from biz.csv_import import ingest
from biz.knowledge.base import knowledge_document,validate_document,export_bundle,rdf_graph,answer
PASS='Testing-Passphrase-2026';NEW='Changed-Passphrase-2026';DATA=ROOT/'data/preprocessed/RetailMesh_Reviewed_CSV_Data.zip'
def profile():return dict(email='owner@example.invalid',display_name='Owner',password=PASS,company_name='Company (fictional)',jurisdiction='DEMO',registration='NEW-OPERATIONS-COMPANY')
class Base(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.db=Path(self.tmp.name)/'app.db';initialize(self.db);self.c=connect(self.db);migrate(self.c);accounts.migrate(self.c)
 def tearDown(self):self.c.close();self.tmp.cleanup()
 def owner(self):self.uid,self.cid=accounts.bootstrap(self.c,profile());return self.uid,self.cid
 def imported(self):
  result=ingest(self.c,DATA);self.owner();self.imported_cids=[r[0] for r in self.c.execute("SELECT RecordId FROM ImportedRecord WHERE TableName='ParentCompany'")];return result
class ImportTests(Base):
 def test_ambiguous_company_ownership_rejects_and_rolls_back_import(self):
  target=Path(self.tmp.name)/'ambiguous-company.zip'
  with zipfile.ZipFile(DATA) as source,zipfile.ZipFile(target,'w') as output:
   for entry in source.infolist():
    payload=source.read(entry)
    if entry.filename.endswith('/ProviderAuthorization.csv'):
     reader=csv.DictReader(io.StringIO(payload.decode('utf-8-sig')));rows=list(reader);extra=dict(rows[0]);extra['Id']=str(max(int(r['Id']) for r in rows)+1);extra['ParentCompanyId']='2';rows.append(extra)
     buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=reader.fieldnames);writer.writeheader();writer.writerows(rows);payload=buffer.getvalue().encode()
    output.writestr(entry.filename,payload)
  before={table:self.c.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0] for table in MODELS}
  with self.assertRaisesRegex(ValueError,'more than one company'):ingest(self.c,target)
  self.assertEqual(self.c.execute('SELECT COUNT(*) FROM DataImportBatch').fetchone()[0],0)
  self.assertEqual(self.c.execute('SELECT COUNT(*) FROM CompanyActivity').fetchone()[0],0)
  self.assertEqual(before,{table:self.c.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0] for table in MODELS})

 def test_imported_activities_are_not_mistaken_for_prepared_engine_demo(self):
  self.imported();cid=self.imported_cids[0];member=accounts.require_company(self.c,self.uid,cid);before=workspaces.summary(self.c,cid,member);self.assertFalse(before['demo_ready'])
  from biz.demo import prepare
  prepare(self.c,cid);after=workspaces.summary(self.c,cid,member);self.assertTrue(after['demo_ready']);self.assertEqual(len(after['activities']),len(before['activities'])+3);self.assertEqual(sum(a['SourceNamespace']==f'demo.workspace.{cid}' for a in after['activities']),3)

 def test_derived_journey_view_reproduces_all_supplied_report_fields(self):
  self.imported()
  with zipfile.ZipFile(DATA) as archive:expected=list(csv.DictReader(io.StringIO(archive.read('csv/JourneyOverview.csv').decode('utf-8-sig'))))
  rows=[dict(r) for r in self.c.execute("SELECT j.* FROM JourneyOverview j JOIN ImportedRecord i ON i.RecordId=j.ActivityId AND i.TableName='VehicleActivity'")]
  fields=list(expected[0]);normalize=lambda row:tuple(str(row[k]) if row.get(k) not in [None,''] else '' for k in fields)
  self.assertEqual(sorted(map(normalize,rows)),sorted(map(normalize,expected)))

 def test_first_admin_can_start_with_dataset_without_extra_company(self):
  ingest(self.c,DATA);uid,cid=accounts.bootstrap(self.c,dict(email='first@example.invalid',display_name='First Admin',password=PASS,manage_imported=True));self.assertEqual(len(accounts.memberships(self.c,uid)),2);self.assertEqual(self.c.execute('SELECT COUNT(*) FROM ParentCompany').fetchone()[0],3)

 def test_ingests_all_34_tables_and_preserves_existing_seed(self):
  old=self.c.execute('SELECT LegalName FROM Provider WHERE Id=1').fetchone()[0];r=self.imported()
  self.assertEqual(len(r['counts']),34);self.assertEqual(sum(r['counts'].values()),self.c.execute('SELECT COUNT(*) FROM ImportedRecord').fetchone()[0]);self.assertEqual(r['counts']['VehicleActivity'],35)
  self.assertEqual(old,self.c.execute('SELECT LegalName FROM Provider WHERE Id=1').fetchone()[0]);self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_reimport_is_noop_even_when_zip_metadata_changes(self):
  r=self.imported();counts={t:self.c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in MODELS}
  target=Path(self.tmp.name)/'repacked.zip'
  with zipfile.ZipFile(DATA) as source,zipfile.ZipFile(target,'w') as out:
   for n in reversed(source.namelist()):out.writestr(n,source.read(n))
  again=ingest(self.c,target);self.assertTrue(again['replayed']);self.assertEqual(r['sha256'],again['sha256'])
  self.assertEqual(counts,{t:self.c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in MODELS})
 def test_original_ids_and_optional_nulls_preserved(self):
  self.imported();mapped=self.c.execute("SELECT RecordId FROM ImportedRecord WHERE TableName='ParentCompany' AND SourceId=1").fetchone()[0]
  self.assertGreater(mapped,1);self.assertIsNone(self.c.execute('SELECT ValidTo FROM ProviderAuthorization WHERE ParentCompanyId=? LIMIT 1',(mapped,)).fetchone()[0])
 def test_invalid_foreign_key_rolls_back_entire_import(self):
  target=Path(self.tmp.name)/'bad.zip'
  with zipfile.ZipFile(DATA) as source,zipfile.ZipFile(target,'w') as out:
   for n in source.namelist():
    payload=source.read(n)
    if n.endswith('/Sale.csv'):payload=payload.decode('utf-8-sig').replace('1,1,62800','1,99999,62800',1).encode()
    out.writestr(n,payload)
  before=self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0]
  with self.assertRaises(ValueError):ingest(self.c,target)
  self.assertEqual(self.c.execute('SELECT COUNT(*) FROM DataImportBatch').fetchone()[0],0);self.assertEqual(before,self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0])
 def test_setup_grants_first_admin_imported_companies(self):
  self.imported();self.assertEqual({m['company_id'] for m in accounts.memberships(self.c,self.uid)},set(self.imported_cids+[self.cid]))
 def test_imported_activity_visible_only_in_assigned_company(self):
  self.imported();sets=[]
  for cid in self.imported_cids:
   s=workspaces.summary(self.c,cid,accounts.require_company(self.c,self.uid,cid));sets.append({r['Id'] for r in s['activities']});self.assertGreater(len(s['recorded_awards']),0)
  self.assertFalse(s["demo_ready"]);self.assertEqual(len(set.union(*sets)),35);self.assertFalse(sets[0]&sets[1]);self.assertEqual(workspaces.summary(self.c,self.cid,accounts.require_company(self.c,self.uid,self.cid))['activities'],[])
 def test_import_cannot_claim_already_managed_company(self):
  self.imported()
  with self.c:
   other=accounts.create_user(self.c,'other@example.invalid','Other',PASS);accounts.create_company(self.c,other,dict(company_name='Other',jurisdiction='DEMO',registration='OTHER-IMPORT-OWNER'))
  with self.assertRaises(accounts.AuthError):ingest(self.c,DATA,other)
  self.assertEqual(len(accounts.memberships(self.c,other)),1)
class KnowledgeTests(Base):
 def setUp(self):super().setUp();self.imported();self.kcid=self.imported_cids[0];self.membership=accounts.require_company(self.c,self.uid,self.kcid)
 def test_knowledge_available_without_engine_run(self):
  self.assertEqual(self.c.execute('SELECT COUNT(*) FROM IncentiveRun').fetchone()[0],0);doc=knowledge_document(self.c,self.kcid,self.membership);self.assertGreater(doc['summary']['nodes'],100);self.assertTrue(validate_document(doc)['conforms']);self.assertGreater(doc['summary']['imported_awards'],0)
 def test_export_never_has_cross_company_nodes_or_dangling_edges(self):
  one=knowledge_document(self.c,self.kcid,self.membership);two=knowledge_document(self.c,self.imported_cids[1],accounts.require_company(self.c,self.uid,self.imported_cids[1]));self.assertFalse({n['@id'] for n in one['@graph']}&{n['@id'] for n in two['@graph']});validate_document(one);validate_document(two)
 def test_contact_and_auth_data_not_exported(self):
  text=json.dumps(knowledge_document(self.c,self.kcid,self.membership));self.assertNotIn('rm:Email',text);self.assertNotIn('rm:PhoneNo',text);self.assertNotIn('rm:DisplayName',text);self.assertNotIn('PasswordHash',text);self.assertNotIn('TokenHash',text)
 def test_provider_cannot_view_or_export_the_graph(self):
  provider=self.c.execute('SELECT ProviderId FROM ProviderAuthorization WHERE ParentCompanyId=? LIMIT 1',(self.kcid,)).fetchone()[0];m={**self.membership,'Role':'Provider','ProviderId':provider}
  with self.assertRaises(accounts.AuthError):knowledge_document(self.c,self.kcid,m)
  with self.assertRaises(accounts.AuthError):export_bundle(self.c,self.kcid,m)
 def test_okf_bundle_hashes_schema_shacl_and_provenance(self):
  payload=export_bundle(self.c,self.kcid,self.membership)
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   manifest=json.loads(z.read('manifest.json'));self.assertTrue(manifest['read_only']);self.assertEqual(manifest['scope']['company_id'],self.kcid)
   for name,digest in manifest['files'].items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
   self.assertTrue(json.loads(z.read('validation.json'))['shacl_conforms']);doc=json.loads(z.read('records.jsonld'));self.assertEqual(doc['okf_version'],'1.0.0')
   from rdflib import Graph
   self.assertTrue(Graph().parse(data=z.read('graph.ttl'),format='turtle').isomorphic(rdf_graph(doc)))
 def test_cited_answer_preserves_offline_sample_decision_semantics(self):
  result=answer(self.c,self.kcid,self.membership,'How many awards?');self.assertIn('offline',result['answer']);self.assertFalse(result['live_llm']);self.assertGreater(len(result['sources']),0)
 def test_validation_rejects_scope_escape(self):
  doc=knowledge_document(self.c,self.kcid,self.membership);doc['@graph'][0]['rm:test']={'@id':'urn:retail-mesh:company:999:record:Provider:1'}
  with self.assertRaises(ValueError):validate_document(doc)
class OnboardingTests(Base):
 def setUp(self):super().setUp();self.owner()
 def draft(self):
  data=dict(legal_name='New Provider (fictional)',jurisdiction='DEMO',registration='NEW-PROVIDER-001',contact_name='Provider Contact',contact_email='provider@example.invalid',outlet_name='Main outlet',outlet_address='Synthetic location',capabilities=['VehicleSale','VehicleService'])
  return onboarding.save_draft(self.c,self.uid,self.cid,data)['application_id']
 def row(self,aid):return dict(self.c.execute('SELECT * FROM ProviderApplication WHERE Id=?',(aid,)).fetchone())
 def move(self,aid,state,note=''):
  return onboarding.transition(self.c,self.uid,self.cid,dict(application_id=aid,version=self.row(aid)['Version'],state=state,note=note))
 def review(self,aid):
  self.move(aid,'Submitted');self.move(aid,'UnderReview')
  for code in onboarding.CHECKS:onboarding.record_check(self.c,self.uid,self.cid,dict(application_id=aid,version=self.row(aid)['Version'],check_code=code,evidence_reference='synthetic:review:'+code))
 def approve(self):
  aid=self.draft();self.review(aid);self.move(aid,'Validated');self.move(aid,'Approved');return aid
 def invite(self,aid):return onboarding.issue_invitation(self.c,self.uid,self.cid,dict(application_id=aid,version=self.row(aid)['Version']))['token']
 def test_draft_submission_and_review_do_not_insert_provider(self):
  count=self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0];aid=self.draft();self.review(aid);self.assertEqual(count,self.c.execute('SELECT COUNT(*) FROM Provider').fetchone()[0]);self.assertIsNone(self.row(aid)['ProviderId'])
 def test_cannot_skip_to_approval(self):
  aid=self.draft()
  with self.assertRaises(ValueError):self.move(aid,'Approved')
 def test_all_evidence_required_to_validate(self):
  aid=self.draft();self.move(aid,'Submitted');self.move(aid,'UnderReview')
  with self.assertRaises(ValueError):self.move(aid,'Validated')
 def test_approval_creates_provider_authorization_and_capabilities(self):
  aid=self.approve();provider=self.row(aid)['ProviderId'];self.assertIsNotNone(provider);self.assertEqual(self.c.execute('SELECT COUNT(*) FROM CapabilityAuthorization ca JOIN ProviderAuthorization pa ON pa.Id=ca.ProviderAuthorizationId WHERE pa.ProviderId=? AND pa.ParentCompanyId=?',(provider,self.cid)).fetchone()[0],2)
  self.assertIsNone(self.c.execute("SELECT 1 FROM AppUser WHERE Email='provider@example.invalid'").fetchone())
 def test_stale_version_is_rejected(self):
  aid=self.draft();self.move(aid,'Submitted')
  with self.assertRaises(accounts.AuthError):onboarding.transition(self.c,self.uid,self.cid,dict(application_id=aid,version=1,state='UnderReview'))
 def test_returning_for_changes_invalidates_checks(self):
  aid=self.draft();self.review(aid);self.move(aid,'NeedsChanges','Contact evidence needs a new review');self.assertEqual(self.c.execute('SELECT COUNT(*) FROM ProviderValidationCheck WHERE ApplicationId=?',(aid,)).fetchone()[0],0);self.assertEqual(onboarding.listing(self.c,self.uid,self.cid)['applications'][0]['ReviewNote'],'Contact evidence needs a new review');self.move(aid,'Submitted')
 def test_different_company_cannot_review_application(self):
  aid=self.draft()
  with self.c:other=accounts.create_company(self.c,self.uid,dict(company_name='Other',jurisdiction='DEMO',registration='OTHER-ONBOARD'))
  with self.assertRaises(accounts.AuthError):onboarding.transition(self.c,self.uid,other,dict(application_id=aid,version=1,state='Submitted'))
 def test_analyst_cannot_create_application(self):
  uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='analyst@example.invalid',display_name='Analyst',password=PASS,role='Analyst'))
  with self.assertRaises(accounts.AuthError):onboarding.save_draft(self.c,uid,self.cid,{})
 def test_invite_only_after_approval(self):
  aid=self.draft()
  with self.assertRaises(ValueError):self.invite(aid)
 def test_single_use_activation_creates_scoped_login(self):
  aid=self.approve();token=self.invite(aid);self.assertNotIn(token,str(list(self.c.execute('SELECT * FROM ProviderInvitation'))));onboarding.activate(self.c,token,PASS)
  session,_=accounts.login(self.c,'provider@example.invalid',PASS);user=accounts.session(self.c,session);m=accounts.require_company(self.c,user['Id'],self.cid);self.assertEqual(m['Role'],'Provider');self.assertEqual(m['ProviderId'],self.row(aid)['ProviderId']);self.assertEqual(self.row(aid)['State'],'Provisioned')
  with self.assertRaises(accounts.AuthError):onboarding.activate(self.c,token,PASS)
 def test_invite_reissue_revokes_old_token(self):
  aid=self.approve();old=self.invite(aid);new=self.invite(aid)
  with self.assertRaises(accounts.AuthError):onboarding.activate(self.c,old,PASS)
  onboarding.activate(self.c,new,PASS)
 def test_expired_invitation_cannot_provision(self):
  aid=self.approve();token=self.invite(aid)
  with self.c:self.c.execute('UPDATE ProviderInvitation SET ExpiresAt=0')
  with self.assertRaises(accounts.AuthError):onboarding.activate(self.c,token,PASS)
 def test_member_form_cannot_bypass_activation(self):
  aid=self.approve()
  with self.assertRaises(accounts.AuthError):accounts.add_member(self.c,self.uid,self.cid,dict(email='provider@example.invalid',display_name='Provider',password=PASS,role='Provider',provider_id=self.row(aid)['ProviderId']))
 def test_existing_account_password_never_reset_by_activation(self):
  with self.c:existing=accounts.create_user(self.c,'provider@example.invalid','Existing',PASS)
  aid=self.approve();token=self.invite(aid)
  with self.assertRaises(accounts.AuthError):onboarding.activate(self.c,token,NEW)
  onboarding.activate(self.c,token,PASS);session,_=accounts.login(self.c,'provider@example.invalid',PASS);self.assertEqual(accounts.session(self.c,session)['Id'],existing)
 def test_password_change_revokes_all_sessions(self):
  first,_=accounts.login(self.c,profile()['email'],PASS);second,_=accounts.login(self.c,profile()['email'],PASS);user=accounts.session(self.c,first);accounts.change_password(self.c,user,PASS,NEW)
  for token in [first,second]:
   with self.assertRaises(accounts.AuthError):accounts.session(self.c,token)
  with self.assertRaises(accounts.AuthError):accounts.login(self.c,profile()['email'],PASS)
  self.assertTrue(accounts.login(self.c,profile()['email'],NEW)[0]);self.assertNotIn(NEW,str(list(self.c.execute('SELECT * FROM WorkspaceAuditEvent'))))
 def test_wrong_current_password_does_not_change_or_revoke(self):
  token,_=accounts.login(self.c,profile()['email'],PASS);user=accounts.session(self.c,token)
  with self.assertRaises(accounts.AuthError):accounts.change_password(self.c,user,'wrong',NEW)
  self.assertEqual(accounts.session(self.c,token)['Id'],self.uid)
 def test_password_attempts_are_throttled(self):
  token,_=accounts.login(self.c,profile()['email'],PASS);user=accounts.session(self.c,token)
  for _ in range(6):
   with self.assertRaises(accounts.AuthError):accounts.change_password(self.c,user,'wrong',NEW)
  with self.assertRaises(accounts.AuthError) as error:accounts.change_password(self.c,user,PASS,NEW)
  self.assertEqual(error.exception.status,429)
class ObservabilityTests(Base):
 def test_only_admin_companies_appear(self):
  self.imported()
  with self.c:
   other=accounts.create_user(self.c,'other@example.invalid','Other',PASS);private=accounts.create_company(self.c,other,dict(company_name='Private other',jurisdiction='DEMO',registration='PRIVATE-OBS'))
  accounts.add_member(self.c,other,private,dict(email=profile()['email'],role='Analyst'))
  dashboard=observability.dashboard(self.c,self.uid);self.assertEqual(len(dashboard['companies']),3);self.assertNotIn('Private other',json.dumps(dashboard));self.assertNotIn(private,{x['company_id'] for x in dashboard['companies']})
 def test_analyst_has_no_dashboard_access(self):
  self.owner();uid=accounts.add_member(self.c,self.uid,self.cid,dict(email='analyst@example.invalid',display_name='Analyst',password=PASS,role='Analyst'))
  with self.assertRaises(accounts.AuthError):observability.dashboard(self.c,uid)
 def test_benefit_currencies_and_points_are_not_mixed(self):
  self.imported();data=observability.dashboard(self.c,self.uid);self.assertTrue(any(c['recorded_cash'] for c in data['companies']));self.assertTrue(any(c['other_benefits'] for c in data['companies']));self.assertTrue(all(isinstance(c['recorded_cash'],dict) for c in data['companies']))
if __name__=='__main__':unittest.main(verbosity=2)
