"""Independent semantic checks for CSV fixtures, beyond SQL/FK integrity."""
from collections import Counter
from decimal import Decimal
import json
from cmn.dates import parse_utc,business_date,billable_days,BUSINESS_ZONE


def index(records):return {table:{str(row['Id']):row for row in rows} for table,rows in records.items() if table!='JourneyOverview'}
def provider_of(d,activity):return d['Outlet'][str(activity['IssuingOutletId'])]['ProviderId']
def active(row,day,status='AuthorizationStatus'):
    return row[status]=='Active' and row['ValidFrom']<=day and (not row['ValidTo'] or day<row['ValidTo'])
def company_of(d,provider,day):
    return {r['ParentCompanyId'] for r in d['ProviderAuthorization'].values() if r['ProviderId']==provider and active(r,day)}
def capabilities(d,provider,company,day):
    authorizations={r['Id'] for r in d['ProviderAuthorization'].values() if r['ProviderId']==provider and r['ParentCompanyId']==company and active(r,day)}
    return {d['Capability'][r['CapabilityId']]['ExistingCapabilityDesignation'] for r in d['CapabilityAuthorization'].values() if r['ProviderAuthorizationId'] in authorizations and active(r,day)}
def identity_status(link,at):
    if not link['VerifiedAt'] or parse_utc(link['VerifiedAt'])>parse_utc(at):return 'Pending'
    if link['RevokedAt'] and parse_utc(link['RevokedAt'])<=parse_utc(at):return 'Revoked'
    return 'Verified'
def activity_completion(d,a):
    kind=a['ActivityKind'];sub=d[kind][a[kind+'Id']]
    return sub.get('ReturnedAt') if kind=='Rental' else sub.get('CompletedAt')
def metric_activities(d,measurement):
    metric=d['MetricDefinitionVersion'][measurement['MetricDefinitionVersionId']];code=metric['OfficialMetricCode'];selected=[]
    for a in d['VehicleActivity'].values():
        end=activity_completion(d,a)
        if a['ActivityStatus']!='Completed' or not end or provider_of(d,a)!=measurement['ProviderId']:continue
        if not measurement['PeriodStart']<=business_date(end)<measurement['PeriodEnd']:continue
        if code=='SERVICE-COMPLETED-COUNT' and a['ActivityKind']!='Service':continue
        if code=='SALE-VALUE-CAD' and a['ActivityKind']!='Sale':continue
        if code in ['REPLACEMENT-RENTAL-COUNT','RENTAL-DURATION-DAYS']:
            if a['ActivityKind']!='Rental':continue
            if code=='REPLACEMENT-RENTAL-COUNT' and not d['Rental'][a['RentalId']]['ReplacementForServiceId']:continue
        selected.append(a)
    return selected

def metric_value(d,measurement):
    metric=d['MetricDefinitionVersion'][measurement['MetricDefinitionVersionId']];code=metric['OfficialMetricCode'];acts=metric_activities(d,measurement)
    if code.endswith('COUNT'):return Decimal(len(acts))
    if code=='SALE-VALUE-CAD':return sum((Decimal(d['Sale'][a['SaleId']]['SalePrice']) for a in acts),Decimal(0))
    if code=='RENTAL-DURATION-DAYS':
        ceiling='CEILING' in metric['DefinitionExpression'].upper()
        return sum((Decimal(billable_days(a['StartedAt'],d['Rental'][a['RentalId']]['ReturnedAt'])) if ceiling else Decimal((parse_utc(d['Rental'][a['RentalId']]['ReturnedAt']).date()-parse_utc(a['StartedAt']).date()).days) for a in acts),Decimal(0))
    raise ValueError('Unsupported sample metric '+code)

def primary_capability(d,evaluation,condition):
    version=d['RuleVersion'][evaluation['RuleVersionId']];rule=d['IncentiveRule'][version['IncentiveRuleId']];program=d['IncentiveProgram'][rule['IncentiveProgramId']]
    caps=capabilities(d,evaluation['ProviderId'],program['ParentCompanyId'],evaluation['QualificationDate'])
    return next((code for code in condition.get('capabilityPriority',['VehicleSale','VehicleRental','VehicleService']) if code in caps),None)

