"""Provider claims, concern conversations and bounded policy explanations."""
import json,re,secrets
from datetime import date
from decimal import Decimal,InvalidOperation
from cmn import accounts
from biz import workspaces
REVIEWERS=['CompanyAdmin','CompanyOperator']

def member(c,actor,company_id):return accounts.require_company(c,actor,company_id,['CompanyAdmin','CompanyOperator','Provider'])
def provider(c,actor,company_id):return accounts.require_company(c,actor,company_id,['Provider'])
def scope_clause(m,alias=''):
    return (' AND '+alias+'ProviderId=?',[m['ProviderId']]) if m['Role']=='Provider' else ('',[])
def claim_row(c,actor,cid,claim_id):
    m=member(c,actor,cid);extra,params=scope_clause(m)
    row=c.execute('SELECT * FROM IncentiveClaim WHERE Id=? AND ParentCompanyId=?'+extra,(claim_id,cid,*params)).fetchone()
    if row is None:raise accounts.AuthError('Claim is not available in this provider/company scope',404)
    return row,m

def claim_options(c,actor,cid):
    m=provider(c,actor,cid)
    rules=[dict(r) for r in c.execute('''SELECT DISTINCT r.Id,r.RuleName,r.AssessmentBasis FROM IncentiveRule r JOIN IncentiveProgram p ON p.Id=r.IncentiveProgramId JOIN ProgramEnrollment e ON e.IncentiveProgramId=p.Id WHERE p.ParentCompanyId=? AND e.ProviderId=? AND e.EnrollmentStatus='Active' AND e.ValidFrom<=date('now') AND (e.ValidTo IS NULL OR e.ValidTo>date('now')) AND p.ActiveFrom<=date('now') AND (p.ActiveTo IS NULL OR p.ActiveTo>date('now')) ORDER BY r.Id''',(cid,m['ProviderId']))]
    return {'rules':rules,'activities':workspaces.summary(c,cid,m)['activities']}

def claims(c,actor,cid):
    m=member(c,actor,cid);extra,params=scope_clause(m);rows=[]
    for row in c.execute('SELECT * FROM IncentiveClaim WHERE ParentCompanyId=?'+extra+' ORDER BY Id DESC',(cid,*params)):
        item=dict(row);item['ProviderName']=c.execute('SELECT LegalName FROM Provider WHERE Id=?',(row['ProviderId'],)).fetchone()[0];item['history']=[dict(r) for r in c.execute('SELECT ActorId,Action,Message,CreatedAt FROM IncentiveClaimEvent WHERE ClaimId=? ORDER BY Id',(row['Id'],))];rows.append(item)
    return {'claims':rows,'options':claim_options(c,actor,cid) if m['Role']=='Provider' else None,'role':m['Role']}

def claim_values(c,actor,cid,data):
    options=claim_options(c,actor,cid);rule=next((r for r in options['rules'] if r['Id']==int(data.get('rule_id',0))),None)
    if rule is None:raise ValueError('Choose a rule from an active program your provider is enrolled in')
    kind=rule['AssessmentBasis'];values={'IncentiveRuleId':rule['Id'],'ClaimType':kind,'VehicleActivityId':None,'PeriodStart':None,'PeriodEnd':None,
        'Statement':accounts.text(data.get('statement'),'Claim explanation',2000),'EvidenceReference':accounts.text(data.get('evidence_reference'),'Evidence reference',500),'RequestedAmountMinor':None,'Currency':None}
    if kind=='Event':
        activity=int(data.get('activity_id',0))
        if activity not in {a['Id'] for a in options['activities']}:raise accounts.AuthError('Activity is not owned by this provider in this company',403)
        values['VehicleActivityId']=activity
    else:
        start=data.get('period_start','');end=data.get('period_end','')
        try:
            if len(start)!=10 or len(end)!=10 or date.fromisoformat(end)<=date.fromisoformat(start):raise ValueError()
        except (ValueError,TypeError):raise ValueError('Use a valid start-inclusive/end-exclusive reporting period')
        values['PeriodStart']=start;values['PeriodEnd']=end
    if data.get('requested_amount') not in [None,'']:
        try:
            amount=Decimal(str(data['requested_amount']))
            if not amount.is_finite() or amount<0 or amount*100!=(amount*100).to_integral_value() or amount>Decimal('100000000'):raise InvalidOperation
        except InvalidOperation:raise ValueError('Requested cash amount must be non-negative with at most two decimal places')
        currency=str(data.get('currency','CAD')).upper()
        if not re.fullmatch('[A-Z]{3}',currency):raise ValueError('Use a three-letter currency code')
        values['RequestedAmountMinor']=int(amount*100);values['Currency']=currency
    return values

