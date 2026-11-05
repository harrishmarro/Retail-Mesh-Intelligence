"""Local password/session authentication and per-request company authorization."""
import base64,hashlib,hmac,re,secrets,time
from cmn.paths import SQL
ITERATIONS=600000
class AuthError(Exception):
 def __init__(self,message='Authentication required',status=401):super().__init__(message);self.status=status

def migrate(c):
 c.executescript((SQL/'10_workspaces.sql').read_text())
 c.executescript((SQL/'11_operations.sql').read_text())
 from cmn.migrations import upgrade_signup
 upgrade_signup(c)
 c.executescript((SQL/'12_signup_claims.sql').read_text())
 columns={r[1] for r in c.execute('PRAGMA table_info(ProviderConcern)')}
 with c:
  if 'Kind' not in columns:c.execute("ALTER TABLE ProviderConcern ADD COLUMN Kind TEXT NOT NULL DEFAULT 'Incentive' CHECK(Kind IN ('Incentive','WorkspaceAccess'))")
  if 'RequestedWorkspaceName' not in columns:c.execute("ALTER TABLE ProviderConcern ADD COLUMN RequestedWorkspaceName TEXT NOT NULL DEFAULT ''")
def now():return int(time.time())
def email(value):
 if not isinstance(value,str) or len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):raise ValueError('Enter a valid email address')
 return value.strip().lower()
def text(value,label,limit=200):
 if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError(label+' is required and must be at most '+str(limit)+' characters')
 return value.strip()
def hash_password(password):
 if not isinstance(password,str) or not 12<=len(password)<=256:raise ValueError('Password must have 12 to 256 characters')
 salt=secrets.token_bytes(16);digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,ITERATIONS)
 return f'pbkdf2_sha256${ITERATIONS}$'+base64.b64encode(salt).decode()+'$'+base64.b64encode(digest).decode()
def verify_password(password,encoded):
 if not isinstance(password,str) or len(password)>256:return False
 try:
  algorithm,count,salt,expected=encoded.split('$')
  if algorithm!='pbkdf2_sha256' or int(count)!=ITERATIONS:return False
  actual=hashlib.pbkdf2_hmac('sha256',password.encode(),base64.b64decode(salt),int(count));return hmac.compare_digest(actual,base64.b64decode(expected))
 except (ValueError,TypeError):return False
DUMMY_HASH='pbkdf2_sha256$600000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
def audit(c,user_id,company_id,action,target=''):
 c.execute('INSERT INTO WorkspaceAuditEvent(UserId,ParentCompanyId,Action,TargetReference,CreatedAt) VALUES(?,?,?,?,?)',(user_id,company_id,action,str(target),now()))
def create_user(c,username,name,password):
 normalized=email(username);encoded=hash_password(password)
 return c.execute('INSERT INTO AppUser(Email,DisplayName,PasswordHash,CreatedAt) VALUES(?,?,?,?)',(normalized,text(name,'Display name'),encoded,now())).lastrowid

def create_company(c,user_id,data):
 name=text(data.get('company_name'),'Company name');jurisdiction=text(data.get('jurisdiction'),'Registration jurisdiction',50);registration=text(data.get('registration'),'Business registration',100)
 cid=c.execute('INSERT INTO ParentCompany(RegistrationJurisdiction,BusinessRegistrationNumber,LegalName) VALUES(?,?,?)',(jurisdiction,registration,name)).lastrowid
 c.execute("INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role) VALUES(?,?,'CompanyAdmin')",(user_id,cid));audit(c,user_id,cid,'workspace.created',cid);return cid

