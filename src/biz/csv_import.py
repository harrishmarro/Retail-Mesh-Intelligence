"""Atomic, fingerprinted CSV import. Never overwrite or re-key existing domain rows."""
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from dal.database import MODELS
from biz.service import validate
from cmn import accounts

# Cyclic FK targets have preallocated IDs. Decision evidence must precede awards.
ORDER = ['ParentCompany','Provider','VehicleModel','Vehicle','Outlet','CustomerAccount',
         'CustomerIdentityLink','ProviderAuthorization','Capability','CapabilityAuthorization',
         'IncentiveProgram','ProgramEnrollment','MetricDefinitionVersion','IncentiveRule',
         'RuleVersion','RuleMetric','VehicleActivity','Sale','Service','Rental',
         'PerformanceMeasurement','MeasurementContribution','EventEvaluation','PeriodEvaluation',
         'EventEvaluationMeasurement','EventEvaluationActivity','EventEvaluationIdentity',
         'PeriodEvaluationMeasurement','PeriodEvaluationActivity','PeriodEvaluationIdentity',
         'EventAwardComponent','PeriodAwardComponent','EventAward','PeriodAward']


def read_archive(path):
    records, raw = {}, {}
    with zipfile.ZipFile(path) as archive:
        if sum(f.file_size for f in archive.infolist()) > 20_000_000:
            raise ValueError('CSV archive is too large')
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            name = Path(entry.filename).name
            if not name.endswith('.csv'):
                raise ValueError('Only CSV files are supported')
            table = name[:-4]
            if table in records or table not in set(MODELS) | {'JourneyOverview'}:
                raise ValueError('Unknown or duplicate CSV: '+name)
            payload = archive.read(entry)
            reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig')))
            rows = list(reader)
            if table != 'JourneyOverview':
                expected = {'Id', *MODELS[table]['fields']}
                if set(reader.fieldnames or []) != expected or len(reader.fieldnames) != len(expected):
                    raise ValueError('CSV columns do not match '+table)
            if any(None in row or any(v is None for v in row.values()) for row in rows):
                raise ValueError('Malformed CSV row in '+table)
            records[table], raw[table] = rows, payload
    if set(records) != set(MODELS) | {'JourneyOverview'}:
        raise ValueError('Archive must contain all 34 domain tables and JourneyOverview')
    overview = records['JourneyOverview']
    activities = records['VehicleActivity']
    if len(overview)!=len(activities) or sorted((r['OfficialActivityReference'],r['ActivityKind']) for r in overview)!=sorted((r['OfficialActivityReference'],r['ActivityKind']) for r in activities):
        raise ValueError('JourneyOverview does not match the supplied activity records')
    # Names and decoded bytes, not ZIP timestamps/compression, define batch identity.
    fingerprint = hashlib.sha256()
    for table in sorted(raw):
        fingerprint.update(table.encode()+b'\0'+raw[table]+b'\0')
    return records, fingerprint.hexdigest()


def grant_imported_companies(c, actor, batch_id):
    if not c.execute("SELECT 1 FROM CompanyMembership WHERE UserId=? AND Role='CompanyAdmin' AND Status='Active'", (actor,)).fetchone():
        raise accounts.AuthError('Company administrator required',403)
    ids = [r[0] for r in c.execute("SELECT RecordId FROM ImportedRecord WHERE BatchId=? AND TableName='ParentCompany'", (batch_id,))]
    for cid in ids:
        others = c.execute("SELECT 1 FROM CompanyMembership WHERE ParentCompanyId=? AND Status='Active' AND UserId!=?", (cid,actor)).fetchone()
        own = c.execute("SELECT 1 FROM CompanyMembership WHERE ParentCompanyId=? AND UserId=? AND Role='CompanyAdmin' AND Status='Active'", (cid,actor)).fetchone()
        if others and not own:
            raise accounts.AuthError('Imported company already has an administrator; access cannot be claimed',403)
        c.execute("INSERT INTO CompanyMembership(UserId,ParentCompanyId,Role) VALUES(?,?,'CompanyAdmin') ON CONFLICT(UserId,ParentCompanyId) DO UPDATE SET Role='CompanyAdmin',ProviderId=NULL,Status='Active'", (actor,cid))
        accounts.audit(c,actor,cid,'import.admin_assigned',batch_id)
    return ids


