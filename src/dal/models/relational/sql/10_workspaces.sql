PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS AppUser(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 Email TEXT NOT NULL COLLATE NOCASE UNIQUE,
 DisplayName TEXT NOT NULL,
 PasswordHash TEXT NOT NULL,
 Status TEXT NOT NULL DEFAULT 'Active' CHECK(Status IN ('Active','Disabled')),
 CreatedAt INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS CompanyMembership(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 UserId INTEGER NOT NULL REFERENCES AppUser(Id),
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),
 Role TEXT NOT NULL CHECK(Role IN ('CompanyAdmin','CompanyOperator','Analyst','Provider')),
 ProviderId INTEGER REFERENCES Provider(Id),
 Status TEXT NOT NULL DEFAULT 'Active' CHECK(Status IN ('Active','Revoked')),
 UNIQUE(UserId,ParentCompanyId),
 CHECK((Role='Provider' AND ProviderId IS NOT NULL) OR (Role!='Provider' AND ProviderId IS NULL))
);
CREATE TABLE IF NOT EXISTS AuthSession(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 TokenHash TEXT NOT NULL UNIQUE,
 UserId INTEGER NOT NULL REFERENCES AppUser(Id),
 CsrfToken TEXT NOT NULL,
 CreatedAt INTEGER NOT NULL,
 ExpiresAt INTEGER NOT NULL,
 Revoked INTEGER NOT NULL DEFAULT 0 CHECK(Revoked IN (0,1))
);
CREATE TABLE IF NOT EXISTS LoginAttempt(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 IdentityKey TEXT NOT NULL,
 AttemptedAt INTEGER NOT NULL,
 Success INTEGER NOT NULL CHECK(Success IN (0,1))
);
CREATE INDEX IF NOT EXISTS IX_LoginAttempt_IdentityTime ON LoginAttempt(IdentityKey,AttemptedAt);
CREATE TABLE IF NOT EXISTS WorkspaceAuditEvent(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 UserId INTEGER REFERENCES AppUser(Id),
 ParentCompanyId INTEGER REFERENCES ParentCompany(Id),
 Action TEXT NOT NULL,
 TargetReference TEXT NOT NULL,
 CreatedAt INTEGER NOT NULL
);
CREATE TRIGGER IF NOT EXISTS WorkspaceAuditFrozen_update BEFORE UPDATE ON WorkspaceAuditEvent BEGIN SELECT RAISE(ABORT,'Audit history is immutable');END;
CREATE TRIGGER IF NOT EXISTS WorkspaceAuditFrozen_delete BEFORE DELETE ON WorkspaceAuditEvent BEGIN SELECT RAISE(ABORT,'Audit history is immutable');END;
INSERT OR IGNORE INTO SchemaMigration(Version,AppliedAt) VALUES('company-workspaces-v1',strftime('%Y-%m-%dT%H:%M:%SZ','now'));
COMMIT;
