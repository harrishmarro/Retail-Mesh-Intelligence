"""Application entry point. UI handlers, business logic and data access live in their layers."""
from http.server import ThreadingHTTPServer
from pathlib import Path
import argparse,os
from dal.database import ROOT,connect,initialize
from biz.incentives import migrate
from ui.legacy import Handler

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--db',default=str(ROOT/'data/preprocessed/retail_mesh.db'));p.add_argument('--init-only',action='store_true');p.add_argument('--port',type=int,default=8000);p.add_argument('--legacy-demo',action='store_true',help='Explicit unauthenticated course demo, loopback only');a=p.parse_args()
 if not Path(a.db).exists():initialize(a.db)
 connection=connect(a.db)
 try:
  migrate(connection)
  from cmn.accounts import migrate as migrate_accounts
  migrate_accounts(connection)
 finally:connection.close()
 if os.name=='posix':os.chmod(a.db,0o600)
 if not a.init_only:
  from ui.portal import PortalHandler
  s=ThreadingHTTPServer(('127.0.0.1',a.port),Handler if a.legacy_demo else PortalHandler);s.db=a.db;print(f'Retail-Mesh: http://127.0.0.1:{a.port}',flush=True)
  try:s.serve_forever()
  except KeyboardInterrupt:pass