def bootstrap(c,data):
 c.execute('BEGIN IMMEDIATE')
 try:
  if c.execute('SELECT 1 FROM AppUser LIMIT 1').fetchone():raise AuthError('Initial setup is already complete',409)
  uid=create_user(c,data.get('email'),data.get('display_name'),data.get('password'))
  imported=c.execute("SELECT RecordId FROM ImportedRecord WHERE TableName='ParentCompany' ORDER BY RecordId LIMIT 1").fetchone()
  if data.get('manage_imported') in [True,'on']:
   if imported is None:raise ValueError('Import the supplied companies before selecting this setup option')
   cid=imported['RecordId'];c.execute("INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role) VALUES(?,?,'CompanyAdmin')",(uid,cid));audit(c,uid,cid,'workspace.initial_admin_assigned',cid)
  else:cid=create_company(c,uid,data)
  from biz.csv_import import grant_imported_companies
  for batch in c.execute('SELECT Id FROM DataImportBatch').fetchall():grant_imported_companies(c,uid,batch['Id'])
  c.commit();return uid,cid
 except Exception:c.rollback();raise

def login(c,username,password):
 normalized=email(username);stamp=now();identity=hashlib.sha256(normalized.encode()).hexdigest()
 # The reservation prevents concurrent attempts from racing around the account throttle.
 c.execute('BEGIN IMMEDIATE')
 try:
  failures=c.execute('SELECT COUNT(*) FROM LoginAttempt WHERE IdentityKey=? AND AttemptedAt>? AND Success=0',(identity,stamp-900)).fetchone()[0]
  if failures>=6:raise AuthError('Too many sign-in attempts; try again after 15 minutes',429)
  user=c.execute('SELECT * FROM AppUser WHERE Email=?',(normalized,)).fetchone()
  good=verify_password(password,user['PasswordHash'] if user else DUMMY_HASH) and user is not None and user['Status']=='Active'
  c.execute('INSERT INTO LoginAttempt(IdentityKey,AttemptedAt,Success) VALUES(?,?,?)',(identity,stamp,int(good)))
  if not good:c.commit();raise AuthError('Invalid email or password')
  c.execute('DELETE FROM LoginAttempt WHERE IdentityKey=?',(identity,))
  token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
  c.execute('INSERT INTO AuthSession(TokenHash,UserId,CsrfToken,CreatedAt,ExpiresAt) VALUES(?,?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['Id'],csrf,stamp,stamp+8*3600));audit(c,user['Id'],None,'session.created');c.commit();return token,csrf
 except Exception:
  if c.in_transaction:c.rollback()
  raise

def session(c,token):
 if not token or len(token)>200:raise AuthError()
 row=c.execute('''SELECT s.Id AS SessionId,s.CsrfToken,u.Id,u.Email,u.DisplayName FROM AuthSession s JOIN AppUser u ON u.Id=s.UserId
 WHERE s.TokenHash=? AND s.Revoked=0 AND s.ExpiresAt>? AND u.Status='Active' ''',(hashlib.sha256(token.encode()).hexdigest(),now())).fetchone()
 if row is None:raise AuthError('Session expired or revoked; sign in again')
 return dict(row)
def logout(c,user):
 with c:c.execute('UPDATE AuthSession SET Revoked=1 WHERE Id=?',(user['SessionId'],));audit(c,user['Id'],None,'session.revoked')
def memberships(c,user_id):
 return [dict(r) for r in c.execute("SELECT m.ParentCompanyId AS company_id,p.LegalName AS company_name,m.Role,m.ProviderId FROM CompanyMembership m JOIN ParentCompany p ON p.Id=m.ParentCompanyId WHERE m.UserId=? AND m.Status='Active' ORDER BY p.LegalName",(user_id,))]
def require_company(c,user_id,company_id,roles=None):
 row=c.execute("SELECT * FROM CompanyMembership WHERE UserId=? AND ParentCompanyId=? AND Status='Active'",(user_id,company_id)).fetchone()
 if row is None or (roles and row['Role'] not in roles):raise AuthError('Workspace access denied',403)
 if row['Role']=='Provider' and not c.execute("SELECT 1 FROM ProviderAuthorization WHERE ParentCompanyId=? AND ProviderId=? AND AuthorizationStatus='Active' AND ValidFrom<=date('now') AND (ValidTo IS NULL OR ValidTo>date('now'))",(company_id,row['ProviderId'])).fetchone():raise AuthError('Provider authorization is not active',403)
 return dict(row)
def add_member(c,actor,company_id,data):
 c.execute('BEGIN IMMEDIATE')
 try:
  require_company(c,actor,company_id,['CompanyAdmin']);role=data.get('role');provider=data.get('provider_id')
  if role not in ['CompanyAdmin','CompanyOperator','Analyst','Provider']:raise ValueError('Choose a supported role')
  if role=='Provider':
   provider=int(provider)
   if not c.execute("SELECT 1 FROM ProviderAuthorization WHERE ParentCompanyId=? AND ProviderId=? AND AuthorizationStatus='Active' AND ValidFrom<=date('now') AND (ValidTo IS NULL OR ValidTo>date('now'))",(company_id,provider)).fetchone():raise AuthError('Provider is not authorized for this workspace',403)
   if c.execute("SELECT 1 FROM ProviderApplication WHERE ParentCompanyId=? AND ProviderId=? AND State!='Provisioned'",(company_id,provider)).fetchone():raise AuthError('Use provider onboarding activation to provision this account',403)
  else:provider=None
  username=email(data.get('email'));existing=c.execute('SELECT Id FROM AppUser WHERE Email=?',(username,)).fetchone()
  uid=existing['Id'] if existing else create_user(c,username,data.get('display_name'),data.get('password'))
  if uid==actor:raise ValueError('Use another administrator to change your own membership')
  c.execute('''INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role,ProviderId) VALUES(?,?,?,?)
   ON CONFLICT(UserId,ParentCompanyId) DO UPDATE SET Role=excluded.Role,ProviderId=excluded.ProviderId,Status='Active' ''',(uid,company_id,role,provider))
  audit(c,actor,company_id,'membership.granted',f'user:{uid};role:{role};provider:{provider}');c.commit();return uid
 except Exception:c.rollback();raise

def revoke_member(c,actor,company_id,user_id):
 with c:
  require_company(c,actor,company_id,['CompanyAdmin'])
  if int(actor)==int(user_id):raise ValueError('Use another company administrator to change your own membership')
  c.execute("UPDATE CompanyMembership SET Status='Revoked' WHERE UserId=? AND ParentCompanyId=?",(user_id,company_id));audit(c,actor,company_id,'membership.revoked',user_id)

def check_password_throttle(c,user_id,password,encoded,purpose):
 identity=hashlib.sha256((purpose+':'+str(user_id)).encode()).hexdigest();stamp=now()
 if c.execute('SELECT COUNT(*) FROM LoginAttempt WHERE IdentityKey=? AND Success=0 AND AttemptedAt>?',(identity,stamp-900)).fetchone()[0]>=6:
  raise AuthError('Too many password attempts; try again after 15 minutes',429)
 if not verify_password(password,encoded):
  c.execute('INSERT INTO LoginAttempt(IdentityKey,AttemptedAt,Success) VALUES(?,?,0)',(identity,stamp));c.commit()
  raise AuthError('Current password is incorrect',400)
 c.execute('DELETE FROM LoginAttempt WHERE IdentityKey=?',(identity,))

def change_password(c,user,current_password,new_password):
 c.execute('BEGIN IMMEDIATE')
 try:
  row=c.execute("SELECT PasswordHash FROM AppUser WHERE Id=? AND Status='Active'",(user['Id'],)).fetchone()
  if row is None:raise AuthError()
  check_password_throttle(c,user['Id'],current_password,row['PasswordHash'],'password-change')
  if current_password==new_password:raise ValueError('Choose a different password')
  encoded=hash_password(new_password)
  c.execute('UPDATE AppUser SET PasswordHash=? WHERE Id=?',(encoded,user['Id']))
  c.execute('UPDATE AuthSession SET Revoked=1 WHERE UserId=?',(user['Id'],))
  audit(c,user['Id'],None,'account.password_changed');c.commit()
 except Exception:
  if c.in_transaction:c.rollback()
  raise
