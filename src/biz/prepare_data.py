"""Deterministic revision of the supplied synthetic fixture; never edit raw input."""
import copy,csv,io,json,zipfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from cmn.dates import intended_local_to_utc,parse_utc,utc_text,business_date,billable_days
from dal.database import MODELS
from biz.csv_import import read_archive
from biz.data_quality import index,provider_of,identity_status,metric_activities,metric_value,period_result,policy_benefits


def prepare(raw_path,output_path):
    original,source_hash=read_archive(raw_path);records=copy.deepcopy(original);d=index(records)
    # Explicit fixture assumption: clock readings in the Victoria sample were intended as local business time.
    for rows in records.values():
        for row in rows:
            for field,value in row.items():
                if field.endswith('At') and value:row[field]=intended_local_to_utc(value)
    for a in d['VehicleActivity'].values():
        a['RecordedAt']=utc_text(parse_utc(a['EndedAt'] or a['StartedAt'])+timedelta(minutes=5))
    # Preserve vehicle/model identity; remove unsupported powertrain/class claims.
    d['Service']['3']['ServiceType']='Hybrid battery diagnostic'
    d['Service']['3']['Outcome']='Hybrid battery condition checked; no repair required in this synthetic inspection'
    d['Service']['10']['ServiceType']='Electrical system diagnostic'
    d['Service']['10']['Outcome']='Battery and low-voltage charging circuit checked; no fault found in this synthetic inspection'
    d['Service']['8']['ServiceType']='Fleet safety inspection'
    # Replacement contracts cover downtime plus one hour to collect/return the vehicles.
    rates={'3':Decimal('89'),'4':Decimal('94')}
    for rental in records['Rental']:
        a=d['VehicleActivity'][rental['VehicleActivityId']]
        if not rental['ReplacementForServiceId']:continue
        service=d['Service'][rental['ReplacementForServiceId']];service_activity=d['VehicleActivity'][service['VehicleActivityId']]
        a['StartedAt']=utc_text(parse_utc(service_activity['StartedAt'])+timedelta(minutes=30))
        returned=utc_text(parse_utc(service['CompletedAt'])+timedelta(hours=1))
        a['EndedAt']=returned;a['RecordedAt']=utc_text(parse_utc(returned)+timedelta(minutes=5));rental['ReturnedAt']=returned
        rental['RentalCharge']=str(rates[provider_of(d,a)]*billable_days(a['StartedAt'],returned))
        rental['ReplacementPurpose']='Service downtime mobility; one-hour vehicle handover allowance'
    # Define every policy quantity instead of unexplained award or rejection overrides.
    criteria={'VehicleSale':{'ACTIVITY-COMPLETED-COUNT':1,'SALE-VALUE-CAD':50000},
              'VehicleRental':{'REPLACEMENT-RENTAL-COUNT':2,'RENTAL-DURATION-DAYS':4},
              'VehicleService':{'SERVICE-COMPLETED-COUNT':2}}
    for version in records['RuleVersion']:
        rule=d['IncentiveRule'][version['IncentiveRuleId']];program=d['IncentiveProgram'][rule['IncentiveProgramId']];latest=version['EffectiveFrom']>='2026-07-01';label='2.0' if latest else '1.0'
        condition={'qualificationMode':'synthetic-fixture-preparation','assessmentBasis':rule['AssessmentBasis'],'version':label,
                   'note':'Offline sample-policy calculation during dataset preparation; not a live business decision or the fleet IncentiveRun engine.'}
        if rule['AssessmentBasis']=='Event':
            condition.update({'eventChecks':['completed sale','same-vehicle completed service','linked replacement rental','same company scope','direct sale-to-service and sale-to-rental verified identity snapshots valid at evaluation'],
                              'requireDirectIdentitySnapshots':True,'replacementHandoverGraceMinutes':60})
            amount=(150 if program['ParentCompanyId']=='1' else 175) if latest else 100
            benefits=[{'type':'Cash','amount':amount,'currency':'CAD'}]+([{'type':'Points','amount':300,'unit':'POINT'}] if latest else [])
            spec={'illustrativeOnly':True,'offlineFixtureOnly':True,'version':label,'benefits':benefits}
        else:
            condition.update({'businessTimezone':'America/Vancouver','periodBoundary':'start inclusive, end exclusive','capabilityPriority':['VehicleSale','VehicleRental','VehicleService'],'criteriaByCapability':criteria})
            points=500 if latest else 250
            spec={'illustrativeOnly':True,'offlineFixtureOnly':True,'version':label,'benefitsByCapability':{
                'VehicleSale':[{'type':'Cash','amount':250 if latest else 100,'currency':'CAD'},{'type':'Points','amount':points,'unit':'POINT'}],
                'VehicleRental':[{'type':'Points','amount':points,'unit':'POINT'}],
                'VehicleService':[{'type':'Points','amount':points,'unit':'POINT'}]}}
        version['ConditionExpression']=json.dumps(condition,separators=(',',':'));version['RewardSpecification']=json.dumps(spec,separators=(',',':'))
    for definition in records['MetricDefinitionVersion']:
        code=definition['OfficialMetricCode']
        definition['DefinitionExpression']={'ACTIVITY-COMPLETED-COUNT':'COUNT completed provider activities by completion business date in America/Vancouver; [PeriodStart, PeriodEnd)',
         'SERVICE-COMPLETED-COUNT':'COUNT completed provider services by completion business date in America/Vancouver; [PeriodStart, PeriodEnd)',
         'SALE-VALUE-CAD':'SUM tax-exclusive SalePrice in CAD for completed sales by completion business date; [PeriodStart, PeriodEnd)',
         'REPLACEMENT-RENTAL-COUNT':'COUNT completed provider rentals linked to a service, by local return date; [PeriodStart, PeriodEnd)',
         'RENTAL-DURATION-DAYS':'SUM CEILING elapsed rental seconds / 86400 for completed rentals, by America/Vancouver return date; minimum one billable day; [PeriodStart, PeriodEnd)'}[code]
    for measurement in records['PerformanceMeasurement']:measurement['MeasuredValue']=str(metric_value(d,measurement))
    # Period rules use five metrics with capability-dependent thresholds.
    next_metric_id=max(int(r['Id']) for r in records['RuleMetric'])+1
    for version in records['RuleVersion']:
        rule=d['IncentiveRule'][version['IncentiveRuleId']]
        if rule['AssessmentBasis']!='Period':continue
        company=d['IncentiveProgram'][rule['IncentiveProgramId']]['ParentCompanyId']
        existing={r['MetricDefinitionVersionId'] for r in records['RuleMetric'] if r['RuleVersionId']==version['Id']}
        for metric in records['MetricDefinitionVersion']:
            if metric['ParentCompanyId']==company and metric['Id'] not in existing:
                records['RuleMetric'].append({'Id':str(next_metric_id),'RuleVersionId':version['Id'],'MetricDefinitionVersionId':metric['Id'],'MetricRole':'Conditional'});next_metric_id+=1
    # Capture a direct rental identity link for each event. Pending evidence has no fabricated VerifiedAt.
    for snapshot in records['EventEvaluationIdentity']:
        link=d['CustomerIdentityLink'][snapshot['CustomerIdentityLinkId']];snapshot['VerifiedAtUsed']=link['VerifiedAt'];snapshot['EvidenceReferenceUsed']=link['EvidenceReference']
    next_identity=max(int(r['Id']) for r in records['EventEvaluationIdentity'])+1
    for e in records['EventEvaluation']:
        sale=d['VehicleActivity'][e['VehicleActivityId']];root=sale['CustomerAccountId'];valid=True;times=[sale['EndedAt']];invalid_proofs=[]
        existing=[r for r in records['EventEvaluationIdentity'] if r['EventEvaluationId']==e['Id']]
        related=[d['VehicleActivity'][r['VehicleActivityId']] for r in records['EventEvaluationActivity'] if r['EventEvaluationId']==e['Id']]
        for a in related:
            times.append(a['EndedAt']);link=next((r for r in records['CustomerIdentityLink'] if {r['AccountAId'],r['AccountBId']}=={root,a['CustomerAccountId']}),None)
            status=identity_status(link,e['EvaluatedAt']) if link else 'Missing'
            if status!='Verified':
                valid=False;invalid_proofs.append('sale-to-'+a['ActivityKind']+': '+('CustomerIdentityLink #'+link['Id'] if link else 'no direct assertion')+' is '+status)
            if link and link['VerifiedAt'] and status=='Verified':
                times.append(link['VerifiedAt'])
                if not any(r['CustomerIdentityLinkId']==link['Id'] for r in existing):
                    records['EventEvaluationIdentity'].append({'Id':str(next_identity),'EventEvaluationId':e['Id'],'CustomerIdentityLinkId':link['Id'],'VerificationOutcomeUsed':identity_status(link,e['EvaluatedAt']),'VerifiedAtUsed':link['VerifiedAt'],'EvidenceReferenceUsed':link['EvidenceReference']});next_identity+=1
        times.extend(d['PerformanceMeasurement'][r['PerformanceMeasurementId']]['CalculatedAt'] for r in records['EventEvaluationMeasurement'] if r['EventEvaluationId']==e['Id'])
        e['Result']='Qualified' if valid else 'Rejected'
        e['QualificationDate']=max(business_date(t) for t in times) if valid else business_date(e['EvaluatedAt'])
        e['Reason']=('Prepared synthetic decision: completed sale, service and replacement rental with both direct identity proofs valid at evaluation; all cited evidence available by qualification date.' if valid else 'Prepared synthetic rejection: '+'; '.join(invalid_proofs)+'. Non-verified assertions are not stored as accepted identity evidence.')
    records['EventAward']=[a for a in records['EventAward'] if d['EventEvaluation'][a['AcceptedEvaluationId']]['Result']=='Qualified']
    valid_event_ids={a['Id'] for a in records['EventAward']};records['EventAwardComponent']=[r for r in records['EventAwardComponent'] if r['EventAwardId'] in valid_event_ids]
    # Retain stable IDs; add missing components using new IDs, rather than reusing removed records.
    next_component=max(int(r['Id']) for r in original['EventAwardComponent'])+1
    for award in records['EventAward']:
        expected=policy_benefits(d,'Event',award);existing=[r for r in records['EventAwardComponent'] if r['EventAwardId']==award['Id']]
        for benefit in expected:
            component=next((r for r in existing if r['RewardType']==benefit['type']),None)
            if component is None:
                component={'Id':str(next_component),'EventAwardId':award['Id'],'RewardType':benefit['type'],'UnitScheme':'ISO4217' if benefit['type']=='Cash' else 'retail-mesh:points','UnitCode':benefit.get('currency') or benefit['unit'],'BenefitValue':str(benefit['amount']),'Currency':benefit.get('currency',''),'ValidFrom':business_date(award['IssuedAt']),'ValidTo':''};records['EventAwardComponent'].append(component);next_component+=1
            component['BenefitValue']=str(benefit['amount'])
    # Pick period identities related to the actual Q3 activity population, not unrelated Q1 customers.
    period_links={'1':'23','2':'18','3':'22','4':'16','5':'23','6':'18','7':'33'}
    for snap in records['PeriodEvaluationIdentity']:
        link=d['CustomerIdentityLink'][period_links[snap['PeriodEvaluationId']]];snap.update(CustomerIdentityLinkId=link['Id'],VerificationOutcomeUsed='Verified',VerifiedAtUsed=link['VerifiedAt'],EvidenceReferenceUsed=link['EvidenceReference'])
    for e in records['PeriodEvaluation']:
        e['Result']=period_result(d,e)
        values={d['MetricDefinitionVersion'][m['MetricDefinitionVersionId']]['OfficialMetricCode']:m['MeasuredValue'] for m in records['PerformanceMeasurement'] if m['ProviderId']==e['ProviderId'] and m['PeriodStart']==e['PeriodStart'] and m['PeriodEnd']==e['PeriodEnd']}
        e['Reason']='Prepared synthetic '+e['Result'].lower()+': '+json.dumps(values,sort_keys=True,separators=(',',':'))+'; checked against the declared capability thresholds. Offline fixture calculation; no payment settlement.'
    next_award=max(int(a['Id']) for a in original['PeriodAward'])+1;next_component=max(int(c['Id']) for c in original['PeriodAwardComponent'])+1
    for evaluation in records['PeriodEvaluation']:
        if evaluation['Result']!='Qualified':continue
        award=next((a for a in records['PeriodAward'] if a['AcceptedEvaluationId']==evaluation['Id']),None)
        if award is None:
            version=d['RuleVersion'][evaluation['RuleVersionId']];award={'Id':str(next_award),'ProviderId':evaluation['ProviderId'],'IncentiveRuleId':version['IncentiveRuleId'],'PeriodStart':evaluation['PeriodStart'],'PeriodEnd':evaluation['PeriodEnd'],'AwardStatus':'Issued','IssuedAt':intended_local_to_utc('2026-10-29T12:00:00Z'),'AcceptedEvaluationId':evaluation['Id'],'FirstComponentId':str(next_component)};records['PeriodAward'].append(award);next_award+=1
        for benefit in policy_benefits(d,'Period',award):
            component=next((c for c in records['PeriodAwardComponent'] if c['PeriodAwardId']==award['Id'] and c['RewardType']==benefit['type']),None)
            if component is None:
                component={'Id':str(next_component),'PeriodAwardId':award['Id'],'RewardType':benefit['type'],'UnitScheme':'ISO4217' if benefit['type']=='Cash' else 'retail-mesh:points','UnitCode':benefit.get('currency') or benefit['unit'],'BenefitValue':str(benefit['amount']),'Currency':benefit.get('currency',''),'ValidFrom':business_date(award['IssuedAt']),'ValidTo':''};records['PeriodAwardComponent'].append(component);next_component+=1
            component['BenefitValue']=str(benefit['amount'])
    # Produce the denormalized report from its owning records, never hand-edit a second copy.
    report=[]
    for a in records['VehicleActivity']:
        outlet=d['Outlet'][a['IssuingOutletId']];provider=d['Provider'][outlet['ProviderId']];model=d['VehicleModel'][d['Vehicle'][a['VehicleId']]['VehicleModelId']];service=d['Service'].get(a['ServiceId']);rental=d['Rental'].get(a['RentalId']);replacement=d['Service'].get(rental['ReplacementForServiceId']) if rental else None
        report.append({'OfficialActivityReference':a['OfficialActivityReference'],'ActivityKind':a['ActivityKind'],'ActivityStatus':a['ActivityStatus'],'StartedAt':a['StartedAt'],'EndedAt':a['EndedAt'],'Provider':provider['LegalName'],'OutletName':outlet['OutletName'],'ProviderLocalCustomerAccount':d['CustomerAccount'][a['CustomerAccountId']]['DisplayName'],'VIN':d['Vehicle'][a['VehicleId']]['VIN'],'Manufacturer':model['Manufacturer'],'ModelName':model['ModelName'],'ModelYear':model['ModelYear'],'ServiceType':service['ServiceType'] if service else '','Outcome':service['Outcome'] if service else '','ReplacementPurpose':rental['ReplacementPurpose'] if rental else '','ReplacementForService':d['VehicleActivity'][replacement['VehicleActivityId']]['OfficialActivityReference'] if replacement else ''})
    records['JourneyOverview']=report
    out=Path(output_path);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
        for table,rows in records.items():
            fields=list(original[table][0]) if original[table] else ['Id']+MODELS[table]['fields'];buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
            info=zipfile.ZipInfo('csv/'+table+'.csv',date_time=(2026,11,4,12,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,buffer.getvalue().encode('utf-8-sig'))
    changes=[]
    for table in MODELS:
        before={r['Id']:r for r in original[table]};after={r['Id']:r for r in records[table]}
        for key in sorted(before.keys()|after.keys(),key=int):
            if key not in before:changes.append({'table':table,'source_id':key,'action':'added','before':None,'after':after[key]})
            elif key not in after:changes.append({'table':table,'source_id':key,'action':'removed','before':before[key],'after':None})
            else:
                fields={field:{'before':before[key][field],'after':after[key][field]} for field in before[key] if before[key][field]!=after[key][field]}
                if fields:changes.append({'table':table,'source_id':key,'action':'updated','fields':fields})
    return records,{'dataset_version':'2.0','raw_sha256':source_hash,'prepared_sha256':read_archive(out)[1],'changes':changes,'assumptions':{'business_timezone':'America/Vancouver','source_clock_interpretation':'Original clock readings treated as intended local business time, then converted to UTC','replacement_handover_grace_minutes':60,'rental_billable_unit':'CEILING elapsed seconds / 86400; minimum 1 day','replacement_daily_rate_cad_by_source_provider':{'3':89,'4':94},'open_rental':'Contract quote of CAD 72 remains provisional and excluded from completion metrics','report_as_of':'2026-11-04','decision_basis':'Offline synthetic sample policy preparation, not real business or human approval'}}
