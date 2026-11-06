"""Derive the relational dictionary from the submitted editable ER diagram."""
from pathlib import Path
import xml.etree.ElementTree as ET
import re,json
ROOT=Path(__file__).resolve().parents[1]
refs={'ParentCompany':'ParentCompany','Provider':'Provider','IssuingOutlet':'Outlet','Outlet':'Outlet','AccountA':'CustomerAccount','AccountB':'CustomerAccount','VehicleActivity':'VehicleActivity','IncentiveProgram':'IncentiveProgram','MetricDefinitionVersion':'MetricDefinitionVersion','ProviderAuthorization':'ProviderAuthorization','Capability':'Capability','IncentiveRule':'IncentiveRule','RuleVersion':'RuleVersion','EventAward':'EventAward','PeriodAward':'PeriodAward'}
models={}
for c in ET.parse(ROOT/'src/dal/models/er/Retail-Mesh-crows-foot-ER.drawio').iter('mxCell'):
 v=c.get('value','')
 if not v.startswith('<b>') or '<hr>' not in v: continue
 name=re.search(r'<b>(.*?)</b>',v)[1]; fields=[]; ck=[]; fks={}
 for a in v.split('<hr>')[1].split('<br>'):
  key='<u>' in a; a=re.sub('<.*?>','',a)
  col=a+'Id' if a in refs else a
  fields.append(col)
  if key: ck.append(col)
  if a in refs:fks[col]=refs[a]
 models[name]={'fields':fields,'ck':ck,'fks':fks,'optional':[],'checks':[],'unique':[]}
def addfk(t,c,d,optional=False):
 m=models[t];m['fields'].append(c);m['fks'][c]=d
 if optional:m['optional'].append(c)
addfk('Vehicle','VehicleModelId','VehicleModel')
addfk('VehicleActivity','CustomerAccountId','CustomerAccount');addfk('VehicleActivity','VehicleId','Vehicle')
addfk('Rental','ReplacementForServiceId','Service',True)
models['Rental']['fields'].append('ReplacementPurpose'); models['Rental']['optional'].append('ReplacementPurpose')
for scope in ['Event','Period']:addfk(scope+'Award','AcceptedEvaluationId',scope+'Evaluation');models[scope+'Award']['unique'].append(['AcceptedEvaluationId'])
for name,a,b,extra in [('MeasurementContribution','PerformanceMeasurement','VehicleActivity',['ContributionRole']),('RuleMetric','RuleVersion','MetricDefinitionVersion',['MetricRole'])]+[(s+'Evaluation'+kind,s+'Evaluation',target,extra) for s in ['Event','Period'] for kind,target,extra in [('Measurement','PerformanceMeasurement',['EvidenceRole']),('Activity','VehicleActivity',['EvidenceRole']),('Identity','CustomerIdentityLink',['VerificationOutcomeUsed','VerifiedAtUsed','EvidenceReferenceUsed'])]]:
 models[name]={'fields':[a+'Id',b+'Id']+extra,'ck':[a+'Id',b+'Id'],'fks':{a+'Id':a,b+'Id':b},'optional':[],'checks':[],'unique':[]}
for t in ['VehicleActivity']:
 for s in ['Sale','Rental','Service']:addfk(t,s+'Id',s,True)
for scope in ['Event','Period']:
 addfk(scope+'Award','FirstComponentId',scope+'AwardComponent')
 models[scope+'AwardComponent']['unique'].append(['Id',scope+'AwardId'])
for t,m in models.items():
 for c in m['fields']:
  if c in ['Email','PhoneNo','EndedAt','ReturnedAt','RevokedAt','ValidTo','EffectiveTo','ActiveTo']:m['optional'].append(c)
 # Final evaluations always include immutable evidence; no draft result is represented.
 for a,b in [('ValidFrom','ValidTo'),('EffectiveFrom','EffectiveTo'),('ActiveFrom','ActiveTo'),('StartedAt','EndedAt'),('PeriodStart','PeriodEnd')]:
  if a in m['fields'] and b in m['fields']:m['checks'].append(f'({b} IS NULL OR {b} > {a})')
 for c in ['BenefitValue','SalePrice','RentalCharge']:
  if c in m['fields']:m['checks'].append(f'{c} >= 0')
 if 'Currency' in m['fields']:
  if t.endswith('Component'):m['optional'].append('Currency')
  m['checks'].append("(Currency IS NULL OR (length(Currency)=3 AND Currency NOT GLOB '*[^A-Z]*'))")
