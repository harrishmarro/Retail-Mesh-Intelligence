from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'src/dal/models/relational';m=json.loads((p/'dictionary.json').read_text())
s=[]
def trigger(name,table,event,condition,message):
 s.append(f"CREATE TRIGGER {name} BEFORE {event} ON {table} WHEN {condition} BEGIN SELECT RAISE(ABORT, '{message}'); END;")
# Constraint triggers run for both inserts and updates.
for event in ['INSERT','UPDATE']:
 suffix=event.lower()
 trigger('ActivityAccount_'+suffix,'VehicleActivity',event,'(SELECT ProviderId FROM Outlet WHERE Id=NEW.IssuingOutletId) != (SELECT ProviderId FROM CustomerAccount WHERE Id=NEW.CustomerAccountId)','Activity account must belong to issuing provider')
 trigger('GrantProvider_'+suffix,'CapabilityAuthorization',event,'(SELECT ProviderId FROM ProviderAuthorization WHERE Id=NEW.ProviderAuthorizationId) != (SELECT ProviderId FROM Outlet WHERE Id=NEW.OutletId)','Capability grant must match outlet provider')
 for scope in ['Event','Period']:
  trigger(scope+'Basis_'+suffix,scope+'Evaluation',event,f"(SELECT r.AssessmentBasis FROM RuleVersion v JOIN IncentiveRule r ON r.Id=v.IncentiveRuleId WHERE v.Id=NEW.RuleVersionId) != '{scope}'",'Rule assessment basis does not match evaluation')
  trigger(scope+'Effective_'+suffix,scope+'Evaluation',event,"NOT EXISTS (SELECT 1 FROM RuleVersion v WHERE v.Id=NEW.RuleVersionId AND NEW.QualificationDate >= v.EffectiveFrom AND (v.EffectiveTo IS NULL OR NEW.QualificationDate < v.EffectiveTo))",'No effective rule version at qualification date')
  subject='VehicleActivityId' if scope=='Event' else 'ProviderId'
  where=f'e.{subject}=NEW.{subject} AND v.IncentiveRuleId=NEW.IncentiveRuleId'
  if scope=='Period':where+=' AND e.PeriodStart=NEW.PeriodStart AND e.PeriodEnd=NEW.PeriodEnd'
  trigger(scope+'AwardAcceptance_'+suffix,scope+'Award',event,f"NOT EXISTS (SELECT 1 FROM {scope}Evaluation e JOIN RuleVersion v ON v.Id=e.RuleVersionId WHERE e.Id=NEW.AcceptedEvaluationId AND e.Result='Qualified' AND {where})",'Award requires qualified evaluation for the same subject and rule')
  # Issued benefits must have at least one component, enforced on transitions and by audit below.
 for t in ['RuleVersion','MetricDefinitionVersion','ProviderAuthorization','ProgramEnrollment','CapabilityAuthorization']:
  mm=m[t];start='EffectiveFrom' if 'EffectiveFrom' in mm['fields'] else 'ValidFrom';end='EffectiveTo' if start=='EffectiveFrom' else 'ValidTo'
  keys=[x for x in mm['ck'] if x!=start]
  same=' AND '.join('x.'+x+'=NEW.'+x for x in keys)
  trigger(t+'NoOverlap_'+suffix,t,event,f"EXISTS (SELECT 1 FROM {t} x WHERE x.Id != COALESCE(NEW.Id,-1) AND {same} AND (x.{end} IS NULL OR NEW.{start}<x.{end}) AND (NEW.{end} IS NULL OR x.{start}<NEW.{end}))",'Overlapping effective intervals are not allowed')
# Evaluations are final immutable assertions in this bounded implementation. Evidence can be inserted once,
# but never overwritten/deleted; source links retain frozen identity evidence attributes.
for scope in ['Event','Period']:
 for event in ['UPDATE','DELETE']:trigger(scope+'EvaluationFrozen_'+event.lower(),scope+'Evaluation',event,'1','Final evaluations are immutable; use a new rule version')
 for kind in ['Identity','Activity','Measurement']:
  for event in ['UPDATE','DELETE']:trigger(scope+kind+'Frozen_'+event.lower(),scope+'Evaluation'+kind,event,'1','Decision evidence is append-only')
  # Do not allow appending after an award has accepted this evaluation.
  trigger(scope+kind+'Closed_insert',scope+'Evaluation'+kind,'INSERT',f'EXISTS (SELECT 1 FROM {scope}Award WHERE AcceptedEvaluationId=NEW.{scope}EvaluationId)','Accepted decision evidence is frozen')
 for t in ['RuleVersion','MetricDefinitionVersion','VehicleActivity','PerformanceMeasurement']:
  # Freeze source evidence once referenced by a final evaluation.
  ref='RuleVersionId' if t=='RuleVersion' else ('VehicleActivityId' if t=='VehicleActivity' else 'PerformanceMeasurementId')
  table=scope+'Evaluation' if t=='RuleVersion' else scope+'Evaluation'+('Activity' if t=='VehicleActivity' else 'Measurement')
  if t=='MetricDefinitionVersion':continue
  for event in ['UPDATE','DELETE']:
   trigger(scope+t+'EvidenceFrozen_'+event.lower(),t,event,f'EXISTS (SELECT 1 FROM {table} WHERE {ref}=OLD.Id)','Source used by a final evaluation is immutable')
