"""SQLite adapter. Connections always enforce foreign keys."""
from pathlib import Path
import sqlite3,json
from cmn.paths import ROOT, SQL
MODELS=json.loads((SQL.parent/'dictionary.json').read_text())
def connect(path):
 c=sqlite3.connect(path);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=5000');return c

def initialize(path, seed=True):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():raise FileExistsError(f'Database already exists: {path}. Use a different path; initialization never overwrites data.')
 c=connect(path)
 try:
  for f in ['01_schema.sql','02_integrity.sql']+(['03_seed.sql'] if seed else []):c.executescript((SQL/f).read_text())
  if c.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Foreign-key validation failed')
 finally:c.close()

def rows(c,table,search=''):
 if table not in MODELS:raise ValueError('Unknown relation')
 cols=['Id']+MODELS[table]['fields'];where=' OR '.join(f'CAST("{x}" AS TEXT) LIKE ?' for x in cols)
 return [dict(x) for x in c.execute(f'SELECT * FROM "{table}" WHERE {where} ORDER BY Id LIMIT 300',['%'+search+'%']*len(cols))]

def save(c,table,data,row_id=None):
 if table not in MODELS:raise ValueError('Unknown relation')
 fields=MODELS[table]['fields'];data={k:v for k,v in data.items() if k in fields}
 if row_id:
  q=f'UPDATE "{table}" SET '+','.join(f'"{k}"=?' for k in data)+' WHERE Id=?';params=list(data.values())+[row_id]
 else:q=f'INSERT INTO "{table}" ('+','.join(f'"{k}"' for k in data)+') VALUES ('+','.join('?' for _ in data)+')';params=list(data.values())
 cur=c.execute(q,params)
 if row_id and cur.rowcount!=1:raise ValueError('Record no longer exists')
 return row_id or cur.lastrowid

def delete(c,table,row_id):
 if table not in MODELS:raise ValueError('Unknown relation')
 if c.execute(f'DELETE FROM "{table}" WHERE Id=?',(row_id,)).rowcount!=1:raise ValueError('Record no longer exists')
