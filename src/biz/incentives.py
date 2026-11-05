"""Bounded fleet journey policy. No arbitrary rule expressions are executed."""
import json,hashlib
from datetime import datetime,timedelta,timezone
from dal.database import save

def utcnow():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def parse(t):return datetime.strptime(t,'%Y-%m-%dT%H:%M:%SZ')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def allrows(c,q,args=()):return [dict(r) for r in c.execute(q,args)]
def one(c,q,args=()):
 r=c.execute(q,args).fetchone()
 if r is None:raise ValueError('Required record not found')
 return dict(r)
def migrate(c):
 from dal.database import SQL
 c.executescript((SQL/'09_fleet_engine.sql').read_text())

def _snapshot(c,company_id,activity_id,rule_id,now):
 rule=one(c,'''SELECT r.*,p.ParentCompanyId,p.ActiveFrom,p.ActiveTo,p.EventVersionPolicy FROM IncentiveRule r
 JOIN IncentiveProgram p ON p.Id=r.IncentiveProgramId WHERE r.Id=? AND p.ParentCompanyId=?''',(rule_id,company_id))
 if rule['AssessmentBasis']!='Event' or rule['EventVersionPolicy']!='SaleCompletedAt':raise ValueError('Only event rules pinned to SaleCompletedAt are supported')
 sale=one(c,'''SELECT a.*,s.CompletedAt,s.SalePrice,s.Currency,o.ProviderId,p.LegalName AS ProviderName FROM VehicleActivity a
 JOIN Sale s ON s.VehicleActivityId=a.Id JOIN Outlet o ON o.Id=a.IssuingOutletId JOIN Provider p ON p.Id=o.ProviderId WHERE a.Id=?''',(activity_id,))
 when=sale['CompletedAt'];day=when[:10]
 version=one(c,'SELECT * FROM RuleVersion WHERE IncentiveRuleId=? AND EffectiveFrom<=? AND (EffectiveTo IS NULL OR EffectiveTo>?)',(rule_id,day,day))
 try:
  condition=json.loads(version['ConditionExpression']);reward=json.loads(version['RewardSpecification'])
 except (ValueError,TypeError):raise ValueError('Rule must contain structured JSON conditions and reward')
 if set(condition)!={'operation','minimum_fleet_vehicles','service_window_days'} or condition['operation']!='fleet_journey_v1':raise ValueError('Unsupported rule operation or condition fields')
 if type(condition['minimum_fleet_vehicles']) is not int or not 1<=condition['minimum_fleet_vehicles']<=100000:raise ValueError('Invalid fleet threshold')
 if type(condition['service_window_days']) is not int or not 1<=condition['service_window_days']<=365:raise ValueError('Invalid service window')
 if set(reward)!={'amount_minor','currency'} or type(reward['amount_minor']) is not int or not 0<reward['amount_minor']<=100000000 or reward['currency']!='CAD':raise ValueError('Unsupported reward: use positive CAD minor units')
 checks=[];evidence={'sale':sale,'rule':rule,'version':version}
 def check(name,passed,detail):checks.append({'name':name,'passed':bool(passed),'detail':detail})
 check('completed_sale',sale['ActivityStatus']=='Completed' and sale['StartedAt']<=when<=now and sale['RecordedAt']<=now,'Completed sale at or before evaluation cutoff')
 check('program_active',rule['ActiveFrom']<=day and (rule['ActiveTo'] is None or day<rule['ActiveTo']),'Program active at sale completion')
 enrollment=allrows(c,"SELECT * FROM ProgramEnrollment WHERE IncentiveProgramId=? AND ProviderId=? AND EnrollmentStatus='Active' AND ValidFrom<=? AND (ValidTo IS NULL OR ValidTo>?)",(rule['IncentiveProgramId'],sale['ProviderId'],day,day))
 evidence['enrollment']=enrollment;check('program_enrollment',bool(enrollment),'Sale provider enrolled at sale completion')
 def authorizations(activity,kind,timestamp):
  d=timestamp[:10]
  return allrows(c,'''SELECT pa.*,ca.Id AS CapabilityAuthorizationId,ca.CapabilityId,ca.ValidFrom AS CapabilityValidFrom,ca.ValidTo AS CapabilityValidTo
  FROM ProviderAuthorization pa JOIN CapabilityAuthorization ca ON ca.ProviderAuthorizationId=pa.Id JOIN Capability k ON k.Id=ca.CapabilityId
  WHERE pa.ParentCompanyId=? AND pa.ProviderId=? AND ca.OutletId=? AND k.ExistingCapabilityDesignation=?
  AND pa.AuthorizationStatus='Active' AND ca.AuthorizationStatus='Active'
  AND pa.ValidFrom<=? AND (pa.ValidTo IS NULL OR pa.ValidTo>?) AND ca.ValidFrom<=? AND (ca.ValidTo IS NULL OR ca.ValidTo>?)''',(company_id,activity['ProviderId'],activity['IssuingOutletId'],kind,d,d,d,d))
 evidence['sale_authorization']=authorizations(sale,'Sale',when);check('sale_authorization',bool(evidence['sale_authorization']),'Authorized issuing outlet and sale capability')
 fleets=allrows(c,'SELECT * FROM Fleet WHERE ParentCompanyId=? AND OwnerAccountId=? ORDER BY Id',(company_id,sale['CustomerAccountId']))
 if len(fleets)>1:raise ValueError('Ambiguous fleet context: this rule requires one fleet per sale account')
 fleet=fleets[0] if fleets else None;evidence['fleet']=fleet
 memberships=[]
 if fleet:memberships=allrows(c,'''SELECT f.*,v.VIN,m.Manufacturer FROM FleetVehicleAssignment f JOIN Vehicle v ON v.Id=f.VehicleId
 JOIN VehicleModel m ON m.Id=v.VehicleModelId WHERE f.FleetId=? AND f.ValidFrom<? AND (f.ValidTo IS NULL OR f.ValidTo>=?) AND f.VehicleId!=? AND m.Manufacturer=(SELECT Manufacturer FROM VehicleModel WHERE Id=(SELECT VehicleModelId FROM Vehicle WHERE Id=?)) ORDER BY f.Id''',(fleet['Id'],when,when,sale['VehicleId'],sale['VehicleId']))
 evidence['fleet_assignments']=memberships
 count=len({x['VehicleId'] for x in memberships});check('pre_sale_fleet',fleet is not None and count>=condition['minimum_fleet_vehicles'],f"{count} existing same-manufacturer vehicles; minimum {condition['minimum_fleet_vehicles']}")
 def identity(a,b):
  if a==b:return {'same_account':a}
  x,y=sorted([a,b]);links=allrows(c,"SELECT * FROM CustomerIdentityLink WHERE AccountAId=? AND AccountBId=? AND VerificationStatus='Verified' AND RevokedAt IS NULL AND VerifiedAt<=?",(x,y,now))
  return links[0] if links else None
 services=allrows(c,'''SELECT a.*,s.Id AS ServiceId,s.CompletedAt,s.ServiceType,s.Outcome,o.ProviderId FROM VehicleActivity a
 JOIN Service s ON s.VehicleActivityId=a.Id JOIN Outlet o ON o.Id=a.IssuingOutletId WHERE a.VehicleId=? AND a.ActivityStatus='Completed' AND a.StartedAt>=? AND s.CompletedAt<=? ORDER BY s.CompletedAt,a.Id''',(sale['VehicleId'],when,now))
 deadline=(parse(when)+timedelta(days=condition['service_window_days'])).strftime('%Y-%m-%dT%H:%M:%SZ')
 candidates=[];selected=None
 for service in services:
  sid=identity(sale['CustomerAccountId'],service['CustomerAccountId']);sauth=authorizations(service,'Service',service['StartedAt'])
  service_ok=service['CompletedAt']>=service['StartedAt'] and service['CompletedAt']<=deadline and service['RecordedAt']<=now and sid and sauth
  rentals=allrows(c,'''SELECT a.*,r.Id AS RentalId,r.ReturnedAt,r.ReplacementPurpose,r.ReplacementForServiceId,o.ProviderId FROM Rental r
  JOIN VehicleActivity a ON a.Id=r.VehicleActivityId JOIN Outlet o ON o.Id=a.IssuingOutletId
  WHERE r.ReplacementForServiceId=? AND a.ActivityStatus='Completed' AND a.VehicleId!=? AND a.StartedAt>=? AND r.ReturnedAt<=? AND r.ReturnedAt<=? ORDER BY a.Id''',(service['ServiceId'],sale['VehicleId'],service['StartedAt'],service['CompletedAt'],now))
  for rental in rentals:
   rid=identity(sale['CustomerAccountId'],rental['CustomerAccountId']);rauth=authorizations(rental,'Rental',rental['StartedAt'])
   ok=bool(service_ok and rid and rauth and rental['ReturnedAt']>=rental['StartedAt'] and rental['RecordedAt']<=now)
   candidate={'service':service,'rental':rental,'service_identity':sid,'rental_identity':rid,'service_authorization':sauth,'rental_authorization':rauth,'valid':ok};candidates.append(candidate)
   if ok and selected is None:selected=candidate
 evidence['candidates']=candidates;evidence['selected']=selected
 check('verified_service_and_replacement',selected is not None,'Completed service within window, different replacement vehicle during service, verified direct accounts and authorized providers')
 result='Qualified' if all(x['passed'] for x in checks) else 'Rejected'
 return {'company_id':company_id,'activity_id':activity_id,'rule_id':rule_id,'rule_version_id':version['Id'],'beneficiary_id':sale['ProviderId'],'beneficiary':sale['ProviderName'],'fleet_count_before_sale':count,'rule_conditions':condition,'reward':reward,'result':result,'checks':checks,'evidence':evidence}

