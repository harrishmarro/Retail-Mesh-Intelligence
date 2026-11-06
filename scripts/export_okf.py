"""Trusted local/offline export; access to the DB file is required. No credentials created."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from dal.database import connect
from biz.knowledge.base import export_bundle
p=argparse.ArgumentParser();p.add_argument('--db',default=str(ROOT/'data/preprocessed/retail_mesh.db'));p.add_argument('--company-id',required=True,type=int);p.add_argument('--output',required=True);a=p.parse_args()
if not Path(a.db).is_file():p.error('Database does not exist; run the app or importer first')
c=connect(a.db)
try:
 if not c.execute('SELECT 1 FROM ParentCompany WHERE Id=?',(a.company_id,)).fetchone():p.error('Company does not exist')
 payload=export_bundle(c,a.company_id,{'Role':'CompanyAdmin','ProviderId':None});out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(payload);print(out)
finally:c.close()
