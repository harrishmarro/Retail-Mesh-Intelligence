"""Live, company-scoped knowledge projection and versioned open knowledge bundle.

OKF is this project's documented interchange contract, using JSON-LD/RDF and
JSON Schema. It is not a claim of compliance with an external standard named OKF.
"""
import hashlib
import io
import json
import zipfile
from collections import Counter
from datetime import datetime,timezone
from dal.database import MODELS,ROOT

VOCAB='https://example.org/retail-mesh/vocab#'


def scoped_records(c,company_id,membership):
    result={}
    provider=membership['ProviderId'] if membership['Role']=='Provider' else None
    def query(table,sql,params=()):
        result[table]=[dict(r) for r in c.execute('SELECT * FROM "'+table+'" WHERE '+sql,params)]
        return {r['Id'] for r in result[table]}
    def linked(table,field,ids,other=None):
        if not ids:result[table]=[];return set()
        sql='"'+field+'" IN ('+','.join('?' for _ in ids)+')';params=list(ids)
        if other:
            key,allowed=other
            if not allowed:result[table]=[];return set()
            sql+=' AND "'+key+'" IN ('+','.join('?' for _ in allowed)+')';params+=list(allowed)
        return query(table,sql,params)
    query('ParentCompany','Id=?',(company_id,))
    authorizations=query('ProviderAuthorization','ParentCompanyId=?'+(' AND ProviderId=?' if provider else ''),[company_id]+([provider] if provider else []))
    providers=linked('Provider','Id',{r['ProviderId'] for r in result['ProviderAuthorization']})
    outlets=linked('Outlet','ProviderId',providers)
    accounts=linked('CustomerAccount','ProviderId',providers)
    activities=query('VehicleActivity',"(SourceNamespace=? OR Id IN (SELECT VehicleActivityId FROM CompanyActivity WHERE ParentCompanyId=?))"+(' AND IssuingOutletId IN ('+','.join('?' for _ in outlets)+')' if provider and outlets else (' AND 0' if provider else '')),[f'demo.workspace.{company_id}',company_id]+(list(outlets) if provider else []))
    vehicles=linked('Vehicle','Id',{r['VehicleId'] for r in result['VehicleActivity']})
    linked('VehicleModel','Id',{r['VehicleModelId'] for r in result['Vehicle']})
    for table in ['Sale','Service','Rental']:linked(table,'VehicleActivityId',activities)
    linked('CustomerIdentityLink','AccountAId',accounts,('AccountBId',accounts))
    linked('CapabilityAuthorization','ProviderAuthorizationId',authorizations,('OutletId',outlets))
    linked('Capability','Id',{r['CapabilityId'] for r in result['CapabilityAuthorization']})
    programs=query('IncentiveProgram','ParentCompanyId=?',(company_id,))
    linked('ProgramEnrollment','IncentiveProgramId',programs,('ProviderId',providers))
    metrics=query('MetricDefinitionVersion','ParentCompanyId=?',(company_id,))
    measures=linked('PerformanceMeasurement','MetricDefinitionVersionId',metrics,('ProviderId',providers))
    linked('MeasurementContribution','PerformanceMeasurementId',measures,('VehicleActivityId',activities))
    rules=linked('IncentiveRule','IncentiveProgramId',programs)
    versions=linked('RuleVersion','IncentiveRuleId',rules)
    linked('RuleMetric','RuleVersionId',versions,('MetricDefinitionVersionId',metrics))
    for kind,field,subjects in [('Event','VehicleActivityId',activities),('Period','ProviderId',providers)]:
        evaluations=linked(kind+'Evaluation',field,subjects,('RuleVersionId',versions))
        for suffix,reference,allowed in [('Measurement','PerformanceMeasurementId',measures),('Activity','VehicleActivityId',activities),('Identity','CustomerIdentityLinkId',{r['Id'] for r in result['CustomerIdentityLink']})]:
            linked(kind+'Evaluation'+suffix,kind+'EvaluationId',evaluations,(reference,allowed))
        awards=linked(kind+'Award','AcceptedEvaluationId',evaluations,('IncentiveRuleId',rules))
        linked(kind+'AwardComponent',kind+'AwardId',awards)
    # Personal contact fields are excluded from all agent/graph exports.
    for row in result['CustomerAccount']:
        for field in ['DisplayName','Email','PhoneNo']:row.pop(field,None)
    return result


