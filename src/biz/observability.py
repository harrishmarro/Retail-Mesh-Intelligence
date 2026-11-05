"""Read-only operational dashboard, limited to companies the actor administers."""
import json
import math
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
from cmn import accounts
from biz.workspaces import summary


def dashboard(c,actor):
    companies=[m for m in accounts.memberships(c,actor) if m['Role']=='CompanyAdmin']
    if not companies:raise accounts.AuthError('Company administrator access required',403)
    result=[];events=[];cutoff=accounts.now()-24*3600
    for member in companies:
        cid=member['company_id'];membership=accounts.require_company(c,actor,cid,['CompanyAdmin'])
        data=summary(c,cid,membership)
        states=dict(Counter(r[0] for r in c.execute('SELECT State FROM ProviderApplication WHERE ParentCompanyId=?',(cid,))))
        observations=[dict(r) for r in c.execute('SELECT RequestId,Route,Method,StatusCode,DurationMs,RecordedAt FROM RequestObservation WHERE ParentCompanyId=? AND RecordedAt>=? ORDER BY Id DESC LIMIT 5000',(cid,cutoff))]
        latencies=sorted(r['DurationMs'] for r in observations)
        cash={};other={}
        for award in data['recorded_awards']:
            for component in award['components']:
                if component['RewardType']=='Cash':
                    currency=component['Currency'];cash[currency]=cash.get(currency,Decimal(0))+Decimal(str(component['BenefitValue']))
                else:
                    unit=component['UnitScheme']+':'+component['UnitCode'];other[unit]=other.get(unit,Decimal(0))+Decimal(str(component['BenefitValue']))
        pending=sum(v for k,v in states.items() if k not in {'Provisioned','Rejected'})
        batches=[dict(r) for r in c.execute('''SELECT DISTINCT b.Id,b.SourceName,b.ContentSha256,b.ImportedAt FROM DataImportBatch b JOIN ImportedRecord i ON i.BatchId=b.Id AND i.TableName='ParentCompany' WHERE i.RecordId=?''',(cid,))]
        result.append({'company_id':cid,'company_name':member['company_name'],'providers':len(data['providers']),
                       'activities':len(data['activities']),'engine_runs':len(data['runs']),'recorded_awards':len(data['recorded_awards']),
                       'recorded_cash':{k:str(v) for k,v in cash.items()},'other_benefits':{k:str(v) for k,v in other.items()},
                       'onboarding_states':states,'pending_applications':pending,'imports':batches,
                       'requests_24h':len(observations),'errors_24h':sum(r['StatusCode']>=400 for r in observations),
                       'p95_ms':round(latencies[max(0,math.ceil(len(latencies)*.95)-1)],2) if latencies else None,
                       'request_sample_limit':5000,
                       'active_members':c.execute("SELECT COUNT(*) FROM CompanyMembership WHERE ParentCompanyId=? AND Status='Active'",(cid,)).fetchone()[0]})
        events.extend([{**dict(r),'company_id':cid,'company_name':member['company_name']} for r in c.execute('SELECT Id,UserId,Action,TargetReference,CreatedAt FROM WorkspaceAuditEvent WHERE ParentCompanyId=? ORDER BY Id DESC LIMIT 50',(cid,))])
    return {'generated_at':datetime.now(timezone.utc).isoformat(),'companies':result,
            'events':sorted(events,key=lambda e:e['Id'],reverse=True)[:100],
            'service':{'database':'reachable' if c.execute('SELECT 1').fetchone()[0]==1 else 'unavailable','request_window_hours':24,'retention_days':7},
            'scope':'Only your active CompanyAdmin memberships; Analyst and Provider companies are excluded.',
            'limitations':['Local request telemetry, not external uptime monitoring','Request samples capped at 5000 per company in 24 hours','Money is recorded entitlement value, not payment settlement','No request bodies, passwords, activation tokens or session secrets are recorded']}