(p/'sql/02_integrity.sql').write_text('\n'.join(s)+'\n')
# Freeze subtype values and definitions that supplied final decision evidence.
for subtype in ['Sale','Rental','Service']:
 for event in ['UPDATE','DELETE']:
  condition=' OR '.join(f'EXISTS (SELECT 1 FROM {scope}EvaluationActivity WHERE VehicleActivityId=OLD.VehicleActivityId)' for scope in ['Event','Period'])
  condition+=' OR EXISTS (SELECT 1 FROM EventEvaluation WHERE VehicleActivityId=OLD.VehicleActivityId)'
  trigger(subtype+'Frozen_'+event.lower(),subtype,event,condition,'Subtype used in final decision is immutable')
for event in ['UPDATE','DELETE']:
 trigger('MetricDefinitionFrozen_'+event.lower(),'MetricDefinitionVersion',event,'EXISTS (SELECT 1 FROM PerformanceMeasurement m WHERE m.MetricDefinitionVersionId=OLD.Id AND (EXISTS (SELECT 1 FROM EventEvaluationMeasurement WHERE PerformanceMeasurementId=m.Id) OR EXISTS (SELECT 1 FROM PeriodEvaluationMeasurement WHERE PerformanceMeasurementId=m.Id)))','Metric definition used in final decision is immutable')
for scope in ['Event','Period']:
 trigger(scope+'IdentitySnapshot_insert',scope+'EvaluationIdentity','INSERT',"NOT EXISTS (SELECT 1 FROM CustomerIdentityLink l WHERE l.Id=NEW.CustomerIdentityLinkId AND l.VerificationStatus=NEW.VerificationOutcomeUsed AND l.VerifiedAt=NEW.VerifiedAtUsed AND l.EvidenceReference=NEW.EvidenceReferenceUsed AND l.VerificationStatus='Verified' AND l.RevokedAt IS NULL)",'Identity evidence must match a currently verified source assertion')
(p/'sql/02_integrity.sql').write_text('\n'.join(s)+'\n')
for table,ref,check in [
 ('MeasurementContribution','PerformanceMeasurementId',"EXISTS (SELECT 1 FROM EventEvaluationMeasurement WHERE PerformanceMeasurementId={id}) OR EXISTS (SELECT 1 FROM PeriodEvaluationMeasurement WHERE PerformanceMeasurementId={id})"),
 ('RuleMetric','RuleVersionId',"EXISTS (SELECT 1 FROM EventEvaluation WHERE RuleVersionId={id}) OR EXISTS (SELECT 1 FROM PeriodEvaluation WHERE RuleVersionId={id})")]:
 for event in ['INSERT','UPDATE','DELETE']:
  pseudo='NEW' if event=='INSERT' else 'OLD'
  trigger(table+'Frozen_'+event.lower(),table,event,check.format(id=pseudo+'.'+ref),'Contributions or metric requirements used in final decisions are immutable')
for event in ['UPDATE','DELETE']:
 trigger('RuleIdentityFrozen_'+event.lower(),'IncentiveRule',event,'EXISTS (SELECT 1 FROM RuleVersion v WHERE v.IncentiveRuleId=OLD.Id AND (EXISTS (SELECT 1 FROM EventEvaluation WHERE RuleVersionId=v.Id) OR EXISTS (SELECT 1 FROM PeriodEvaluation WHERE RuleVersionId=v.Id)))','Rule used in final decision is immutable')
(p/'sql/02_integrity.sql').write_text('\n'.join(s)+'\n')
# Business identities are stable after insertion. Updates change descriptive attributes,
# not which real-world record the row denotes; create a new record for a new identity.
for table,mm in m.items():
 condition=' OR '.join('NEW.'+col+' IS NOT OLD.'+col for col in mm['ck'])
 trigger(table+'StableIdentity_update',table,'UPDATE',condition,'Business candidate keys are immutable; create a new identity instead')
# An outlet/account cannot be reassigned to another legal provider (their provider is
# part of their stable business key). Subject vehicle catalogue identity is likewise stable.
for event in ['UPDATE']:
 trigger('VehicleEvidenceIdentity_update','Vehicle',event,"(NEW.VehicleModelId IS NOT OLD.VehicleModelId) AND EXISTS (SELECT 1 FROM VehicleActivity a WHERE a.VehicleId=OLD.Id AND (EXISTS (SELECT 1 FROM EventEvaluation WHERE VehicleActivityId=a.Id) OR EXISTS (SELECT 1 FROM EventEvaluationActivity WHERE VehicleActivityId=a.Id) OR EXISTS (SELECT 1 FROM PeriodEvaluationActivity WHERE VehicleActivityId=a.Id)))",'Vehicle model used in final evidence is immutable')
(p/'sql/02_integrity.sql').write_text('\n'.join(s)+'\n')
