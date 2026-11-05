"""Company-admin review workflow. Applications are staging records until approval."""
import hashlib
import json
import secrets
from datetime import date
from cmn import accounts

CHECKS = {'business_registration':'Business registration evidence',
          'contact_authority':'Authorized contact evidence',
          'capability_compliance':'Capability and compliance evidence'}
CAPABILITIES = {'VehicleSale','VehicleRental','VehicleService','WarrantyRepair','EVDiagnostics'}
TRANSITIONS = {'Draft':{'Submitted'},'Submitted':{'UnderReview'},
               'UnderReview':{'NeedsChanges','Validated','Rejected','Approved'},
               'NeedsChanges':{'Submitted'},'Validated':{'Approved','NeedsChanges'}}


def listing(c, actor, company_id):
    accounts.require_company(c,actor,company_id,['CompanyAdmin','CompanyOperator'])
    result=[]
    for row in c.execute('SELECT * FROM ProviderApplication WHERE ParentCompanyId=? ORDER BY Id DESC',(company_id,)):
        item=dict(row);item['capabilities']=json.loads(item.pop('CapabilitiesJson'))
        item['checks']=[dict(r) for r in c.execute('SELECT CheckCode,EvidenceReference,ReviewedBy,ReviewedAt FROM ProviderValidationCheck WHERE ApplicationId=?',(row['Id'],))]
        item['history']=[dict(r) for r in c.execute("SELECT Id,Action,UserId,CreatedAt,TargetReference FROM WorkspaceAuditEvent WHERE ParentCompanyId=? AND (TargetReference=? OR TargetReference LIKE ?) AND Action LIKE 'provider.%' ORDER BY Id",(company_id,'application:'+str(row['Id']),'application:'+str(row['Id'])+'; %'))]
        notes=[h['TargetReference'].split('; ',1)[1] for h in item['history'] if h['Action']=='provider.review_note']
        item['ReviewNote']=notes[-1] if notes else ''
        result.append(item)
    from biz.provider_signup import portal_settings,available_programs
    return {'applications':result,'check_definitions':CHECKS,'capability_options':sorted(CAPABILITIES),'signup':portal_settings(c,actor,company_id),'program_options':available_programs(c,company_id)}


def application(c, actor, company_id, application_id, version=None):
    accounts.require_company(c,actor,company_id,['CompanyAdmin','CompanyOperator'])
    row=c.execute('SELECT * FROM ProviderApplication WHERE Id=? AND ParentCompanyId=?',(application_id,company_id)).fetchone()
    if row is None:raise accounts.AuthError('Application not found in this company',404)
    if version is not None and row['Version']!=version:raise accounts.AuthError('Application changed; refresh before continuing',409)
    return row