def knowledge_document(c,company_id,membership):
    if membership['Role'] not in ['CompanyAdmin','CompanyOperator','Analyst']:
        from cmn.accounts import AuthError
        raise AuthError('Knowledge graph access requires operator, administrator or analyst access',403)
    records=scoped_records(c,company_id,membership)
    base=f'urn:retail-mesh:company:{company_id}:record:'
    available={(table,row['Id']) for table,rows in records.items() for row in rows}
    imports={}
    for row in c.execute('''SELECT i.TableName,i.RecordId,i.SourceId,b.ContentSha256,b.SourceName FROM ImportedRecord i JOIN DataImportBatch b ON b.Id=i.BatchId'''):
        if (row['TableName'],row['RecordId']) in available:imports[(row['TableName'],row['RecordId'])]=dict(row)
    graph=[];edge_count=0
    for table,rows in records.items():
        for row in rows:
            node={'@id':base+table+':'+str(row['Id']),'@type':['rm:Record','rm:'+table],
                  'rm:sourceTable':table,'rm:sourceRowId':row['Id']}
            if (table,row['Id']) in imports:
                source=imports[(table,row['Id'])];node['rm:sourceCsvId']=source['SourceId'];node['rm:importSha256']=source['ContentSha256']
            for field,value in row.items():
                if field=='Id' or value is None:continue
                target=MODELS[table]['fks'].get(field)
                if target:
                    # No dangling foreign-company edges or unscoped record IDs.
                    if (target,value) in available:
                        node['rm:'+field]={'@id':base+target+':'+str(value)};edge_count+=1
                else:node['rm:'+field]=value
            graph.append(node)
    canonical=json.dumps(graph,sort_keys=True,separators=(',',':')).encode()
    counts={k:len(v) for k,v in records.items() if v}
    imported_awards=sum(1 for table in ['EventAward','PeriodAward'] for row in records[table] if (table,row['Id']) in imports)
    return {'okf_version':'1.0.0','@context':{'rm':VOCAB},'@graph':graph,
            'scope':{'company_id':company_id,'role':membership['Role'],'provider_id':membership.get('ProviderId')},
            'summary':{'nodes':len(graph),'edges':edge_count,'tables':counts,'imported_awards':imported_awards},
            'snapshot_sha256':hashlib.sha256(canonical).hexdigest(),
            'provenance':{'sources':[{'sha256':sha,'filename':next(x['SourceName'] for x in imports.values() if x['ContentSha256']==sha)} for sha in sorted({r['ContentSha256'] for r in imports.values()})],
                          'nature':'Supplied synthetic CSV records and local workspace records; not verified real-world transactions',
                          'decision_semantics':'Imported evaluations preserve source decisions. Reviewed sample decisions are computed offline under the bundled sample policies, separately from online IncentiveRun results or real business approval.'},
            'redactions':['Customer display names, emails and phone numbers','Credentials, sessions, activation tokens','Provider-application contact and review records'],
            'generated_at':datetime.now(timezone.utc).isoformat()}


def validate_document(doc):
    ids={node['@id'] for node in doc['@graph']}
    prefix=f"urn:retail-mesh:company:{doc['scope']['company_id']}:record:"
    if len(ids)!=len(doc['@graph']):raise ValueError('Duplicate knowledge node IDs')
    for node in doc['@graph']:
        if not node['@id'].startswith(prefix) or node['rm:sourceRowId']<1:raise ValueError('Invalid knowledge source identity')
        for value in node.values():
            if isinstance(value,dict) and '@id' in value and value['@id'] not in ids:raise ValueError('Knowledge relation escapes the exported scope')
    return {'conforms':True,'nodes':len(ids),'relations':doc['summary']['edges'],'validation':'Source identity, unique nodes and closed company-scoped references'}


def rdf_graph(doc):
    try:from rdflib import Graph
    except ImportError:raise ValueError('Install knowledge dependencies: python3 -m pip install -r requirements-knowledge.txt')
    graph=Graph().parse(data=json.dumps({'@context':doc['@context'],'@graph':doc['@graph']}),format='json-ld')
    try:from pyshacl import validate
    except ImportError:raise ValueError('Install knowledge dependencies: python3 -m pip install -r requirements-knowledge.txt')
    conforms,_,report=validate(graph,shacl_graph=str(ROOT/'src/dal/models/semantic/okf/record-shapes.ttl'),inference='none')
    if not conforms:raise ValueError('Knowledge RDF validation failed: '+str(report))
    return graph