def submit_claim(c,actor,cid,data):
    m=provider(c,actor,cid);values=claim_values(c,actor,cid,data);stamp=accounts.now()
    c.execute('BEGIN IMMEDIATE')
    try:
        claim_id=data.get('claim_id')
        if claim_id:
            old,_=claim_row(c,actor,cid,int(claim_id))
            if old['Status']!='ChangesNeeded':raise ValueError('Only claims returned for changes can be resubmitted')
            if old['Version']!=int(data.get('version',0)):raise accounts.AuthError('Claim changed; refresh first',409)
            c.execute('UPDATE IncentiveClaim SET '+','.join(k+'=?' for k in values)+",Status='Submitted',Version=Version+1,UpdatedAt=? WHERE Id=?",(*values.values(),stamp,claim_id));action='resubmitted'
        else:
            columns=list(values);claim_id=c.execute('INSERT INTO IncentiveClaim(Reference,ParentCompanyId,ProviderId,SubmittedBy,'+','.join(columns)+',CreatedAt,UpdatedAt) VALUES('+','.join('?' for _ in range(len(columns)+6))+')',('CLM-'+secrets.token_hex(6).upper(),cid,m['ProviderId'],actor,*values.values(),stamp,stamp)).lastrowid;action='submitted'
        c.execute('INSERT INTO IncentiveClaimEvent(ClaimId,ActorId,Action,Message,CreatedAt) VALUES(?,?,?,?,?)',(claim_id,actor,action,values['Statement'],stamp));accounts.audit(c,actor,cid,'claim.'+action,claim_id);c.commit();return {'claim_id':int(claim_id),'status':'Submitted'}
    except Exception:c.rollback();raise

def review_claim(c,actor,cid,data):
    accounts.require_company(c,actor,cid,REVIEWERS);c.execute('BEGIN IMMEDIATE')
    try:
        row,_=claim_row(c,actor,cid,int(data.get('claim_id',0)))
        if row['Version']!=int(data.get('version',0)):raise accounts.AuthError('Claim changed; refresh first',409)
        target=data.get('status');allowed={'Submitted':{'UnderReview'},'UnderReview':{'ChangesNeeded','Approved','Rejected'}}
        if target not in allowed.get(row['Status'],set()):raise ValueError('Start review before deciding this claim')
        note=accounts.text(data.get('note'),'Review explanation',1000)
        c.execute('UPDATE IncentiveClaim SET Status=?,ReviewNote=?,Version=Version+1,UpdatedAt=? WHERE Id=?',(target,note,accounts.now(),row['Id']))
        c.execute('INSERT INTO IncentiveClaimEvent(ClaimId,ActorId,Action,Message,CreatedAt) VALUES(?,?,?,?,?)',(row['Id'],actor,target,note,accounts.now()));accounts.audit(c,actor,cid,'claim.'+target,row['Id']);c.commit()
        return {'claim_id':row['Id'],'status':target,'message':'Claim decision recorded. No award or payment was generated.'}
    except Exception:c.rollback();raise

def concerns(c,actor,cid):
    m=member(c,actor,cid);extra,params=scope_clause(m);rows=[]
    for row in c.execute('SELECT * FROM ProviderConcern WHERE ParentCompanyId=?'+extra+' ORDER BY Id DESC',(cid,*params)):
        item=dict(row);item['messages']=[dict(r) for r in c.execute('SELECT ActorId,Message,CreatedAt FROM ProviderConcernMessage WHERE ConcernId=? ORDER BY Id',(row['Id'],))];rows.append(item)
    return {'concerns':rows,'role':m['Role']}

def concern_action(c,actor,cid,data):
    m=member(c,actor,cid);message=accounts.text(data.get('message'),'Concern or response',2000);c.execute('BEGIN IMMEDIATE')
    try:
        concern_id=data.get('concern_id')
        if concern_id:
            extra,params=scope_clause(m);row=c.execute('SELECT * FROM ProviderConcern WHERE Id=? AND ParentCompanyId=?'+extra,(int(concern_id),cid,*params)).fetchone()
            if row is None:raise accounts.AuthError('Concern is not in this provider/company scope',404)
            if row['Version']!=int(data.get('version',0)):raise accounts.AuthError('Concern changed; refresh first',409)
            if m['Role']=='Provider':
                if row['Status']=='Closed':raise ValueError('Raise a new concern after a conversation is closed')
                target='Open' if row['Status']=='Resolved' else row['Status']
            else:
                target=data.get('status',row['Status'])
                if target not in ['Open','UnderReview','Resolved','Closed']:raise ValueError('Choose a supported concern status')
            c.execute('UPDATE ProviderConcern SET Status=?,Version=Version+1,UpdatedAt=? WHERE Id=?',(target,accounts.now(),concern_id))
        else:
            if m['Role']!='Provider':raise accounts.AuthError('Provider access required to raise a concern',403)
            kind=data.get('kind','Incentive')
            if kind not in ['Incentive','WorkspaceAccess']:raise ValueError('Choose an incentive concern or workspace-access request')
            workspace_name=accounts.text(data.get('workspace_name'),'Requested workspace name',200) if kind=='WorkspaceAccess' else ''
            claim_id=int(data['claim_id']) if data.get('claim_id') and kind=='Incentive' else None
            if claim_id:claim_row(c,actor,cid,claim_id)
            concern_id=c.execute('INSERT INTO ProviderConcern(ParentCompanyId,ProviderId,RaisedBy,ClaimId,Kind,RequestedWorkspaceName,Subject,CreatedAt,UpdatedAt) VALUES(?,?,?,?,?,?,?,?,?)',(cid,m['ProviderId'],actor,claim_id,kind,workspace_name,accounts.text(data.get('subject'),'Subject',200),accounts.now(),accounts.now())).lastrowid;target='Open'
        c.execute('INSERT INTO ProviderConcernMessage(ConcernId,ActorId,Message,CreatedAt) VALUES(?,?,?,?)',(concern_id,actor,message,accounts.now()));accounts.audit(c,actor,cid,'concern.'+target,concern_id);c.commit();return {'concern_id':int(concern_id),'status':target}
    except Exception:c.rollback();raise

