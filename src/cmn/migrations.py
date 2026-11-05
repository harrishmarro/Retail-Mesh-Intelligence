"""Transactional constraint upgrades for existing installations; preserve row IDs."""
from dal.database import SQL

def upgrade_signup(c):
    membership=c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='CompanyMembership'").fetchone()[0]
    columns={r[1]:r for r in c.execute('PRAGMA table_info(ProviderApplication)')}
    rebuild_membership='CompanyOperator' not in membership
    rebuild_application=bool(columns['CreatedBy'][3]) or 'RequestedProgramsJson' not in columns or 'ApplicantEvidenceReferences' not in columns
    if not rebuild_membership and not rebuild_application:return
    if c.in_transaction:raise ValueError('Constraint migration requires an idle connection')
    c.execute('PRAGMA foreign_keys=OFF')
    try:
        c.execute('BEGIN IMMEDIATE')
        if rebuild_membership:
            c.execute('''CREATE TABLE CompanyMembership_new(Id INTEGER PRIMARY KEY AUTOINCREMENT,UserId INTEGER NOT NULL REFERENCES AppUser(Id),ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),Role TEXT NOT NULL CHECK(Role IN ('CompanyAdmin','CompanyOperator','Analyst','Provider')),ProviderId INTEGER REFERENCES Provider(Id),Status TEXT NOT NULL DEFAULT 'Active' CHECK(Status IN ('Active','Revoked')),UNIQUE(UserId,ParentCompanyId),CHECK((Role='Provider' AND ProviderId IS NOT NULL) OR (Role!='Provider' AND ProviderId IS NULL)))''')
            c.execute('INSERT INTO CompanyMembership_new SELECT * FROM CompanyMembership');c.execute('DROP TABLE CompanyMembership');c.execute('ALTER TABLE CompanyMembership_new RENAME TO CompanyMembership')
        if rebuild_application:
            # Reuse the current schema declaration without rewriting referenced child table names.
            schema=(SQL/'11_operations.sql').read_text();start=schema.index('CREATE TABLE IF NOT EXISTS ProviderApplication(');end=schema.index('\n);',start)+3
            declaration=schema[start:end].replace('CREATE TABLE IF NOT EXISTS ProviderApplication(','CREATE TABLE ProviderApplication_new(')
            c.execute(declaration)
            old=[r[1] for r in c.execute('PRAGMA table_info(ProviderApplication)')];names=','.join('"'+name+'"' for name in old)
            c.execute('INSERT INTO ProviderApplication_new('+names+') SELECT '+names+' FROM ProviderApplication')
            c.execute('DROP TABLE ProviderApplication');c.execute('ALTER TABLE ProviderApplication_new RENAME TO ProviderApplication')
            c.execute('CREATE INDEX IF NOT EXISTS IX_ProviderApplication_CompanyState ON ProviderApplication(ParentCompanyId,State)')
        if c.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Signup migration violated existing relationships')
        c.commit()
    except Exception:c.rollback();raise
    finally:c.execute('PRAGMA foreign_keys=ON')