def period_result(d,evaluation):
    version=d['RuleVersion'][evaluation['RuleVersionId']];condition=json.loads(version['ConditionExpression'])
    criteria=condition.get('criteriaByCapability')
    if not criteria:return None
    cap=primary_capability(d,evaluation,condition);thresholds=criteria.get(cap,{})
    values={d['MetricDefinitionVersion'][m['MetricDefinitionVersionId']]['OfficialMetricCode']:Decimal(m['MeasuredValue']) for m in d['PerformanceMeasurement'].values() if m['ProviderId']==evaluation['ProviderId'] and m['PeriodStart']==evaluation['PeriodStart'] and m['PeriodEnd']==evaluation['PeriodEnd']}
    return 'Qualified' if thresholds and all(code in values and values[code]>=Decimal(str(minimum)) for code,minimum in thresholds.items()) else 'Rejected'

def policy_benefits(d,kind,award):
    e=d[kind+'Evaluation'][award['AcceptedEvaluationId']];v=d['RuleVersion'][e['RuleVersionId']];spec=json.loads(v['RewardSpecification'])
    if kind=='Period' and 'benefitsByCapability' in spec:return spec['benefitsByCapability'].get(primary_capability(d,e,json.loads(v['ConditionExpression'])),[])
    return spec.get('benefits',[])

