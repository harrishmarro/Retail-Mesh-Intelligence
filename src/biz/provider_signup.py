"""Opt-in public intake, private applicant tracking and operator review."""
import hashlib,json,secrets
from cmn import accounts
from biz import onboarding

def portal_settings(c,actor,company_id):
    accounts.require_company(c,actor,company_id,['CompanyAdmin','CompanyOperator'])
    row=c.execute('SELECT PublicCode,Enabled FROM ProviderSignupPortal WHERE ParentCompanyId=?',(company_id,)).fetchone()
    return {'enabled':bool(row and row['Enabled']),'public_code':row['PublicCode'] if row else None}

def configure(c,actor,company_id,data):
    with c:
        accounts.require_company(c,actor,company_id,['CompanyAdmin'])
        if not isinstance(data.get('enabled'),bool):raise ValueError('Choose whether provider signup is enabled')
        previous=c.execute('SELECT PublicCode FROM ProviderSignupPortal WHERE ParentCompanyId=?',(company_id,)).fetchone()
        code=previous['PublicCode'] if previous and data.get('rotate') is not True else secrets.token_urlsafe(18)
        c.execute('''INSERT INTO ProviderSignupPortal(ParentCompanyId,PublicCode,Enabled,UpdatedBy,UpdatedAt) VALUES(?,?,?,?,?) ON CONFLICT(ParentCompanyId) DO UPDATE SET PublicCode=excluded.PublicCode,Enabled=excluded.Enabled,UpdatedBy=excluded.UpdatedBy,UpdatedAt=excluded.UpdatedAt''',(company_id,code,int(data['enabled']),actor,accounts.now()))
        accounts.audit(c,actor,company_id,'provider.signup_configured','enabled:'+str(data['enabled']))
    return portal_settings(c,actor,company_id)

def available_programs(c,company_id):
    return [dict(r) for r in c.execute("SELECT Id,ProgramName FROM IncentiveProgram WHERE ParentCompanyId=? AND ActiveFrom<=date('now') AND (ActiveTo IS NULL OR ActiveTo>date('now')) ORDER BY Id",(company_id,))]

def public_portal(c,code):
    if not isinstance(code,str) or not 10<=len(code)<=100:raise accounts.AuthError('Ask the company operator for a valid signup link or code',404)
    row=c.execute('''SELECT p.ParentCompanyId,pc.LegalName FROM ProviderSignupPortal p JOIN ParentCompany pc ON pc.Id=p.ParentCompanyId WHERE p.PublicCode=? AND p.Enabled=1''',(code,)).fetchone()
    if row is None:raise accounts.AuthError('This company signup page is unavailable',404)
    return {'company_id':row['ParentCompanyId'],'company_name':row['LegalName'],'capability_options':sorted(onboarding.CAPABILITIES),'programs':available_programs(c,row['ParentCompanyId'])}

def fields(c,company_id,data):
    values={key:accounts.text(data.get(source),label,limit) for key,source,label,limit in [
        ('LegalName','legal_name','Legal name',200),('RegistrationJurisdiction','jurisdiction','Registration jurisdiction',50),('BusinessRegistrationNumber','registration','Registration number',100),('ContactName','contact_name','Contact name',200),('ContactPhone','contact_phone','Contact phone',40),('OutletName','outlet_name','Outlet name',200),('OutletAddress','outlet_address','Outlet address',500)]}
    values['ApplicantEvidenceReferences']=accounts.text(data.get('supporting_evidence'),'Supporting evidence references',2000)
    values['ContactEmail']=accounts.email(data.get('contact_email'));website=data.get('website','')
    if not isinstance(website,str) or len(website)>300 or (website and not website.startswith(('https://','http://'))):raise ValueError('Website must be an HTTP(S) URL or blank')
    values['Website']=website.strip();caps=data.get('capabilities')
    if not isinstance(caps,list) or not caps or not all(isinstance(x,str) and x in onboarding.CAPABILITIES for x in caps):raise ValueError('Select at least one supported capability')
    values['CapabilitiesJson']=json.dumps(sorted(set(caps)))
    requested=data.get('program_ids',[])
    if not isinstance(requested,list):raise ValueError('Choose requested programs')
    try:programs=sorted({int(x) for x in requested})
    except (ValueError,TypeError):raise ValueError('Invalid requested program')
    if not set(programs)<={p['Id'] for p in available_programs(c,company_id)}:raise ValueError('A requested program is not active in this company')
    values['RequestedProgramsJson']=json.dumps(programs);return values

