"""Build deterministic synthetic fixtures. No production customer data."""
import sys,sqlite3,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from dal.database import SQL
c=sqlite3.connect(':memory:');c.executescript((SQL/'01_schema.sql').read_text());c.executescript((SQL/'02_integrity.sql').read_text())
statements=['-- Synthetic demonstration data. Explicit fixture IDs are reproducible; application IDs autogenerate.','PRAGMA foreign_keys=ON;','BEGIN;']
def add(t,**d):
 q='INSERT INTO '+t+' ('+','.join(d)+') VALUES ('+','.join('?' for _ in d)+')'
 cur=c.execute(q,list(d.values()));id=cur.lastrowid
 def literal(v):return 'NULL' if v is None else str(v) if isinstance(v,(int,float)) else "'"+str(v).replace("'","''")+"'"
 statements.append('INSERT INTO '+t+' ('+','.join(['Id']+list(d))+') VALUES ('+','.join(map(literal,[id]+list(d.values())))+');');return id
D='2026-01-01';E='2026-12-31';T='2026-10-01T10:00:00Z'
add('ParentCompany',RegistrationJurisdiction='CA-BC',BusinessRegistrationNumber='SYNTHETIC-PC-001',LegalName='Mesh Motors (Synthetic)')
for n in ['Dealer A','Provider B Rental','Provider C Service']:
 p=add('Provider',RegistrationJurisdiction='CA-BC',BusinessRegistrationNumber='DEMO-'+n[0:10],LegalName=n)
 add('Outlet',ProviderId=p,ExistingOutletReference='MAIN',OutletName=n+' Main',Address='Synthetic address, Victoria BC')
 add('CustomerAccount',ProviderId=p,SourceNamespace='demo.crm',ExistingCustomerReference='C-001',DisplayName='Synthetic Customer',Email='demo@example.invalid',PhoneNo=None)
 add('ProviderAuthorization',ParentCompanyId=1,ProviderId=p,ValidFrom=D,ValidTo=None,AuthorizationStatus='Active')
for a,b in [(1,2),(1,3),(2,3)]:add('CustomerIdentityLink',AccountAId=a,AccountBId=b,VerificationStatus='Verified',VerificationMethod='Synthetic consented evidence',VerifiedAt=T,RevokedAt=None,EvidenceReference=f'demo:identity:{a}:{b}')
for i,n in enumerate(['Sale','Rental','Service'],1):
 add('Capability',ExistingCapabilityDesignation=n,Description=n+' operations')
 add('CapabilityAuthorization',ProviderAuthorizationId=i,OutletId=i,CapabilityId=i,ValidFrom=D,ValidTo=None,AuthorizationStatus='Active')
add('VehicleModel',Manufacturer='Mesh',CatalogueNamespace='demo.catalogue',ManufacturerModelCode='M1',ModelYear=2026,TrimCode='BASE',ModelName='Demonstrator')
for vin in ['1HGCM82633A004352','1HGCM82633A004353']:add('Vehicle',VIN=vin,LifecycleStatus='Active',VehicleModelId=1)
for kind,provider,vehicle,ref in [('Sale',1,1,'SALE-001'),('Service',3,1,'SVC-001'),('Rental',2,2,'RENT-001')]:
 a=add('VehicleActivity',IssuingOutletId=provider,SourceNamespace='demo.ops',ActivityKind=kind,OfficialActivityReference=ref,ActivityStatus='Completed',StartedAt=T,EndedAt='2026-10-03T10:00:00Z',RecordedAt=T,CustomerAccountId=provider,VehicleId=vehicle,**{kind+'Id':-1})
 details={'Sale':dict(SalePrice=30000,Currency='CAD',CompletedAt=T),'Service':dict(ServiceType='Warranty',Outcome='Repaired',CompletedAt='2026-10-03T10:00:00Z'),'Rental':dict(RentalCharge=100,Currency='CAD',ReturnedAt='2026-10-03T10:00:00Z',ReplacementForServiceId=1,ReplacementPurpose='Warranty replacement')}[kind]
 s=add(kind,VehicleActivityId=a,**details)
 q=f'UPDATE VehicleActivity SET {kind}Id={s} WHERE Id={a};';c.execute(q);statements.append(q)