def review(records):
    d=index(records);issues=[]
    def add(level,code,table,row,detail):issues.append({'severity':level,'code':code,'table':table,'source_id':str(row['Id']),'detail':detail})
    for a in d['VehicleActivity'].values():
        start=parse_utc(a['StartedAt']);end=activity_completion(d,a)
        if not 8<=start.astimezone(BUSINESS_ZONE).hour<18:add('warning','outside_business_hours','VehicleActivity',a,'Start falls outside 08:00–18:00 America/Vancouver for this daytime sample.')
        if a['EndedAt'] and parse_utc(a['EndedAt'])<start:add('error','reversed_activity_interval','VehicleActivity',a,'Activity ends before it starts.')
        if a['ActivityStatus']=='Completed' and (not end or not a['EndedAt']):add('error','completed_without_end','VehicleActivity',a,'Completed activity lacks its completion/return timestamp.')
        if a['ActivityStatus']=='Completed' and end and parse_utc(a['RecordedAt'])<parse_utc(end):add('information','record_created_before_completion','VehicleActivity',a,'RecordedAt may represent creation; the prepared revision will explicitly use final-record time.')
        if a['ActivityKind'] in ['Sale','Service'] and end and a['EndedAt']!=end:add('error','subtype_end_mismatch','VehicleActivity',a,'Parent and subtype completion timestamps differ.')
        if d['CustomerAccount'][a['CustomerAccountId']]['ProviderId']!=provider_of(d,a):add('error','account_provider_mismatch','VehicleActivity',a,'Customer account belongs to another issuing provider.')
    for r in d['Rental'].values():
        a=d['VehicleActivity'][r['VehicleActivityId']]
        if r['ReturnedAt'] and parse_utc(r['ReturnedAt'])<=parse_utc(a['StartedAt']):add('error','invalid_rental_duration','Rental',r,'Return must follow collection.')
        if r['ReplacementForServiceId']:
            service=d['Service'][r['ReplacementForServiceId']];s=d['VehicleActivity'][service['VehicleActivityId']]
            if a['VehicleId']==s['VehicleId']:add('error','replacement_same_vehicle','Rental',r,'Replacement vehicle is the serviced vehicle.')
            if r['ReturnedAt'] and (parse_utc(r['ReturnedAt'])-parse_utc(service['CompletedAt'])).total_seconds()>3600:add('warning','replacement_after_service_grace','Rental',r,'Return exceeds a one-hour handover allowance after service; no extension reason is supplied.')
    for service in d['Service'].values():
        a=d['VehicleActivity'][service['VehicleActivityId']];model=d['VehicleModel'][d['Vehicle'][a['VehicleId']]['VehicleModelId']]
        if 'EV charging' in service['ServiceType'] and not any(token in model['ModelName'].upper() for token in [' EV','EV6','IONIQ']):add('warning','unsupported_ev_description','Service',service,'EV-specific charging diagnosis is unsupported by this model label; use a powertrain-supported description.')
    for m in d['PerformanceMeasurement'].values():
        if Decimal(m['MeasuredValue'])!=metric_value(d,m):add('error','measurement_value_mismatch','PerformanceMeasurement',m,'Value does not reconcile to completed provider activities in the stated business-date period.')
        expected={a['Id'] for a in metric_activities(d,m)};actual={r['VehicleActivityId'] for r in d['MeasurementContribution'].values() if r['PerformanceMeasurementId']==m['Id']}
        if expected!=actual:add('error','measurement_contribution_mismatch','PerformanceMeasurement',m,'Contributing activity IDs do not match the metric population.')
    for e in d['EventEvaluation'].values():
        acts=[d['VehicleActivity'][e['VehicleActivityId']]]+[d['VehicleActivity'][r['VehicleActivityId']] for r in d['EventEvaluationActivity'].values() if r['EventEvaluationId']==e['Id']]
        snapshots=[r for r in d['EventEvaluationIdentity'].values() if r['EventEvaluationId']==e['Id']]
        times=[activity_completion(d,a) for a in acts if activity_completion(d,a)]+[r['VerifiedAtUsed'] for r in snapshots]
        times += [d['PerformanceMeasurement'][r['PerformanceMeasurementId']]['CalculatedAt'] for r in d['EventEvaluationMeasurement'].values() if r['EventEvaluationId']==e['Id']]
        if e['Result']=='Qualified' and any(business_date(t)>e['QualificationDate'] for t in times):add('error','qualification_precedes_evidence','EventEvaluation',e,'Qualification precedes required completion, measurement or verified-identity evidence.')
        if any(parse_utc(t)>parse_utc(e['EvaluatedAt']) for t in times):add('error','future_decision_evidence','EventEvaluation',e,'Decision uses evidence not yet available at evaluation time.')
        if e['Result']=='Qualified':
            account=acts[0]['CustomerAccountId']
            for act in acts[1:]:
                pair={account,act['CustomerAccountId']}
                matching=[link for link in d['CustomerIdentityLink'].values() if {link['AccountAId'],link['AccountBId']}==pair]
                valid=[link for link in matching if identity_status(link,e['EvaluatedAt'])=='Verified']
                if not valid:add('error','invalid_direct_identity','EventEvaluation',e,'No valid direct sale-to-'+act['ActivityKind']+' account verification at decision time.')
                elif not any(s['CustomerIdentityLinkId'] in {v['Id'] for v in valid} and s['VerificationOutcomeUsed']=='Verified' for s in snapshots):add('error','missing_identity_snapshot','EventEvaluation',e,'Direct sale-to-'+act['ActivityKind']+' verification exists but is not cited in the decision snapshot.')
    for kind in ['Event','Period']:
        for snap in d[kind+'EvaluationIdentity'].values():
            e=d[kind+'Evaluation'][snap[kind+'EvaluationId']];link=d['CustomerIdentityLink'][snap['CustomerIdentityLinkId']]
            if snap['VerifiedAtUsed']!=link['VerifiedAt'] or snap['VerificationOutcomeUsed']!=identity_status(link,e['EvaluatedAt']):add('error','identity_snapshot_mismatch',kind+'EvaluationIdentity',snap,'Frozen verification facts do not match source evidence at decision time.')
        for award in d[kind+'Award'].values():
            expected=Counter((b['type'],Decimal(str(b['amount'])),b.get('currency') or b.get('unit')) for b in policy_benefits(d,kind,award))
            actual=Counter((b['RewardType'],Decimal(b['BenefitValue']),b['Currency'] or b['UnitCode']) for b in d[kind+'AwardComponent'].values() if b[kind+'AwardId']==award['Id'])
            if expected!=actual:add('error','award_policy_mismatch',kind+'Award',award,'Issued benefit components do not match the declared policy for this rule/capability.')
    for e in d['PeriodEvaluation'].values():
        expected=period_result(d,e)
        if expected is None:add('warning','period_criteria_not_explicit','PeriodEvaluation',e,'Policy describes a manual review but has no reproducible numerical criteria for the outcome.')
        elif expected!=e['Result']:add('error','period_result_mismatch','PeriodEvaluation',e,'Result differs from the policy thresholds and period measurements.')
        accounts={d['VehicleActivity'][r['VehicleActivityId']]['CustomerAccountId'] for r in d['PeriodEvaluationActivity'].values() if r['PeriodEvaluationId']==e['Id']}
        for snap in d['PeriodEvaluationIdentity'].values():
            if snap['PeriodEvaluationId']!=e['Id']:continue
            link=d['CustomerIdentityLink'][snap['CustomerIdentityLinkId']]
            if not accounts.intersection({link['AccountAId'],link['AccountBId']}):add('error','irrelevant_period_identity','PeriodEvaluationIdentity',snap,'Identity evidence is unrelated to this provider’s cited activities in the review period.')
    return {'counts':dict(Counter(i['severity'] for i in issues)),'issue_codes':dict(Counter(i['code'] for i in issues)),'issues':issues,'source_rows':sum(len(rows) for table,rows in records.items() if table!='JourneyOverview'),'metric_reconciliation_count':len(d['PerformanceMeasurement'])}
