"""Import the supplied dataset into a new or existing local DB, without replacing rows."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import initialize,connect
from biz.incentives import migrate
from cmn import accounts
from biz.csv_import import ingest
p=argparse.ArgumentParser();p.add_argument('--db',default=str(ROOT/'data/preprocessed/retail_mesh.db'));p.add_argument('--zip',default=str(ROOT/'data/preprocessed/RetailMesh_Reviewed_CSV_Data.zip'));p.add_argument('--grant-admin',help='Existing local company-admin email to grant the imported company memberships');a=p.parse_args()
if not Path(a.db).exists():initialize(a.db)
c=connect(a.db)
try:
 migrate(c);accounts.migrate(c);actor=None
 if a.grant_admin:
  row=c.execute('SELECT Id FROM AppUser WHERE Email=?',(accounts.email(a.grant_admin),)).fetchone()
  if row is None:raise ValueError('Administrator account does not exist')
  actor=row['Id']
 print(json.dumps(ingest(c,a.zip,actor),indent=2))
finally:c.close()
