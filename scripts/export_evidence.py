"""Export observed query results as machine-readable evaluation evidence."""
import sys,json,platform,sqlite3
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from dal.database import connect,SQL,MODELS
c=connect(R/'data/preprocessed/retail_mesh.db')
r={'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'relation_count':len(MODELS),'rows_per_relation':{t:c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in MODELS},'foreign_key_check':[list(r) for r in c.execute('PRAGMA foreign_key_check')],'integrity_check':c.execute('PRAGMA integrity_check').fetchone()[0]}
for name in ['04_journey','05_metrics','06_awards','07_audit']:r[name]=[dict(x) for x in c.execute((SQL/(name+'.sql')).read_text())]
(R/'doc/observed-results.json').write_text(json.dumps(r,indent=2));print('Observed query evidence exported')