def evaluate(c,company_id,activity_id,rule_id,evaluated_at=None):
 now=evaluated_at or utcnow();parse(now)
 # A write reservation serializes imports and duplicate evaluation attempts.
 c.execute('BEGIN IMMEDIATE')
 try:
  snapshot=_snapshot(c,company_id,activity_id,rule_id,now)
  digest=hashlib.sha256(canonical(snapshot).encode()).hexdigest()
  previous=c.execute("SELECT * FROM IncentiveRun WHERE ParentCompanyId=? AND VehicleActivityId=? AND IncentiveRuleId=? AND Result='Qualified' ORDER BY Id DESC LIMIT 1",(company_id,activity_id,rule_id)).fetchone()
  if previous:
   answer=json.loads(previous['SnapshotJson']);answer.update(run_id=previous['Id'],replayed=True,review_required=previous['InputHash']!=digest);c.commit();return answer
  previous=c.execute('SELECT * FROM IncentiveRun WHERE VehicleActivityId=? AND RuleVersionId=? AND InputHash=?',(activity_id,snapshot['rule_version_id'],digest)).fetchone()
  if previous:
   answer=json.loads(previous['SnapshotJson']);answer.update(run_id=previous['Id'],replayed=True,review_required=False);c.commit();return answer
  evaluation_id=award_id=None
  if snapshot['result']=='Qualified':
   evidence=snapshot['evidence'];selected=evidence['selected'];day=evidence['sale']['CompletedAt'][:10]
   evaluation_id=save(c,'EventEvaluation',dict(VehicleActivityId=activity_id,RuleVersionId=snapshot['rule_version_id'],Result='Qualified',Reason='All fleet_journey_v1 conditions passed',QualificationDate=day,EvaluatedAt=now,DecisionEvidenceReference='urn:retail-mesh:snapshot:sha256:'+digest))
   for act in [evidence['sale'],selected['service'],selected['rental']]:save(c,'EventEvaluationActivity',dict(EventEvaluationId=evaluation_id,VehicleActivityId=act['Id'],EvidenceRole=act['ActivityKind']))
   seen=set()
   for link in [selected['service_identity'],selected['rental_identity']]:
    if 'Id' in link and link['Id'] not in seen:
     seen.add(link['Id']);save(c,'EventEvaluationIdentity',dict(EventEvaluationId=evaluation_id,CustomerIdentityLinkId=link['Id'],VerificationOutcomeUsed=link['VerificationStatus'],VerifiedAtUsed=link['VerifiedAt'],EvidenceReferenceUsed=link['EvidenceReference']))
   award_id=save(c,'EventAward',dict(VehicleActivityId=activity_id,IncentiveRuleId=rule_id,AwardStatus='Issued',IssuedAt=now,AcceptedEvaluationId=evaluation_id,FirstComponentId=-1))
   amount=snapshot['reward']['amount_minor'];currency=snapshot['reward']['currency']
   cid=save(c,'EventAwardComponent',dict(EventAwardId=award_id,RewardType='Cash',UnitScheme='ISO4217',UnitCode=currency,BenefitValue=f'{amount//100}.{amount%100:02d}',Currency=currency,ValidFrom=now[:10],ValidTo=None))
   c.execute('UPDATE EventAward SET FirstComponentId=? WHERE Id=?',(cid,award_id))
  snapshot.update(evaluated_at=now,input_hash=digest,event_evaluation_id=evaluation_id,event_award_id=award_id)
  cur=c.execute('''INSERT INTO IncentiveRun(ParentCompanyId,VehicleActivityId,IncentiveRuleId,RuleVersionId,InputHash,Result,SnapshotJson,CreatedAt,EventEvaluationId,EventAwardId)
  VALUES(?,?,?,?,?,?,?,?,?,?)''',(company_id,activity_id,rule_id,snapshot['rule_version_id'],digest,snapshot['result'],canonical(snapshot),now,evaluation_id,award_id))
  c.commit();snapshot.update(run_id=cur.lastrowid,replayed=False,review_required=False);return snapshot
 except Exception:c.rollback();raise

def get_run(c,company_id,run_id):
 row=one(c,'SELECT * FROM IncentiveRun WHERE Id=? AND ParentCompanyId=?',(run_id,company_id));snapshot=json.loads(row['SnapshotJson']);snapshot['run_id']=row['Id'];return snapshot