add('IncentiveProgram',ParentCompanyId=1,OfficialProgramReference='DEMO-2026',ProgramName='Connected Journey',ActiveFrom=D,ActiveTo=None,EventVersionPolicy='QualificationDate',PeriodVersionPolicy='QualificationDate')
for p in [1,2,3]:add('ProgramEnrollment',IncentiveProgramId=1,ProviderId=p,ValidFrom=D,ValidTo=None,EnrollmentStatus='Active')
add('MetricDefinitionVersion',ParentCompanyId=1,OfficialMetricCode='SERVICE-COUNT',EffectiveFrom=D,EffectiveTo=None,MetricName='Completed services',DefinitionExpression='COUNT completed Service activities',UnitScheme='count',UnitCode='service')
add('PerformanceMeasurement',ProviderId=3,MetricDefinitionVersionId=1,PeriodStart='2026-10-01',PeriodEnd='2026-11-01',MeasuredValue=1,CalculatedAt='2026-11-01T00:00:00Z')
add('MeasurementContribution',PerformanceMeasurementId=1,VehicleActivityId=2,ContributionRole='Completed service')
for basis in ['Event','Period']:
 rule=add('IncentiveRule',IncentiveProgramId=1,OfficialRuleCode=basis.upper()+'-01',RuleName=basis+' demonstration',AssessmentBasis=basis)
 add('RuleVersion',IncentiveRuleId=rule,EffectiveFrom=D,EffectiveTo=None,ConditionExpression=json.dumps({'operation':'manual_verified_demo','basis':basis}),RewardSpecification='100 CAD event / 10 points period, synthetic')
 add('RuleMetric',RuleVersionId=rule,MetricDefinitionVersionId=1,MetricRole='Evidence')
 subj={'VehicleActivityId':1} if basis=='Event' else {'ProviderId':3,'PeriodStart':'2026-10-01','PeriodEnd':'2026-11-01'}
 add(basis+'Evaluation',**subj,RuleVersionId=rule,Result='Qualified',Reason='Manually verified synthetic acceptance scenario',QualificationDate='2026-10-03',EvaluatedAt='2026-11-01T01:00:00Z',DecisionEvidenceReference='demo:decision:'+basis)
 add(basis+'EvaluationMeasurement',**{basis+'EvaluationId':1},PerformanceMeasurementId=1,EvidenceRole='Supporting metric')
 add(basis+'EvaluationActivity',**{basis+'EvaluationId':1},VehicleActivityId=2,EvidenceRole='Supporting service')
 add(basis+'EvaluationIdentity',**{basis+'EvaluationId':1},CustomerIdentityLinkId=2,VerificationOutcomeUsed='Verified',VerifiedAtUsed=T,EvidenceReferenceUsed='demo:identity:1:3')
 add(basis+'Award',**subj,IncentiveRuleId=rule,AwardStatus='Issued',IssuedAt='2026-11-01T02:00:00Z',AcceptedEvaluationId=1,FirstComponentId=-1)
 add(basis+'AwardComponent',**{basis+'AwardId':1},RewardType='Cash' if basis=='Event' else 'Points',UnitScheme='ISO4217' if basis=='Event' else 'demo.points',UnitCode='CAD' if basis=='Event' else 'POINT',BenefitValue=100 if basis=='Event' else 10,Currency='CAD' if basis=='Event' else None,ValidFrom='2026-11-01',ValidTo=None)
 q=f'UPDATE {basis}Award SET FirstComponentId=1 WHERE Id=1;';c.execute(q);statements.append(q)
c.commit();assert not c.execute('PRAGMA foreign_key_check').fetchall();statements.append('COMMIT;');(SQL/'03_seed.sql').write_text('\n'.join(statements)+'\n')
print('Seed covers every relation')
