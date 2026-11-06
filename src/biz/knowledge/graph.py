"""Snapshot-based RDF export and SHACL validation. Optional dependencies."""
from pathlib import Path
from dal.database import ROOT

def build_graph(snapshot):
 try:from rdflib import Graph,Namespace,Literal,RDF,XSD
 except ImportError:raise ValueError('Install knowledge dependencies: python3 -m pip install -r requirements-knowledge.txt')
 from rdflib.namespace import PROV,RDFS
 g=Graph();rm=Namespace('https://example.org/retail-mesh/vocab#');ex=Namespace(f"https://example.org/retail-mesh/demo/company/{snapshot['company_id']}/")
 g.bind('rm',rm);g.bind('ex',ex);g.bind('prov',PROV)
 run=ex['run/'+str(snapshot['run_id'])];v=ex['rule-version/'+str(snapshot['rule_version_id'])]
 def lit(s,p,value,datatype=None):g.add((s,rm[p],Literal(value,datatype=datatype)))
 g.add((run,RDF.type,rm.IncentiveEvaluation));g.add((v,RDF.type,rm.RuleVersion));g.add((run,rm.appliedRuleVersion,v))
 lit(run,'result',snapshot['result']);lit(run,'inputHash',snapshot['input_hash']);lit(run,'evaluatedAt',snapshot['evaluated_at'],XSD.dateTime);lit(run,'fleetCountBeforeSale',snapshot['fleet_count_before_sale'],XSD.integer)
 frozen=ex['snapshot/'+snapshot['input_hash']];g.add((frozen,RDF.type,rm.EvidenceSnapshot));g.add((run,PROV.used,frozen));lit(frozen,'sourceReference','urn:retail-mesh:snapshot:sha256:'+snapshot['input_hash'])
 for i,check in enumerate(snapshot['checks']):
  node=ex[f"run/{snapshot['run_id']}/check/{i}"];g.add((node,RDF.type,rm.Check));g.add((run,rm.hasCheck,node));lit(node,'name',check['name']);lit(node,'passed',check['passed'],XSD.boolean);lit(node,'description',check['detail'])
 evidence=snapshot['evidence'];selected=evidence['selected'];acts=[evidence['sale']]+([selected['service'],selected['rental']] if selected else [])
 for act in acts:
  node=ex['activity/'+str(act['Id'])];provider=ex['provider/'+str(act['ProviderId'])];vehicle=ex['vehicle/'+str(act['VehicleId'])]
  g.add((node,RDF.type,rm[act['ActivityKind']]));g.add((provider,RDF.type,rm.Provider));g.add((vehicle,RDF.type,rm.Vehicle));g.add((node,rm.performedBy,provider));g.add((node,rm.involvesVehicle,vehicle));lit(node,'sourceReference',act['SourceNamespace']+':'+act['OfficialActivityReference']);g.add((frozen,rm.citesActivity,node))
 if selected:g.add((ex['activity/'+str(selected['rental']['Id'])],rm.replacementFor,ex['activity/'+str(selected['service']['Id'])]))
 # Preserve the historical/identity proof path as resources with relationship attributes.
 fleet=evidence['fleet']
 if fleet:
  fleet_node=ex['fleet/'+str(fleet['Id'])];g.add((fleet_node,RDF.type,rm.Fleet));g.add((frozen,rm.citesFleet,fleet_node));lit(fleet_node,'name',fleet['FleetName'])
  for member in evidence['fleet_assignments']:
   node=ex['snapshot/'+snapshot['input_hash']+'/membership/'+str(member['Id'])];vehicle=ex['vehicle/'+str(member['VehicleId'])]
   g.add((node,RDF.type,rm.FleetMembershipEvidence));g.add((frozen,rm.citesMembership,node));g.add((node,rm.fleet,fleet_node));g.add((node,rm.vehicle,vehicle));g.add((vehicle,RDF.type,rm.Vehicle))
   lit(node,'validFrom',member['ValidFrom'],XSD.dateTime)
   if member['ValidTo']:lit(node,'validTo',member['ValidTo'],XSD.dateTime)
   lit(node,'sourceReference',member['EvidenceReference'])
 if selected:
  seen=set()
  for link in [selected['service_identity'],selected['rental_identity']]:
   if 'Id' not in link or link['Id'] in seen:continue
   seen.add(link['Id']);node=ex['snapshot/'+snapshot['input_hash']+'/identity/'+str(link['Id'])]
   g.add((node,RDF.type,rm.IdentityEvidence));g.add((frozen,rm.citesIdentity,node));lit(node,'verificationStatus',link['VerificationStatus']);lit(node,'verifiedAt',link['VerifiedAt'],XSD.dateTime);lit(node,'accountAId',link['AccountAId'],XSD.integer);lit(node,'accountBId',link['AccountBId'],XSD.integer);lit(node,'sourceReference',link['EvidenceReference'])
 for i,enrollment in enumerate(evidence['enrollment']):
  node=ex['snapshot/'+snapshot['input_hash']+'/enrollment/'+str(enrollment['Id'])];g.add((node,RDF.type,rm.EnrollmentEvidence));g.add((frozen,rm.citesEnrollment,node));lit(node,'sourceReference','ProgramEnrollment:'+str(enrollment['Id']));lit(node,'validFromDate',enrollment['ValidFrom'],XSD.date)
 lit(v,'conditionsJson',evidence['version']['ConditionExpression']);lit(v,'rewardJson',evidence['version']['RewardSpecification']);lit(v,'effectiveFrom',evidence['version']['EffectiveFrom'],XSD.date)
 beneficiary=ex['provider/'+str(snapshot['beneficiary_id'])];g.add((beneficiary,RDF.type,rm.Provider));g.add((beneficiary,RDFS.label,Literal(snapshot['beneficiary'])))
 if snapshot['event_award_id']:
  award=ex['award/'+str(snapshot['event_award_id'])];g.add((award,RDF.type,rm.ProviderAward));g.add((award,rm.beneficiary,beneficiary));g.add((award,PROV.wasGeneratedBy,run));lit(award,'amountMinor',snapshot['reward']['amount_minor'],XSD.integer);lit(award,'currency',snapshot['reward']['currency'])
 return g

