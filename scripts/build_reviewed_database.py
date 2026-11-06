"""Build a new clean demo DB. Refuse to overwrite any existing database."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from cmn.paths import DEFAULT_DB,PREPARED_CSV,PREPROCESSED_DATA
from dal.database import initialize,connect
from biz.incentives import migrate
from cmn.accounts import migrate as migrate_accounts
from biz.csv_import import ingest,read_archive
from biz.data_quality import review
from biz.knowledge.base import export_bundle
p=argparse.ArgumentParser();p.add_argument('--output',default=str(DEFAULT_DB));a=p.parse_args()
records,_=read_archive(PREPARED_CSV);quality=review(records)
if quality['counts'].get('error'):raise ValueError('Resolve semantic errors before building the reviewed database')
initialize(a.output,seed=False);c=connect(a.output)
try:
 migrate(c);migrate_accounts(c);result=ingest(c,PREPARED_CSV)
 if c.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Foreign key check failed')
 folder=PREPROCESSED_DATA/'knowledge_exports';folder.mkdir(exist_ok=True)
 for company in c.execute('SELECT Id,LegalName FROM ParentCompany ORDER BY Id'):
  (folder/f"company-{company['Id']}-okf.zip").write_bytes(export_bundle(c,company['Id'],{'Role':'CompanyAdmin','ProviderId':None}))
 (PREPROCESSED_DATA/'quality'/'import-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'database':str(a.output),'companies':c.execute('SELECT COUNT(*) FROM ParentCompany').fetchone()[0],'imported_records':sum(result['counts'].values()),'tables':c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0],'users':c.execute('SELECT COUNT(*) FROM AppUser').fetchone()[0]},indent=2))
finally:c.close()
