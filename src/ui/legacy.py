"""Local evaluation web application; Python standard library only."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import argparse,json,secrets,sqlite3,os
from dal.database import ROOT,MODELS,connect,initialize,rows
from biz.service import mutate
from biz import demo
from biz.incentives import migrate,evaluate,get_run
TOKEN=secrets.token_urlsafe(32)
class Handler(BaseHTTPRequestHandler):
 def reply(self,obj,status=200):
  b=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  if u.path=='/':
   b=(ROOT/'src/ui/index.html').read_bytes().replace(b'__TOKEN__',TOKEN.encode());self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b);return
  c=connect(self.server.db)
  try:
   if u.path=='/api/demo/status':
    ctx=self.demo_context(c,required=False)
    runs=[] if ctx is None else [dict(x) for x in c.execute('SELECT Id,Result,CreatedAt,EventAwardId FROM IncentiveRun WHERE ParentCompanyId=? ORDER BY Id DESC LIMIT 20',(ctx['company_id'],))]
    self.reply({'context':ctx,'runs':runs,'live_llm':False})
   elif u.path=='/api/demo/graph':
    from biz.knowledge.graph import build_graph,validate_graph
    ctx=self.demo_context(c);snapshot=get_run(c,ctx['company_id'],int(q.get('run_id',['0'])[0]));graph=build_graph(snapshot);validation=validate_graph(graph)
    if not validation['conforms']:raise ValueError('Export graph failed SHACL validation')
    fmt=q.get('format',['turtle'])[0]
    if fmt not in ['turtle','json-ld']:raise ValueError('Unsupported graph format')
    b=graph.serialize(format=fmt).encode();self.send_response(200);self.send_header('Content-Type','text/turtle; charset=utf-8' if fmt=='turtle' else 'application/ld+json');self.send_header('Content-Disposition','attachment; filename="retail-mesh-run-'+str(snapshot['run_id'])+('.ttl"' if fmt=='turtle' else '.jsonld"'));self.end_headers();self.wfile.write(b)
   elif u.path=='/api/model':self.reply(MODELS)
   elif u.path=='/api/rows':self.reply(rows(c,q.get('table',['Provider'])[0],q.get('q',[''])[0]))
   elif u.path=='/api/report':
    key=q.get('name',['journey'])[0]
    files={'journey':'04_journey.sql','metrics':'05_metrics.sql','awards':'06_awards.sql','audit':'07_audit.sql'}
    if key not in files:raise ValueError('Unknown report')
    sql=(ROOT/'src/dal/models/relational/sql'/files[key]).read_text();self.reply([dict(r) for r in c.execute(sql)])
   else:self.reply({'error':'Not found'},404)
  except (ValueError,sqlite3.Error) as e:self.reply({'error':str(e)},400)
  finally:c.close()
 def demo_context(self,c,required=True):
  r=c.execute("SELECT r.Id AS rule_id,p.ParentCompanyId AS company_id,a.Id AS activity_id FROM IncentiveRule r JOIN IncentiveProgram p ON p.Id=r.IncentiveProgramId JOIN VehicleActivity a ON a.SourceNamespace='demo.northstar' AND a.OfficialActivityReference='NS-SALE-001' WHERE p.OfficialProgramReference='SYNTHETIC-FLEET-JOURNEY' AND r.OfficialRuleCode='FLEET-JOURNEY-150'").fetchone()
  if r is None:
   if required:raise ValueError('Prepare the fictional fleet demo first')
   return None
  return dict(r)
 def do_POST(self):
  if self.path not in ['/api/mutate','/api/demo/prepare','/api/demo/evaluate','/api/demo/ask']:self.reply({'error':'Not found'},404);return
  if self.headers.get('X-CSRF-Token')!=TOKEN:self.reply({'error':'Invalid session token'},403);return
  try:
   n=int(self.headers.get('Content-Length',0))
   if n<1 or n>65536:raise ValueError('Invalid request size')
   d=json.loads(self.rfile.read(n));c=connect(self.server.db)
   try:
    if self.path=='/api/demo/prepare':self.reply({'context':demo.prepare(c),'message':'Fictional fleet demo prepared; no award has been preloaded.'});return
    if self.path=='/api/demo/evaluate':
     ctx=self.demo_context(c);self.reply(evaluate(c,ctx['company_id'],ctx['activity_id'],ctx['rule_id']));return
    if self.path=='/api/demo/ask':
     from biz.knowledge.graph import graph_answer
     ctx=self.demo_context(c);snapshot=get_run(c,ctx['company_id'],int(d.get('run_id',0)));self.reply(graph_answer(snapshot,str(d.get('question',''))));return
    id=mutate(c,d['table'],d.get('data',{}),d.get('id'),d.get('operation','save'))
   finally:c.close()
   self.reply({'id':id,'message':'Deleted successfully' if d.get('operation')=='delete' else 'Saved successfully'})
  except (ValueError,KeyError,TypeError,sqlite3.Error) as e:self.reply({'error':str(e)},400)
 def log_message(self,*args):pass