def submit(c,data):
    portal=public_portal(c,data.get('code'));cid=portal['company_id'];values=fields(c,cid,data);stamp=accounts.now()
    c.execute('BEGIN IMMEDIATE')
    try:
        identity=hashlib.sha256(('signup:'+str(cid)+':'+values['ContactEmail']).encode()).hexdigest()
        if c.execute('SELECT COUNT(*) FROM LoginAttempt WHERE IdentityKey=? AND AttemptedAt>?',(identity,stamp-900)).fetchone()[0]>=3:raise accounts.AuthError('Too many applications; try again in 15 minutes',429)
        c.execute('INSERT INTO LoginAttempt(IdentityKey,AttemptedAt,Success) VALUES(?,?,0)',(identity,stamp))
        columns=list(values)
        aid=c.execute('INSERT INTO ProviderApplication(ParentCompanyId,'+','.join(columns)+",State,CreatedBy,CreatedAt,UpdatedAt) VALUES ("+','.join('?' for _ in range(len(columns)+5))+')',(cid,*values.values(),'Submitted',None,stamp,stamp)).lastrowid
        token=secrets.token_urlsafe(32)
        c.execute('INSERT INTO ProviderApplicationAccess(ApplicationId,TokenHash,CreatedAt,ExpiresAt) VALUES(?,?,?,?)',(aid,hashlib.sha256(token.encode()).hexdigest(),stamp,stamp+30*86400))
        accounts.audit(c,None,cid,'provider.public_submitted','application:'+str(aid));c.commit()
        return {'application_reference':'APP-'+str(aid),'tracking_token':token,'message':'Application submitted for company-operator review. Save your private tracking link; no provider account exists yet.'}
    except Exception:c.rollback();raise

def owned_application(c,token):
    if not isinstance(token,str) or not 30<=len(token)<=200:raise accounts.AuthError('Private application link is invalid or expired',404)
    row=c.execute('''SELECT a.* FROM ProviderApplicationAccess access JOIN ProviderApplication a ON a.Id=access.ApplicationId WHERE access.TokenHash=? AND access.ExpiresAt>?''',(hashlib.sha256(token.encode()).hexdigest(),accounts.now())).fetchone()
    if row is None:raise accounts.AuthError('Private application link is invalid or expired',404)
    return row

def applicant_status(c,token):
    row=owned_application(c,token);item=dict(row);item.pop('CreatedBy',None)
    item['capabilities']=json.loads(item.pop('CapabilitiesJson'));item['program_ids']=json.loads(item.pop('RequestedProgramsJson'))
    note=c.execute("SELECT TargetReference FROM WorkspaceAuditEvent WHERE ParentCompanyId=? AND Action='provider.review_note' AND TargetReference LIKE ? ORDER BY Id DESC LIMIT 1",(row['ParentCompanyId'],'application:'+str(row['Id'])+'; %')).fetchone()
    item['review_note']=note[0].split('; ',1)[1] if note else ''
    item['decision']={'NeedsChanges':'Changes needed','Approved':'Accepted','Provisioned':'Account active'}.get(row['State'],row['State'])
    item['company_name']=c.execute('SELECT LegalName FROM ParentCompany WHERE Id=?',(row['ParentCompanyId'],)).fetchone()[0]
    item['programs']=available_programs(c,row['ParentCompanyId']);item['capability_options']=sorted(onboarding.CAPABILITIES)
    item['activation_available']=bool(c.execute('''SELECT 1 FROM ProviderInvitation WHERE ApplicationId=? AND TokenHash=? AND Revoked=0 AND UsedAt IS NULL AND ExpiresAt>?''',(row['Id'],hashlib.sha256(token.encode()).hexdigest(),accounts.now())).fetchone()) and row['State']=='Approved'
    return item

