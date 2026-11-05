"""Workspace-specific reads. Legacy unscoped CRUD is never used by this portal."""
import json
from cmn.accounts import AuthError

def demo_context(c,company_id):
 row=c.execute('''SELECT r.Id AS rule_id,p.ParentCompanyId AS company_id,a.Id AS activity_id FROM IncentiveRule r
 JOIN IncentiveProgram p ON p.Id=r.IncentiveProgramId
 JOIN VehicleActivity a ON a.SourceNamespace=? AND a.OfficialActivityReference='NS-SALE-001'
 WHERE p.ParentCompanyId=? AND p.OfficialProgramReference='SYNTHETIC-FLEET-JOURNEY' AND r.OfficialRuleCode='FLEET-JOURNEY-150' ''',(f'demo.workspace.{company_id}',company_id)).fetchone()
 if row is None:raise ValueError('Prepare the fictional scenario in this workspace first')
 return dict(row)

def summary(c,company_id,membership):
 provider=membership['ProviderId'] if membership['Role']=='Provider' else None
 providers=[dict(r) for r in c.execute('''SELECT DISTINCT p.Id,p.LegalName FROM Provider p JOIN ProviderAuthorization pa ON pa.ProviderId=p.Id
 WHERE pa.ParentCompanyId=? AND (? IS NULL OR p.Id=?) ORDER BY p.Id''',(company_id,provider,provider))]
 activities=[dict(r) for r in c.execute('''SELECT a.Id,a.SourceNamespace,a.OfficialActivityReference,a.ActivityKind,a.ActivityStatus,a.StartedAt,a.EndedAt,p.LegalName AS Provider FROM VehicleActivity a
 JOIN Outlet o ON o.Id=a.IssuingOutletId JOIN Provider p ON p.Id=o.ProviderId
 WHERE (a.SourceNamespace=? OR EXISTS(SELECT 1 FROM CompanyActivity ca WHERE ca.VehicleActivityId=a.Id AND ca.ParentCompanyId=?)) AND (? IS NULL OR p.Id=?) ORDER BY a.Id''',(f'demo.workspace.{company_id}',company_id,provider,provider))]
 runs=[]
 for row in c.execute('SELECT Id,SnapshotJson,CreatedAt FROM IncentiveRun WHERE ParentCompanyId=? ORDER BY Id DESC LIMIT 100',(company_id,)):
  s=json.loads(row['SnapshotJson'])
  if provider is not None and s['beneficiary_id']!=provider:continue
  runs.append({'id':row['Id'],'result':s['result'],'created_at':row['CreatedAt'],'beneficiary':s['beneficiary'],'beneficiary_id':s['beneficiary_id'],'amount_minor':s['reward']['amount_minor'] if s['event_award_id'] else None,'currency':s['reward']['currency'],'fleet_count_before_sale':s['fleet_count_before_sale']})
 fleets=[] if provider else [dict(r) for r in c.execute('SELECT Id,FleetReference,FleetName FROM Fleet WHERE ParentCompanyId=?',(company_id,))]
 from biz.knowledge.base import scoped_records
 records=scoped_records(c,company_id,membership);recorded=[]
 for kind in ['Event','Period']:
  for award in records[kind+'Award']:
   components=[{k:v for k,v in row.items() if k not in ['Id',kind+'AwardId']} for row in records[kind+'AwardComponent'] if row[kind+'AwardId']==award['Id']]
   imported=c.execute('SELECT b.SourceName FROM ImportedRecord i JOIN DataImportBatch b ON b.Id=i.BatchId WHERE i.TableName=? AND i.RecordId=?',(kind+'Award',award['Id'])).fetchone()
   recorded.append({'id':award['Id'],'kind':kind,'status':award['AwardStatus'],'issued_at':award['IssuedAt'],'evaluation_id':award['AcceptedEvaluationId'],'rule_id':award['IncentiveRuleId'],'components':components,'origin':('Prepared sample decision' if 'Reviewed' in imported['SourceName'] else 'Imported source decision') if imported else 'Recorded evaluation'})
 try:demo_context(c,company_id);demo_ready=True
 except ValueError:demo_ready=False
 return {'demo_ready':demo_ready,'providers':providers,'activities':activities,'runs':runs,'fleets':fleets,'recorded_awards':recorded,'role':membership['Role'],'scope':'company_authorized_records'}

def authorize_run(snapshot,membership):
 if membership['Role']=='Provider' and snapshot['beneficiary_id']!=membership['ProviderId']:raise AuthError('Award access denied',403)
 return snapshot

def public_run(snapshot,membership):
 authorize_run(snapshot,membership)
 if membership['Role']!='Provider':return snapshot
 allowed=['company_id','activity_id','rule_id','rule_version_id','beneficiary_id','beneficiary','fleet_count_before_sale','reward','result','checks','evaluated_at','input_hash','event_evaluation_id','event_award_id','run_id']
 return {k:snapshot[k] for k in allowed}
