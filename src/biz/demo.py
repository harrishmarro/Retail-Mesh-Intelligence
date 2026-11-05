"""Idempotent fictional acceptance scenario from the supplied 3MT presentation."""
import json
from dal.database import save
from biz.incentives import migrate

def prepare(c,company_id=None):
 migrate(c)
 namespace='demo.northstar' if company_id is None else f'demo.workspace.{int(company_id)}'
 with c:
  c.execute('BEGIN IMMEDIATE')
  existing=c.execute("SELECT r.Id AS RuleId,p.ParentCompanyId FROM IncentiveRule r JOIN IncentiveProgram p ON p.Id=r.IncentiveProgramId WHERE p.OfficialProgramReference='SYNTHETIC-FLEET-JOURNEY' AND r.OfficialRuleCode='FLEET-JOURNEY-150' AND ((? IS NULL AND p.ParentCompanyId=(SELECT Id FROM ParentCompany WHERE RegistrationJurisdiction='DEMO' AND BusinessRegistrationNumber='SYNTHETIC-NORTHSTAR')) OR p.ParentCompanyId=?)",(company_id,company_id)).fetchone()
  if existing:
   a=c.execute("SELECT Id FROM VehicleActivity WHERE SourceNamespace=? AND OfficialActivityReference='NS-SALE-001'",(namespace,)).fetchone()
   return {'company_id':existing['ParentCompanyId'],'rule_id':existing['RuleId'],'activity_id':a['Id'],'synthetic':True}
  company=company_id or save(c,'ParentCompany',dict(RegistrationJurisdiction='DEMO',BusinessRegistrationNumber='SYNTHETIC-NORTHSTAR',LegalName='Northstar Motors (fictional)'))
  providers=[];outlets=[];accounts=[]
  for kind,name in [('Sale','Maple Motors'),('Rental','Island Rentals'),('Service','Harbour Service')]:
   p=save(c,'Provider',dict(RegistrationJurisdiction='DEMO',BusinessRegistrationNumber=('SYNTHETIC-'+kind.upper() if company_id is None else f'SYNTHETIC-{company_id}-'+kind.upper()),LegalName=name+' (fictional)'));providers.append(p)
   o=save(c,'Outlet',dict(ProviderId=p,ExistingOutletReference='DEMO-MAIN',OutletName=name+' Demo Outlet',Address='Fictional location'));outlets.append(o)
   a=save(c,'CustomerAccount',dict(ProviderId=p,SourceNamespace='demo.northstar.crm',ExistingCustomerReference='CEDAR-001',DisplayName='Cedar Logistics (fictional)',Email=None,PhoneNo=None));accounts.append(a)
   pa=save(c,'ProviderAuthorization',dict(ParentCompanyId=company,ProviderId=p,ValidFrom='2026-01-01',ValidTo=None,AuthorizationStatus='Active'))
   capability=c.execute('SELECT Id FROM Capability WHERE ExistingCapabilityDesignation=?',(kind,)).fetchone()[0]
   save(c,'CapabilityAuthorization',dict(ProviderAuthorizationId=pa,OutletId=o,CapabilityId=capability,ValidFrom='2026-01-01',ValidTo=None,AuthorizationStatus='Active'))
  for b in accounts[1:]:
   x,y=sorted([accounts[0],b]);save(c,'CustomerIdentityLink',dict(AccountAId=x,AccountBId=y,VerificationStatus='Verified',VerificationMethod='Synthetic acceptance fixture',VerifiedAt='2026-09-01T00:00:00Z',RevokedAt=None,EvidenceReference=f'demo:northstar:identity:{x}:{y}'))
  existing_model=c.execute("SELECT Id FROM VehicleModel WHERE Manufacturer='Northstar (fictional)' AND CatalogueNamespace='demo.northstar.catalogue' AND ManufacturerModelCode='HORIZON' AND ModelYear=2026 AND TrimCode='DEMO'").fetchone()
  model=existing_model['Id'] if existing_model else save(c,'VehicleModel',dict(Manufacturer='Northstar (fictional)',CatalogueNamespace='demo.northstar.catalogue',ManufacturerModelCode='HORIZON',ModelYear=2026,TrimCode='DEMO',ModelName='Northstar Horizon (fictional)'))
  vehicles=[save(c,'Vehicle',dict(VIN='DEMVHCL'+(f'{i:010d}' if company_id is None else f'{company_id:04d}{i:06d}'),LifecycleStatus='Active',VehicleModelId=model)) for i in range(1,15)]
  if company_id is not None and not 1<=int(company_id)<=9999:raise ValueError('Demo company ID must be between 1 and 9999')
  fleet=c.execute('INSERT INTO Fleet(ParentCompanyId,OwnerAccountId,FleetReference,FleetName) VALUES(?,?,?,?)',(company,accounts[0],'CEDAR-FLEET','Cedar Logistics (fictional)')).lastrowid
  for v in vehicles[:12]:c.execute('INSERT INTO FleetVehicleAssignment(FleetId,VehicleId,ValidFrom,ValidTo,EvidenceReference) VALUES(?,?,?,?,?)',(fleet,v,'2026-01-01T00:00:00Z',None,'demo:northstar:preexisting:'+str(v)))
  def activity(kind,provider_index,vehicle,ref,start,end,details):
   aid=save(c,'VehicleActivity',dict(IssuingOutletId=outlets[provider_index],SourceNamespace=namespace,ActivityKind=kind,OfficialActivityReference=ref,ActivityStatus='Completed',StartedAt=start,EndedAt=end,RecordedAt=end,CustomerAccountId=accounts[provider_index],VehicleId=vehicle,**{kind+'Id':-1}))
   sid=save(c,kind,dict(VehicleActivityId=aid,**details));c.execute(f'UPDATE VehicleActivity SET {kind}Id=? WHERE Id=?',(sid,aid));return aid,sid
  sale,_=activity('Sale',0,vehicles[12],'NS-SALE-001','2026-10-01T09:00:00Z','2026-10-01T10:00:00Z',dict(SalePrice=30000,Currency='CAD',CompletedAt='2026-10-01T10:00:00Z'))
  c.execute('INSERT INTO FleetVehicleAssignment(FleetId,VehicleId,ValidFrom,ValidTo,EvidenceReference) VALUES(?,?,?,?,?)',(fleet,vehicles[12],'2026-10-01T10:00:00Z',None,'demo:northstar:new-sale'))
  service,service_id=activity('Service',2,vehicles[12],'NS-SERVICE-001','2026-10-10T09:00:00Z','2026-10-12T17:00:00Z',dict(ServiceType='Eligible demonstration service',Outcome='Completed',CompletedAt='2026-10-12T17:00:00Z'))
  activity('Rental',1,vehicles[13],'NS-RENTAL-001','2026-10-10T12:00:00Z','2026-10-11T12:00:00Z',dict(RentalCharge=80,Currency='CAD',ReturnedAt='2026-10-11T12:00:00Z',ReplacementForServiceId=service_id,ReplacementPurpose='Replacement during eligible service'))
  program=save(c,'IncentiveProgram',dict(ParentCompanyId=company,OfficialProgramReference='SYNTHETIC-FLEET-JOURNEY',ProgramName='Northstar Fleet Journey (fictional)',ActiveFrom='2026-01-01',ActiveTo=None,EventVersionPolicy='SaleCompletedAt',PeriodVersionPolicy='QualificationDate'))
  for p in providers:save(c,'ProgramEnrollment',dict(IncentiveProgramId=program,ProviderId=p,ValidFrom='2026-01-01',ValidTo=None,EnrollmentStatus='Active'))
  rule=save(c,'IncentiveRule',dict(IncentiveProgramId=program,OfficialRuleCode='FLEET-JOURNEY-150',RuleName='Fleet sale with service and replacement rental',AssessmentBasis='Event'))
  save(c,'RuleVersion',dict(IncentiveRuleId=rule,EffectiveFrom='2026-01-01',EffectiveTo=None,ConditionExpression=json.dumps({'operation':'fleet_journey_v1','minimum_fleet_vehicles':10,'service_window_days':30}),RewardSpecification=json.dumps({'amount_minor':15000,'currency':'CAD'})))
  return {'company_id':company,'rule_id':rule,'activity_id':sale,'synthetic':True}