models['CustomerIdentityLink']['checks'] += ['AccountAId < AccountBId',"VerificationStatus IN ('Pending','Verified','Revoked','Rejected')","(VerificationStatus != 'Verified' OR (VerifiedAt IS NOT NULL AND RevokedAt IS NULL))"]
models['CustomerIdentityLink']['optional'] += ['VerifiedAt']
models['Vehicle']['checks'] += ["length(VIN)=17 AND VIN NOT GLOB '*[^A-HJ-NPR-Z0-9]*'"]
models['IncentiveRule']['checks'] += ["AssessmentBasis IN ('Event','Period')"]
models['VehicleActivity']['checks'] += ["ActivityKind IN ('Sale','Rental','Service')","(ActivityKind='Sale' AND SaleId IS NOT NULL AND RentalId IS NULL AND ServiceId IS NULL) OR (ActivityKind='Rental' AND RentalId IS NOT NULL AND SaleId IS NULL AND ServiceId IS NULL) OR (ActivityKind='Service' AND ServiceId IS NOT NULL AND SaleId IS NULL AND RentalId IS NULL)"]
for scope in ['Event','Period']:
 models[scope+'AwardComponent']['checks'] += ["(RewardType != 'Cash' OR (Currency IS NOT NULL AND UnitScheme='ISO4217' AND UnitCode=Currency))","(RewardType != 'Points' OR Currency IS NULL)"]
models['Rental']['checks'] += ["(ReplacementForServiceId IS NULL AND ReplacementPurpose IS NULL) OR (ReplacementForServiceId IS NOT NULL AND ReplacementPurpose IS NOT NULL)"]
for s in ['Event','Period']:
 models[s+'Evaluation']['checks'] += ["Result IN ('Qualified','Rejected')"]
 models[s+'Award']['checks'] += ["AwardStatus IN ('Issued','Cancelled')"]
for s in ['Sale','Rental','Service']:
 models[s]['unique'].append(['Id','VehicleActivityId'])
 models['VehicleActivity']['unique'].append(['Id',s+'Id'])
for t,m in models.items():m['optional']=sorted(set(m['optional']))
def typ(c):return 'INTEGER' if c.endswith('Id') or c=='ModelYear' else 'NUMERIC' if c in ['MeasuredValue','BenefitValue','SalePrice','RentalCharge'] else 'TEXT'
lines=['-- Generated from the supplied ER model; edit the generator, then regenerate.','PRAGMA foreign_keys = ON;','BEGIN;']
for t,m in models.items():
 cols=['Id INTEGER PRIMARY KEY AUTOINCREMENT']
 for c in m['fields']:
  spec=f'{c} {typ(c)}'+('' if c in m['optional'] else ' NOT NULL')
  if typ(c)=='TEXT':spec+=f' CHECK ({c} IS NULL OR length(trim({c})) > 0)'
  if c in ['ValidFrom','ValidTo','EffectiveFrom','EffectiveTo','ActiveFrom','ActiveTo','PeriodStart','PeriodEnd','QualificationDate']:
   spec+=f" CHECK ({c} IS NULL OR (length({c})=10 AND date({c}, '+0 days') IS NOT NULL AND date({c}, '+0 days')={c}))"
  if c.endswith('At'):
   spec+=f" CHECK ({c} IS NULL OR (length({c})=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',{c}, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',{c}, '+0 days')={c}))"
  cols.append(spec)
 cols.append(f"CONSTRAINT UK_{t}_BusinessKey UNIQUE ({', '.join(m['ck'])})")
 for i,u in enumerate(m['unique']):cols.append(f"CONSTRAINT UK_{t}_{i} UNIQUE ({', '.join(u)})")
 for c,target in m['fks'].items():
  if t=='VehicleActivity' and c in ['SaleId','RentalId','ServiceId']:
   cols.append(f'CONSTRAINT FK_{t}_{c}_2_{target}_Id FOREIGN KEY ({c}, Id) REFERENCES {target}(Id,VehicleActivityId) DEFERRABLE INITIALLY DEFERRED')
  elif t in ['Sale','Rental','Service'] and c=='VehicleActivityId':
   cols.append(f'CONSTRAINT FK_{t}_{c}_2_VehicleActivity_Id FOREIGN KEY ({c},Id) REFERENCES VehicleActivity(Id,{t}Id) DEFERRABLE INITIALLY DEFERRED')
  elif c=='FirstComponentId':
   cols.append(f'CONSTRAINT FK_{t}_{c}_2_{target}_Id FOREIGN KEY ({c}, Id) REFERENCES {target}(Id,{t}Id) DEFERRABLE INITIALLY DEFERRED')
  else:cols.append(f'CONSTRAINT FK_{t}_{c}_2_{target}_Id FOREIGN KEY ({c}) REFERENCES {target}(Id) DEFERRABLE INITIALLY DEFERRED')
 for check in m['checks']:cols.append('CHECK ('+check+')')
 lines.append('CREATE TABLE '+t+' (\n  '+',\n  '.join(cols)+'\n);')
 for c in m['fks']:lines.append(f'CREATE INDEX IX_{t}_{c} ON {t}({c});')
lines.append('COMMIT;')
base=ROOT/'src/dal/models/relational';(base/'dictionary.json').write_text(json.dumps(models,indent=2));(base/'sql/01_schema.sql').write_text('\n\n'.join(lines)+'\n')
print(f'{len(models)} relations generated')