def ingest(c, path, actor=None):
    records, fingerprint = read_archive(path)
    c.execute('BEGIN IMMEDIATE')
    try:
        previous = c.execute('SELECT * FROM DataImportBatch WHERE ContentSha256=?', (fingerprint,)).fetchone()
        if previous:
            result = {'batch_id':previous['Id'],'sha256':fingerprint,'counts':json.loads(previous['CountsJson']),'replayed':True}
        else:
            mapping, prepared = {}, {}
            for table in ORDER:
                offset = c.execute(f'SELECT COALESCE(MAX(Id),0) FROM "{table}"').fetchone()[0]
                mapping[table], prepared[table] = {}, []
                for line, row in enumerate(records[table], 2):
                    try:
                        source = int(row['Id'])
                        if source < 1 or source in mapping[table]:
                            raise ValueError('Duplicate or invalid source Id')
                        values = validate(table,{k:v for k,v in row.items() if k!='Id'})
                        mapping[table][source] = offset+source
                        prepared[table].append((source, values, line))
                    except (ValueError,TypeError) as e:
                        raise ValueError(f'{table}.csv line {line}: {e}') from e
            # Validate every source FK before any insertion; preserve blank optional values as NULL.
            for table in ORDER:
                for source, values, line in prepared[table]:
                    for field, target in MODELS[table]['fks'].items():
                        value = values.get(field)
                        if value is not None:
                            if value not in mapping[target]:
                                raise ValueError(f'{table}.csv line {line}: missing {target} source Id {value}')
                            values[field] = mapping[target][value]
            counts = {t:len(records[t]) for t in ORDER}
            batch = c.execute('INSERT INTO DataImportBatch(ContentSha256,SourceName,ImportedAt,CountsJson,JourneyReportRows) VALUES(?,?,?,?,?)',
                              (fingerprint,Path(path).name,accounts.now(),json.dumps(counts),len(records['JourneyOverview']))).lastrowid
            for table in ORDER:
                fields = ['Id']+MODELS[table]['fields']
                query = f'INSERT INTO "{table}" ('+','.join('"'+f+'"' for f in fields)+') VALUES ('+','.join('?' for _ in fields)+')'
                for source, values, line in prepared[table]:
                    try:
                        c.execute(query,[mapping[table][source]]+[values[f] for f in fields[1:]])
                    except Exception as e:
                        raise ValueError(f'{table}.csv line {line}: {e}') from e
                    c.execute('INSERT INTO ImportedRecord(BatchId,TableName,SourceId,RecordId) VALUES(?,?,?,?)', (batch,table,source,mapping[table][source]))
            # Ownership derives from the supplied provider authorization valid at activity time.
            c.execute('''INSERT INTO CompanyActivity(ParentCompanyId,VehicleActivityId,Origin)
                         SELECT pa.ParentCompanyId,a.Id,? FROM VehicleActivity a
                         JOIN Outlet o ON o.Id=a.IssuingOutletId JOIN ProviderAuthorization pa ON pa.ProviderId=o.ProviderId
                         JOIN ImportedRecord i ON i.TableName='VehicleActivity' AND i.RecordId=a.Id AND i.BatchId=?
                         WHERE pa.AuthorizationStatus='Active' AND pa.ValidFrom<=substr(a.StartedAt,1,10)
                         AND (pa.ValidTo IS NULL OR pa.ValidTo>substr(a.StartedAt,1,10))''', ('csv:'+fingerprint,batch))
            ambiguous = c.execute('''SELECT VehicleActivityId FROM CompanyActivity
                                     WHERE Origin=? GROUP BY VehicleActivityId
                                     HAVING COUNT(*)>1 LIMIT 1''', ('csv:'+fingerprint,)).fetchone()
            if ambiguous:
                raise ValueError('An activity matches more than one company at its event date; company ownership must be resolved before import')
            assigned = c.execute('SELECT COUNT(DISTINCT VehicleActivityId) FROM CompanyActivity WHERE Origin=?', ('csv:'+fingerprint,)).fetchone()[0]
            if assigned != counts['VehicleActivity']:
                raise ValueError('Some activities have no valid company authorization at their event date')
            if c.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Foreign key validation failed; import rolled back')
            result = {'batch_id':batch,'sha256':fingerprint,'counts':counts,'replayed':False}
        if actor is not None:
            result['company_ids'] = grant_imported_companies(c,actor,result['batch_id'])
        c.commit()
        return result
    except Exception:
        c.rollback()
        raise
