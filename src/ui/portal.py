"""Authenticated loopback portal. Legacy database-wide routes are intentionally absent."""
from http.server import BaseHTTPRequestHandler
from http.cookies import SimpleCookie,CookieError
from urllib.parse import urlparse,parse_qs,unquote
import json,secrets,sqlite3,hmac,time
from dal.database import ROOT,connect
from cmn import accounts
from biz import demo,workspaces
from biz.incentives import evaluate,get_run
from biz.ai.explanations import configuration,narrate
ANON_CSRF=secrets.token_urlsafe(32)
COOKIE='retail_mesh_session'
class PortalHandler(BaseHTTPRequestHandler):
 def handle_one_request(self):
  self._started=time.perf_counter();self._request_id=secrets.token_hex(12);self._company_id=None;self._status_code=500
  try:super().handle_one_request()
  finally:
   route=urlparse(getattr(self,'path','')).path
   if route.startswith('/api/'):
    try:
     c=connect(self.server.db)
     with c:
      # Known route names only: never log arbitrary URLs, query strings or credentials.
      known=route if route in API_ROUTES else '/api/unknown'
      c.execute('INSERT INTO RequestObservation(ParentCompanyId,RequestId,Route,Method,StatusCode,DurationMs,RecordedAt) VALUES(?,?,?,?,?,?,?)',(self._company_id,self._request_id,known,getattr(self,'command','UNKNOWN'),self._status_code,round((time.perf_counter()-self._started)*1000,2),accounts.now()))
      c.execute('DELETE FROM RequestObservation WHERE RecordedAt<?',(accounts.now()-7*86400,))
     c.close()
    except sqlite3.Error:pass
 def send_response(self,code,message=None):
  self._status_code=code;super().send_response(code,message)
 def download(self,payload,mime,filename):
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Disposition','attachment; filename="'+filename+'"');self.end_headers();self.wfile.write(payload)

 def end_headers(self):
  self.send_header('X-Request-ID',getattr(self,'_request_id',''));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','no-referrer');super().end_headers()
 def reply(self,obj,status=200,cookie=None):
  b=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(b)
 def cookie(self,token='',clear=False):return f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age='+('0' if clear else str(8*3600))
 def token(self):
  try:
   jar=SimpleCookie();jar.load(self.headers.get('Cookie',''));return jar[COOKIE].value if COOKIE in jar else None
  except CookieError:return None
 def origin(self):
  allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
  if self.headers.get('Host') not in allowed:raise accounts.AuthError('Invalid request host',403)
  origin=self.headers.get('Origin')
  if origin and origin not in {'http://'+x for x in allowed}:raise accounts.AuthError('Cross-origin requests are not allowed',403)
  if self.command=='POST' and self.headers.get('Sec-Fetch-Site')=='cross-site':raise accounts.AuthError('Cross-site requests are not allowed',403)
 def user(self,c):return accounts.session(c,self.token())
 def company(self,c,user,company_id,roles=None):
  membership=accounts.require_company(c,user['Id'],int(company_id),roles);self._company_id=int(company_id);return membership
 def handle_error(self,e):
  if isinstance(e,accounts.AuthError):self.reply({'error':str(e)},e.status)
  elif isinstance(e,sqlite3.IntegrityError):self.reply({'error':'The requested change conflicts with an existing identity or relationship'},409)
  else:self.reply({'error':str(e)},400)
 def do_GET(self):
  c=None
  try:
   self.origin();u=urlparse(self.path);q=parse_qs(u.query)
   if u.path=='/':
    index=ROOT/'src/ui/react-dist/index.html'
    if not index.is_file():self.reply({'error':'React frontend is not built. Run npm ci and npm run build in src/ui/react/.'},503);return
    b=index.read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");self.end_headers();self.wfile.write(b);return
   if u.path.startswith('/assets/'):
    assets=(ROOT/'src/ui/react-dist/assets').resolve();file=(ROOT/'src/ui/react-dist'/unquote(u.path).lstrip('/')).resolve()
    types={'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf','.svg':'image/svg+xml'}
    if not file.is_relative_to(assets) or not file.is_file() or file.suffix not in types:self.reply({'error':'Asset not found'},404);return
    self.send_response(200);self.send_header('Content-Type',types[file.suffix]);self.end_headers();self.wfile.write(file.read_bytes());return
   c=connect(self.server.db)
   if u.path=='/api/auth/status':
    try:user=self.user(c)
    except accounts.AuthError:user=None
    self.reply({'imported_company_count':c.execute("SELECT COUNT(*) FROM ImportedRecord WHERE TableName='ParentCompany'").fetchone()[0],'needs_setup':c.execute('SELECT 1 FROM AppUser LIMIT 1').fetchone() is None,'user':None if not user else {k:user[k] for k in ['Id','Email','DisplayName']},'csrf':user['CsrfToken'] if user else ANON_CSRF,'workspaces':accounts.memberships(c,user['Id']) if user else [],'ai':configuration()});return
   if u.path=='/api/public/provider-signup':
    from biz.provider_signup import public_portal
    self.reply(public_portal(c,q.get('code',[''])[0]));return
   user=self.user(c)
   if u.path=='/api/workspaces':self.reply(accounts.memberships(c,user['Id']));return
   if not u.path.startswith('/api/workspace/'):raise accounts.AuthError('This route is unavailable in workspace mode',403)
   cid=int(q.get('company_id',['0'])[0]);membership=self.company(c,user,cid)
   if u.path in ['/api/workspace/knowledge','/api/workspace/knowledge-export']:
    self.company(c,user,cid,['CompanyAdmin','CompanyOperator','Analyst'])
   if u.path=='/api/workspace/knowledge':
    from biz.knowledge.base import knowledge_document,validate_document
    doc=knowledge_document(c,cid,membership);doc['validation']=validate_document(doc);self.reply(doc)
   elif u.path=='/api/workspace/knowledge-export':
    from biz.knowledge.base import export_bundle
    self.download(export_bundle(c,cid,membership),'application/zip','retail-mesh-company-'+str(cid)+'-okf.zip')
   elif u.path=='/api/workspace/claims':
    from biz.provider_services import claims
    self.reply(claims(c,user['Id'],cid))
   elif u.path=='/api/workspace/concerns':
    from biz.provider_services import concerns
    self.reply(concerns(c,user['Id'],cid))
   elif u.path=='/api/workspace/provider-signup':
    from biz.provider_signup import portal_settings
    self.reply(portal_settings(c,user['Id'],cid))
   elif u.path=='/api/workspace/applications':
    from biz.onboarding import listing
    self.reply(listing(c,user['Id'],cid))
   elif u.path=='/api/workspace/observability':
    self.company(c,user,cid,['CompanyAdmin'])
    from biz.observability import dashboard
    self.reply(dashboard(c,user['Id']))
   elif u.path=='/api/workspace/status':self.reply(workspaces.summary(c,cid,membership))
   elif u.path=='/api/workspace/run':self.reply(workspaces.public_run(get_run(c,cid,int(q.get('run_id',['0'])[0])),membership))
   elif u.path=='/api/workspace/graph':
    self.company(c,user,cid,['CompanyAdmin','CompanyOperator','Analyst'])
    from biz.knowledge.graph import build_graph,validate_graph
    snapshot=get_run(c,cid,int(q.get('run_id',['0'])[0]));g=build_graph(snapshot);validation=validate_graph(g)
    if not validation['conforms']:raise ValueError('Graph failed validation')
    fmt=q.get('format',['turtle'])[0]
    if fmt not in ['turtle','json-ld']:raise ValueError('Unsupported graph format')
    b=g.serialize(format=fmt).encode();self.send_response(200);self.send_header('Content-Type','text/turtle' if fmt=='turtle' else 'application/ld+json');self.send_header('Content-Disposition','attachment; filename="workspace-run-'+str(snapshot['run_id'])+('.ttl"' if fmt=='turtle' else '.jsonld"'));self.end_headers();self.wfile.write(b)
   elif u.path=='/api/workspace/members':
    self.company(c,user,cid,['CompanyAdmin']);self.reply([dict(r) for r in c.execute('SELECT u.Id,u.Email,u.DisplayName,m.Role,m.ProviderId,m.Status FROM CompanyMembership m JOIN AppUser u ON u.Id=m.UserId WHERE m.ParentCompanyId=?',(cid,))])
   elif u.path=='/api/workspace/audit':
    self.company(c,user,cid,['CompanyAdmin']);self.reply([dict(r) for r in c.execute('SELECT Id,UserId,Action,TargetReference,CreatedAt FROM WorkspaceAuditEvent WHERE ParentCompanyId=? ORDER BY Id DESC LIMIT 100',(cid,))])
   else:self.reply({'error':'Not found'},404)
  except (accounts.AuthError,ValueError,TypeError,KeyError,sqlite3.Error) as e:self.handle_error(e)
  finally:
   if c:c.close()
 def do_POST(self):
  c=None
  try:
   self.origin()
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Use application/json')
   size=int(self.headers.get('Content-Length','0'))
   if not 1<=size<=65536:raise ValueError('Invalid request size')
   data=json.loads(self.rfile.read(size))
   if not isinstance(data,dict):raise ValueError('JSON object required')
   c=connect(self.server.db);path=urlparse(self.path).path
   if path in ['/api/public/provider-submit','/api/public/provider-status','/api/public/provider-resubmit']:
    expected=ANON_CSRF
    try:expected=self.user(c)['CsrfToken']
    except accounts.AuthError:pass
    if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),expected):raise accounts.AuthError('Invalid request token',403)
    from biz.provider_signup import submit,applicant_status,resubmit
    if path.endswith('provider-submit'):self.reply(submit(c,data))
    elif path.endswith('provider-status'):self.reply(applicant_status(c,data.get('token')))
    else:self.reply(resubmit(c,data))
    return
   if path in ['/api/auth/setup','/api/auth/login','/api/auth/activate-provider']:
    expected=ANON_CSRF
    if path.endswith('activate-provider'):
     try:expected=self.user(c)['CsrfToken']
     except accounts.AuthError:pass
    if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),expected):raise accounts.AuthError('Invalid request token',403)
    if path.endswith('activate-provider'):
     from biz.onboarding import activate
     self.reply(activate(c,data.get('token'),data.get('password')));return
    if path.endswith('setup'):accounts.bootstrap(c,data)
    token,csrf=accounts.login(c,data.get('email'),data.get('password'));self.reply({'csrf':csrf},cookie=self.cookie(token));return
   user=self.user(c)
   if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),user['CsrfToken']):raise accounts.AuthError('Invalid session token',403)
   if path=='/api/auth/logout':accounts.logout(c,user);self.reply({'message':'Signed out'},cookie=self.cookie(clear=True));return
   if path=='/api/auth/change-password':
    accounts.change_password(c,user,data.get('current_password'),data.get('new_password'));self.reply({'message':'Password changed. All sessions were revoked; sign in again.'},cookie=self.cookie(clear=True));return
   if path=='/api/workspaces':
    if not any(m['Role']=='CompanyAdmin' for m in accounts.memberships(c,user['Id'])):raise accounts.AuthError('Company administrator access required to create a company',403)
    with c:cid=accounts.create_company(c,user['Id'],data)
    self.reply({'company_id':cid});return
   if not path.startswith('/api/workspace/'):raise accounts.AuthError('This route is unavailable in workspace mode',403)
   cid=int(data.get('company_id',0));membership=self.company(c,user,cid)
   if path=='/api/workspace/provider-signup':
    from biz.provider_signup import configure
    self.reply(configure(c,user['Id'],cid,data))
   elif path=='/api/workspace/review-provider-application':
    from biz.provider_signup import review_application
    self.reply(review_application(c,user['Id'],cid,data))
   elif path in ['/api/workspace/claims','/api/workspace/review-claim','/api/workspace/concerns','/api/workspace/provider-chat']:
    from biz.provider_services import submit_claim,review_claim,concern_action,chat
    function={'/api/workspace/claims':submit_claim,'/api/workspace/review-claim':review_claim,'/api/workspace/concerns':concern_action,'/api/workspace/provider-chat':chat}[path]
    self.reply(function(c,user['Id'],cid,data))
   elif path=='/api/workspace/knowledge-ask':
    self.company(c,user,cid,['CompanyAdmin','CompanyOperator','Analyst'])
    from biz.knowledge.base import answer
    self.reply(answer(c,cid,membership,data.get('question')))
   elif path=='/api/workspace/import-csv':
    self.company(c,user,cid,['CompanyAdmin'])
    from biz.csv_import import ingest
    self.reply(ingest(c,ROOT/'data/preprocessed/RetailMesh_Reviewed_CSV_Data.zip',user['Id']))
   elif path in ['/api/workspace/application-draft','/api/workspace/application-check','/api/workspace/application-transition','/api/workspace/application-invite']:
    self.company(c,user,cid,['CompanyAdmin','CompanyOperator'])
    if path.endswith('application-draft'):raise accounts.AuthError('New applications must be submitted through the separate provider signup page',403)
    from biz.onboarding import save_draft,record_check,transition,issue_invitation
    functions={'/api/workspace/application-draft':save_draft,'/api/workspace/application-check':record_check,'/api/workspace/application-transition':transition,'/api/workspace/application-invite':issue_invitation}
    self.reply(functions[path](c,user['Id'],cid,data))
   elif path=='/api/workspace/seed-demo':
    self.company(c,user,cid,['CompanyAdmin']);ctx=demo.prepare(c,cid)
    with c:accounts.audit(c,user['Id'],cid,'demo.prepared',ctx['activity_id'])
    self.reply(ctx)
   elif path=='/api/workspace/evaluate':
    self.company(c,user,cid,['CompanyAdmin']);ctx=workspaces.demo_context(c,cid);result=evaluate(c,cid,ctx['activity_id'],ctx['rule_id'])
    with c:accounts.audit(c,user['Id'],cid,'rule.evaluated',result['run_id'])
    self.reply(result)
   elif path=='/api/workspace/ask':
    from biz.knowledge.graph import graph_answer
    snapshot=workspaces.authorize_run(get_run(c,cid,int(data.get('run_id',0))),membership);question=str(data.get('question',''))
    if not 1<=len(question)<=1000:raise ValueError('Question must have 1 to 1000 characters')
    if membership['Role']=='Provider':
     result={'answer':f"Your provider award result is {snapshot['result']}. "+(f"Calculated amount: {snapshot['reward']['currency']} {snapshot['reward']['amount_minor']/100:.2f}." if snapshot['event_award_id'] else 'No award was issued.')+' Detailed cross-provider evidence requires company analyst access.','mode':'provider_summary','checks':snapshot['checks'],'sources':[{'type':'IncentiveRun','id':snapshot['run_id']},{'type':'RuleVersion','id':snapshot['rule_version_id']}],'live_llm':False,'ai_status':'role_restricted'}
    else:result=narrate(graph_answer(snapshot,question),question,enabled=data.get('use_ai') is True)
    with c:accounts.audit(c,user['Id'],cid,'explanation.requested',snapshot['run_id'])
    self.reply(result)
   elif path=='/api/workspace/members':self.reply({'user_id':accounts.add_member(c,user['Id'],cid,data)})
   elif path=='/api/workspace/revoke-member':accounts.revoke_member(c,user['Id'],cid,int(data.get('user_id',0)));self.reply({'message':'Membership revoked'})
   else:self.reply({'error':'Not found'},404)
  except (accounts.AuthError,ValueError,TypeError,KeyError,sqlite3.Error) as e:self.handle_error(e)
  finally:
   if c:c.close()
 def log_message(self,*args):pass

API_ROUTES=set(['/api/auth/status', '/api/auth/setup', '/api/auth/login', '/api/auth/logout', '/api/auth/change-password', '/api/auth/activate-provider', '/api/workspaces', '/api/workspace/status', '/api/workspace/run', '/api/workspace/graph', '/api/workspace/members', '/api/workspace/audit', '/api/workspace/revoke-member', '/api/workspace/seed-demo', '/api/workspace/evaluate', '/api/workspace/ask', '/api/workspace/knowledge', '/api/workspace/knowledge-export', '/api/workspace/knowledge-ask', '/api/workspace/applications', '/api/workspace/observability', '/api/workspace/import-csv', '/api/workspace/application-draft', '/api/workspace/application-check', '/api/workspace/application-transition', '/api/workspace/application-invite'])

API_ROUTES.update(['/api/public/provider-signup', '/api/public/provider-submit', '/api/public/provider-status', '/api/public/provider-resubmit', '/api/workspace/provider-signup', '/api/workspace/review-provider-application', '/api/workspace/claims', '/api/workspace/review-claim', '/api/workspace/concerns', '/api/workspace/provider-chat'])