def resubmit(c,data):
    c.execute('BEGIN IMMEDIATE')
    try:
        row=owned_application(c,data.get('token'))
        if row['State']!='NeedsChanges':raise ValueError('Only applications returned for changes can be edited and resubmitted')
        if row['Version']!=int(data.get('version',0)):raise accounts.AuthError('Application changed; refresh before resubmitting',409)
        values=fields(c,row['ParentCompanyId'],data)
        c.execute('UPDATE ProviderApplication SET '+','.join(k+'=?' for k in values)+",State='Submitted',Version=Version+1,UpdatedAt=? WHERE Id=?",(*values.values(),accounts.now(),row['Id']))
        c.execute('DELETE FROM ProviderValidationCheck WHERE ApplicationId=?',(row['Id'],))
        accounts.audit(c,None,row['ParentCompanyId'],'provider.public_resubmitted','application:'+str(row['Id']));c.commit()
        return {'message':'Changes submitted for a new company-operator review'}
    except Exception:c.rollback();raise

def review_application(c,actor,company_id,data):
    decision=data.get('decision');targets={'Accepted':'Approved','Changes needed':'NeedsChanges','Rejected':'Rejected'}
    if decision not in targets:raise ValueError('Choose Accepted, Changes needed or Rejected')
    note=accounts.text(data.get('note'),'Review explanation',500)
    c.execute('BEGIN IMMEDIATE')
    try:
        row=onboarding.application(c,actor,company_id,int(data.get('application_id',0)),int(data.get('version',0)))
        programs=data.get('program_ids',json.loads(row['RequestedProgramsJson']))
        if not isinstance(programs,list):raise ValueError('Choose program enrolment')
        programs=sorted({int(p) for p in programs})
        if not set(programs)<={p['Id'] for p in available_programs(c,company_id)}:raise ValueError('Program does not belong to this company or is inactive')
        result=onboarding.transition(c,actor,company_id,{**data,'state':targets[decision],'note':note},transaction=False)
        if decision=='Accepted':
            for program in programs:
                if not c.execute("SELECT 1 FROM ProgramEnrollment WHERE IncentiveProgramId=? AND ProviderId=? AND EnrollmentStatus='Active' AND ValidFrom<=date('now') AND (ValidTo IS NULL OR ValidTo>date('now'))",(program,result['provider_id'])).fetchone():
                    c.execute("INSERT INTO ProgramEnrollment(IncentiveProgramId,ProviderId,ValidFrom,EnrollmentStatus) VALUES(?,?,date('now'),'Active')",(program,result['provider_id']))
            access=c.execute('SELECT TokenHash FROM ProviderApplicationAccess WHERE ApplicationId=? AND ExpiresAt>?',(row['Id'],accounts.now())).fetchone()
            if access:
                c.execute('UPDATE ProviderInvitation SET Revoked=1 WHERE ApplicationId=? AND UsedAt IS NULL',(row['Id'],))
                c.execute('INSERT INTO ProviderInvitation(ApplicationId,TokenHash,CreatedBy,CreatedAt,ExpiresAt) VALUES(?,?,?,?,?)',(row['Id'],access['TokenHash'],actor,accounts.now(),accounts.now()+48*3600))
            accounts.audit(c,actor,company_id,'provider.accepted_programs','application:'+str(row['Id'])+'; programs:'+json.dumps(programs))
        c.commit()
        return {**result,'decision':decision,'activation':'The applicant can activate from the private status link after acceptance.'}
    except Exception:c.rollback();raise