def save_draft(c, actor, company_id, data):
    c.execute('BEGIN IMMEDIATE')
    try:
        accounts.require_company(c,actor,company_id,['CompanyAdmin','CompanyOperator'])
        fields=[accounts.text(data.get(k),label,limit) for k,label,limit in [
            ('legal_name','Provider legal name',200),('jurisdiction','Jurisdiction',50),
            ('registration','Business registration',100),('contact_name','Contact name',200),
            ('outlet_name','Outlet name',200),('outlet_address','Outlet address',500)]]
        contact=accounts.email(data.get('contact_email'))
        capabilities=data.get('capabilities')
        if not isinstance(capabilities,list) or not capabilities or not all(isinstance(x,str) and x in CAPABILITIES for x in capabilities):
            raise ValueError('Choose at least one supported capability')
        values=[*fields[:4],contact,*fields[4:],json.dumps(sorted(set(capabilities)))]
        aid=data.get('application_id');stamp=accounts.now()
        if aid:
            old=application(c,actor,company_id,int(aid),int(data.get('version',0)))
            if old['State'] not in {'Draft','NeedsChanges'}:raise ValueError('Only drafts and returned applications can be edited')
            c.execute('''UPDATE ProviderApplication SET LegalName=?,RegistrationJurisdiction=?,BusinessRegistrationNumber=?,ContactName=?,ContactEmail=?,OutletName=?,OutletAddress=?,CapabilitiesJson=?,UpdatedAt=?,Version=Version+1 WHERE Id=?''',(*values,stamp,aid))
            c.execute('DELETE FROM ProviderValidationCheck WHERE ApplicationId=?',(aid,))
        else:
            aid=c.execute('''INSERT INTO ProviderApplication(ParentCompanyId,LegalName,RegistrationJurisdiction,BusinessRegistrationNumber,ContactName,ContactEmail,OutletName,OutletAddress,CapabilitiesJson,CreatedBy,CreatedAt,UpdatedAt) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(company_id,*values,actor,stamp,stamp)).lastrowid
        accounts.audit(c,actor,company_id,'provider.draft_saved','application:'+str(aid));c.commit();return {'application_id':int(aid)}
    except Exception:c.rollback();raise


def record_check(c, actor, company_id, data):
    c.execute('BEGIN IMMEDIATE')
    try:
        row=application(c,actor,company_id,int(data.get('application_id',0)),int(data.get('version',0)))
        if row['State']!='UnderReview':raise ValueError('Start review before recording evidence')
        code=data.get('check_code')
        if code not in CHECKS:raise ValueError('Unsupported validation check')
        reference=accounts.text(data.get('evidence_reference'),'Evidence reference',500)
        c.execute('''INSERT INTO ProviderValidationCheck(ApplicationId,CheckCode,EvidenceReference,ReviewedBy,ReviewedAt) VALUES(?,?,?,?,?) ON CONFLICT(ApplicationId,CheckCode) DO UPDATE SET EvidenceReference=excluded.EvidenceReference,ReviewedBy=excluded.ReviewedBy,ReviewedAt=excluded.ReviewedAt''',(row['Id'],code,reference,actor,accounts.now()))
        c.execute('UPDATE ProviderApplication SET Version=Version+1,UpdatedAt=? WHERE Id=?',(accounts.now(),row['Id']))
        accounts.audit(c,actor,company_id,'provider.evidence_recorded.'+code,'application:'+str(row['Id'])+'; evidence: '+reference);c.commit();return {'message':'Evidence recorded'}
    except Exception:c.rollback();raise


def transition(c, actor, company_id, data, transaction=True):
    if transaction:c.execute('BEGIN IMMEDIATE')
    try:
        row=application(c,actor,company_id,int(data.get('application_id',0)),int(data.get('version',0)))
        target=data.get('state')
        if target not in TRANSITIONS.get(row['State'],set()):raise ValueError('This onboarding transition is not allowed')
        if target in {'Validated','Approved'}:
            passed={r[0] for r in c.execute('SELECT CheckCode FROM ProviderValidationCheck WHERE ApplicationId=?',(row['Id'],))}
            if passed!=set(CHECKS):raise ValueError('All three evidence checks must be recorded before validation and approval')
        provider=None
        if target=='Approved':
            existing=c.execute('SELECT * FROM Provider WHERE RegistrationJurisdiction=? AND BusinessRegistrationNumber=?',(row['RegistrationJurisdiction'],row['BusinessRegistrationNumber'])).fetchone()
            if existing and existing['LegalName']!=row['LegalName']:raise ValueError('Registered provider name conflicts with the application')
            provider=existing['Id'] if existing else c.execute('INSERT INTO Provider(RegistrationJurisdiction,BusinessRegistrationNumber,LegalName) VALUES(?,?,?)',(row['RegistrationJurisdiction'],row['BusinessRegistrationNumber'],row['LegalName'])).lastrowid
            today=date.today().isoformat()
            authorization=c.execute("SELECT Id FROM ProviderAuthorization WHERE ParentCompanyId=? AND ProviderId=? AND AuthorizationStatus='Active' AND ValidFrom<=? AND (ValidTo IS NULL OR ValidTo>?)",(company_id,provider,today,today)).fetchone()
            pa=authorization['Id'] if authorization else c.execute("INSERT INTO ProviderAuthorization(ParentCompanyId,ProviderId,ValidFrom,AuthorizationStatus) VALUES(?,?,?,'Active')",(company_id,provider,today)).lastrowid
            outlet=c.execute('INSERT INTO Outlet(ProviderId,ExistingOutletReference,OutletName,Address) VALUES(?,?,?,?)',(provider,'onboarding:'+str(company_id)+':'+str(row['Id']),row['OutletName'],row['OutletAddress'])).lastrowid
            for code in json.loads(row['CapabilitiesJson']):
                capability=c.execute('SELECT Id FROM Capability WHERE ExistingCapabilityDesignation=?',(code,)).fetchone()
                cap=capability['Id'] if capability else c.execute('INSERT INTO Capability(ExistingCapabilityDesignation,Description) VALUES(?,?)',(code,'Reviewed provider capability: '+code)).lastrowid
                c.execute("INSERT INTO CapabilityAuthorization(ProviderAuthorizationId,OutletId,CapabilityId,ValidFrom,AuthorizationStatus) VALUES(?,?,?,?,'Active')",(pa,outlet,cap,today))
        if target in {'NeedsChanges','Submitted'}:
            c.execute('DELETE FROM ProviderValidationCheck WHERE ApplicationId=?',(row['Id'],))
        note=accounts.text(data.get('note'),'Review note',500) if target in {'NeedsChanges','Rejected'} or data.get('note') else ''
        c.execute('UPDATE ProviderApplication SET State=?,ProviderId=COALESCE(?,ProviderId),Version=Version+1,UpdatedAt=? WHERE Id=?',(target,provider,accounts.now(),row['Id']))
        accounts.audit(c,actor,company_id,'provider.state.'+target,'application:'+str(row['Id']))
        if note:
            # Notes stay in the audit record; never contain credentials or uploaded documents.
            accounts.audit(c,actor,company_id,'provider.review_note','application:'+str(row['Id'])+'; '+note)
        if transaction:c.commit()
        return {'application_id':row['Id'],'state':target,'provider_id':provider}
    except Exception:
        if transaction:c.rollback()
        raise


def issue_invitation(c, actor, company_id, data):
    c.execute('BEGIN IMMEDIATE')
    try:
        row=application(c,actor,company_id,int(data.get('application_id',0)),int(data.get('version',0)))
        if row['State']!='Approved':raise ValueError('Approve the validated provider before issuing activation access')
        existing=c.execute('SELECT Id FROM AppUser WHERE Email=?',(row['ContactEmail'],)).fetchone()
        if existing and c.execute("SELECT 1 FROM CompanyMembership WHERE UserId=? AND ParentCompanyId=? AND Status='Active'",(existing['Id'],company_id)).fetchone():
            raise ValueError('The contact already has company access; use a separate provider contact account')
        token=secrets.token_urlsafe(32);stamp=accounts.now();expires=stamp+48*3600
        c.execute('UPDATE ProviderInvitation SET Revoked=1 WHERE ApplicationId=? AND UsedAt IS NULL',(row['Id'],))
        c.execute('INSERT INTO ProviderInvitation(ApplicationId,TokenHash,CreatedBy,CreatedAt,ExpiresAt) VALUES(?,?,?,?,?)',(row['Id'],hashlib.sha256(token.encode()).hexdigest(),actor,stamp,expires))
        c.execute('UPDATE ProviderApplication SET Version=Version+1,UpdatedAt=? WHERE Id=?',(stamp,row['Id']))
        accounts.audit(c,actor,company_id,'provider.activation_issued','application:'+str(row['Id']));c.commit()
        return {'token':token,'expires_at':expires,'contact_email':row['ContactEmail'],'delivery':'manual_one_time_link'}
    except Exception:c.rollback();raise


def activate(c, token, password):
    if not isinstance(token,str) or not 30<=len(token)<=200:raise accounts.AuthError('Activation link is invalid or expired',400)
    c.execute('BEGIN IMMEDIATE')
    try:
        row=c.execute('''SELECT i.Id AS InvitationId,i.ExpiresAt,i.UsedAt,i.Revoked,a.* FROM ProviderInvitation i JOIN ProviderApplication a ON a.Id=i.ApplicationId WHERE i.TokenHash=?''',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if row is None or row['Revoked'] or row['UsedAt'] or row['ExpiresAt']<=accounts.now() or row['State']!='Approved':raise accounts.AuthError('Activation link is invalid or expired',400)
        if not c.execute("SELECT 1 FROM ProviderAuthorization WHERE ParentCompanyId=? AND ProviderId=? AND AuthorizationStatus='Active' AND ValidFrom<=date('now') AND (ValidTo IS NULL OR ValidTo>date('now'))",(row['ParentCompanyId'],row['ProviderId'])).fetchone():raise accounts.AuthError('Provider authorization is not active',403)
        existing=c.execute('SELECT * FROM AppUser WHERE Email=?',(row['ContactEmail'],)).fetchone()
        if existing:
            accounts.check_password_throttle(c,existing['Id'],password,existing['PasswordHash'],'activation')
            if existing['Status']!='Active':raise accounts.AuthError('Account is disabled',403)
            uid=existing['Id']
            if c.execute('SELECT 1 FROM CompanyMembership WHERE UserId=? AND ParentCompanyId=?',(uid,row['ParentCompanyId'])).fetchone():raise ValueError('Existing membership must be reviewed by an administrator')
        else:uid=accounts.create_user(c,row['ContactEmail'],row['ContactName'],password)
        c.execute("INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role,ProviderId) VALUES(?,?,'Provider',?)",(uid,row['ParentCompanyId'],row['ProviderId']))
        c.execute('UPDATE ProviderInvitation SET UsedAt=? WHERE Id=?',(accounts.now(),row['InvitationId']))
        c.execute("UPDATE ProviderApplication SET State='Provisioned',Version=Version+1,UpdatedAt=? WHERE Id=?",(accounts.now(),row['Id']))
        accounts.audit(c,uid,row['ParentCompanyId'],'provider.activated','application:'+str(row['Id']));c.commit()
        return {'message':'Provider access activated. Sign in with your email and password.'}
    except Exception:
        if c.in_transaction:c.rollback()
        raise