def validate_graph(graph):
 try:from pyshacl import validate
 except ImportError:raise ValueError('Install knowledge dependencies: python3 -m pip install -r requirements-knowledge.txt')
 conforms,report,text=validate(graph,shacl_graph=str(ROOT/'src/dal/models/semantic/retail-mesh-shapes.ttl'),inference='none',meta_shacl=True,advanced=False)
 return {'conforms':bool(conforms),'report':text,'triples':len(graph)}

def graph_answer(snapshot,question):
 """Read-only bounded question router; intentionally not marketed as a live LLM."""
 q=question.strip().lower()
 if not q or len(q)>1000:raise ValueError('Question must have 1 to 1000 characters')
 g=build_graph(snapshot);validation=validate_graph(g)
 if not validation['conforms']:raise ValueError('Graph validation failed; explanation withheld')
 rows=list(g.query('''PREFIX rm:<https://example.org/retail-mesh/vocab#> PREFIX prov:<http://www.w3.org/ns/prov#> PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
 SELECT ?name ?amount ?currency WHERE {?a a rm:ProviderAward;rm:beneficiary/rdfs:label ?name;rm:amountMinor ?amount;rm:currency ?currency.}'''))
 checks=[{'name':str(n),'passed':bool(p.toPython()),'detail':str(d)} for n,p,d in g.query('''PREFIX rm:<https://example.org/retail-mesh/vocab#> SELECT ?name ?passed ?detail WHERE {?check a rm:Check;rm:name ?name;rm:passed ?passed;rm:description ?detail.}''')]
 if any(t in q for t in ['why','award','incentive','150','reward']):
  if rows:
   name,amount,currency=rows[0];minor=int(amount);answer=f'{name} received {currency} {minor//100}.{minor%100:02d} because all {len(checks)} recorded policy checks passed. The pre-sale fleet contained {snapshot["fleet_count_before_sale"]} qualifying vehicles. The exact rule version and evidence snapshot are linked below.'
  else:answer='No award was issued. Failed checks: '+', '.join(x['name'] for x in checks if not x['passed'])+'.'
 elif any(t in q for t in ['missing','fail','reject']):answer='Failed checks: '+(', '.join(x['name'] for x in checks if not x['passed']) or 'none')+'.'
 elif any(t in q for t in ['rental','service','vehicle','journey']):
  selected=snapshot['evidence']['selected'];answer=(f"{selected['rental']['OfficialActivityReference']} used vehicle #{selected['rental']['VehicleId']} during {selected['service']['OfficialActivityReference']} on vehicle #{selected['service']['VehicleId']}." if selected else 'No fully verified service and replacement-rental path was accepted.')
 elif any(t in q for t in ['fleet','count']):answer=f"The fleet had {snapshot['fleet_count_before_sale']} qualifying vehicles immediately before this sale, based on dated assignments."
 else:answer='This local assistant supports questions about award reasons, failed checks, fleet count and the accepted service/rental journey. No answer was generated for this question.'
 return {'answer':answer,'mode':'deterministic_graph_query','run_id':snapshot['run_id'],'checks':checks,'sources':[{'type':'IncentiveRun','id':snapshot['run_id']},{'type':'RuleVersion','id':snapshot['rule_version_id']},{'type':'EvidenceSnapshot','sha256':snapshot['input_hash']}],'graph_validation':validation,'live_llm':False}