def chat(c,actor,cid,data):
    m=provider(c,actor,cid);question=accounts.text(data.get('question'),'Question',1000);q=question.lower();sources=[]
    if any(word in q for word in ['status','my claims','claim requests','submitted claim']):
        rows=claims(c,actor,cid)['claims'];text='Your provider has '+str(len(rows))+' claim requests. '+(' '.join(row['Reference']+': '+row['Status']+'.' for row in rows[:10]) if rows else 'Use My claims to request an incentive review.');sources=[{'type':'IncentiveClaim','id':r['Id']} for r in rows[:10]]
    elif any(word in q for word in ['concern','disagree','wrong','appeal']):text='Use My concerns to raise a calculation question or dispute, optionally linking one of your claims. The company operator can respond and you can track the conversation there.'
    else:
        descriptions=[]
        for option in claim_options(c,actor,cid)['rules']:
            version=c.execute("SELECT * FROM RuleVersion WHERE IncentiveRuleId=? AND EffectiveFrom<=date('now') AND (EffectiveTo IS NULL OR EffectiveTo>date('now')) ORDER BY EffectiveFrom DESC LIMIT 1",(option['Id'],)).fetchone()
            if not version:continue
            condition=json.loads(version['ConditionExpression']);spec=json.loads(version['RewardSpecification']);criteria=condition.get('criteriaByCapability')
            if criteria:
                codes={r[0] for r in c.execute("SELECT DISTINCT cp.ExistingCapabilityDesignation FROM CapabilityAuthorization ca JOIN Capability cp ON cp.Id=ca.CapabilityId JOIN ProviderAuthorization pa ON pa.Id=ca.ProviderAuthorizationId WHERE pa.ParentCompanyId=? AND pa.ProviderId=? AND pa.AuthorizationStatus='Active' AND ca.AuthorizationStatus='Active' AND ca.ValidFrom<=date('now') AND (ca.ValidTo IS NULL OR ca.ValidTo>date('now'))",(cid,m['ProviderId']))}
                cap=next((v for v in condition.get('capabilityPriority',[]) if v in codes),None)
                labels={'ACTIVITY-COMPLETED-COUNT':'completed activities','SALE-VALUE-CAD':'completed sales value (CAD)','REPLACEMENT-RENTAL-COUNT':'completed replacement rentals','RENTAL-DURATION-DAYS':'billable rental days','SERVICE-COMPLETED-COUNT':'completed services'}
                checks=', '.join(labels.get(code,code)+' at least '+str(value) for code,value in criteria.get(cap,{}).items());benefits=spec.get('benefitsByCapability',{}).get(cap,[])
                descriptions.append(option['RuleName']+': '+(checks or 'Contact the operator for your capability criteria')+'. Benefits: '+', '.join(str(b['amount'])+' '+(b.get('currency') or b.get('unit','')) for b in benefits)+'.')
            else:descriptions.append(option['RuleName']+': '+ '; '.join(condition.get('eventChecks',[]))+'. Benefits: '+', '.join(str(b['amount'])+' '+(b.get('currency') or b.get('unit','')) for b in spec.get('benefits',[]))+'.')
            sources.append({'type':'RuleVersion','id':version['Id']})
        text=(' '.join(descriptions) if descriptions else 'Your provider is not enrolled in an active incentive program. Ask the company operator about program enrolment.')+' These are policy explanations, not an eligibility decision or payment. Reviewed sample decisions were prepared offline; claim acceptance remains a separate review.'
    return {'answer':text,'sources':sources,'mode':'provider_scoped_policy_assistant','live_llm':False,'scope':'Your provider and active company only'}