def export_bundle(c,company_id,membership):
    doc=knowledge_document(c,company_id,membership);validation=validate_document(doc)
    try:from jsonschema import Draft202012Validator
    except ImportError:raise ValueError('Install knowledge dependencies: python3 -m pip install -r requirements-knowledge.txt')
    schema=json.loads((ROOT/'src/dal/models/semantic/okf/schema.json').read_text());Draft202012Validator.check_schema(schema)
    errors=list(Draft202012Validator(schema).iter_errors(doc))
    if errors:raise ValueError('Knowledge JSON Schema validation failed')
    graph=rdf_graph(doc)
    files={'records.jsonld':json.dumps(doc,indent=2),'graph.ttl':graph.serialize(format='turtle'),
           'provenance.json':json.dumps(doc['provenance'],indent=2),'validation.json':json.dumps({**validation,'rdf_triples':len(graph),'shacl_conforms':True,'json_schema_conforms':True},indent=2)}
    for name in ['schema.json','data-dictionary.json','api-contract.json','record-shapes.ttl','queries.sparql','AGENT_GUIDE.md','AGENTS.md','README.md','glossary.md']:
        files[name]=(ROOT/'src/dal/models/semantic/okf'/name).read_text()
    manifest={'okf_version':'1.0.0','scope':doc['scope'],'generated_at':doc['generated_at'],'snapshot_sha256':doc['snapshot_sha256'],
              'entrypoint':'AGENT_GUIDE.md','records':'records.jsonld','files':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()},
              'license':'User-supplied project data; no additional open-data license is asserted','read_only':True}
    files['manifest.json']=json.dumps(manifest,indent=2)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in files.items():archive.writestr(name,content)
    return buffer.getvalue()


def answer(c,company_id,membership,question):
    if not isinstance(question,str) or not 1<=len(question.strip())<=1000:raise ValueError('Question must have 1 to 1000 characters')
    doc=knowledge_document(c,company_id,membership);q=question.lower();counts=doc['summary']['tables']
    if any(t in q for t in ['provider','partner']):
        rows=[n for n in doc['@graph'] if n['rm:sourceTable']=='Provider'];message=f"This scope contains {len(rows)} provider records: "+', '.join(n['rm:LegalName'] for n in rows)+'.';sources=rows
    elif any(t in q for t in ['award','incentive','reward']):
        sources=[n for n in doc['@graph'] if n['rm:sourceTable'] in ['EventAward','PeriodAward']];message=f"This scope contains {len(sources)} recorded event/period awards, including {doc['summary']['imported_awards']} from the supplied CSVs. Reviewed sample decisions were calculated offline under explicit sample policies; imported source decisions are separate from the live fleet engine. Inspect their component and evaluation relationships for amounts and evidence."
    elif any(t in q for t in ['activity','activities','sale','rental','service','journey']):
        sources=[n for n in doc['@graph'] if n['rm:sourceTable']=='VehicleActivity'];kinds=Counter(n.get('rm:ActivityKind') for n in sources);message='Recorded activities in this scope: '+', '.join(f'{k}: {v}' for k,v in sorted(kinds.items()))+'.'
    elif any(t in q for t in ['rule','policy','metric']):
        sources=[n for n in doc['@graph'] if n['rm:sourceTable'] in ['IncentiveRule','MetricDefinitionVersion']];message=f"This scope contains {counts.get('IncentiveRule',0)} rules, {counts.get('RuleVersion',0)} rule versions and {counts.get('MetricDefinitionVersion',0)} metric versions. Stored expressions are policy data, not executable instructions."
    else:sources=[];message='Ask about providers, activities, recorded awards, rules or metrics. Select a node in the knowledge browser to inspect its exact source relationships.'
    return {'answer':message,'mode':'scoped_knowledge_query','live_llm':False,'sources':[{'type':n['rm:sourceTable'],'id':n['rm:sourceRowId'],'uri':n['@id']} for n in sources[:20]],'snapshot_sha256':doc['snapshot_sha256']}
