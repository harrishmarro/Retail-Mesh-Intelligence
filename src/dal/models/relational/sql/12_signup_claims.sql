-- Public application ownership and provider service workflows.
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS ProviderSignupPortal(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER NOT NULL UNIQUE REFERENCES ParentCompany(Id),
 PublicCode TEXT NOT NULL UNIQUE,
 Enabled INTEGER NOT NULL DEFAULT 0 CHECK(Enabled IN (0,1)),
 UpdatedBy INTEGER NOT NULL REFERENCES AppUser(Id),UpdatedAt INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ProviderApplicationAccess(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ApplicationId INTEGER NOT NULL UNIQUE REFERENCES ProviderApplication(Id),
 TokenHash TEXT NOT NULL UNIQUE,CreatedAt INTEGER NOT NULL,ExpiresAt INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS IncentiveClaim(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 Reference TEXT NOT NULL UNIQUE,
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),
 ProviderId INTEGER NOT NULL REFERENCES Provider(Id),
 SubmittedBy INTEGER NOT NULL REFERENCES AppUser(Id),
 IncentiveRuleId INTEGER NOT NULL REFERENCES IncentiveRule(Id),
 ClaimType TEXT NOT NULL CHECK(ClaimType IN ('Event','Period')),
 VehicleActivityId INTEGER REFERENCES VehicleActivity(Id),
 PeriodStart TEXT,PeriodEnd TEXT,
 Statement TEXT NOT NULL,EvidenceReference TEXT NOT NULL,
 RequestedAmountMinor INTEGER,Currency TEXT,
 Status TEXT NOT NULL DEFAULT 'Submitted' CHECK(Status IN ('Submitted','UnderReview','ChangesNeeded','Approved','Rejected')),
 ReviewNote TEXT NOT NULL DEFAULT '',Version INTEGER NOT NULL DEFAULT 1,
 CreatedAt INTEGER NOT NULL,UpdatedAt INTEGER NOT NULL,
 CHECK((ClaimType='Event' AND VehicleActivityId IS NOT NULL AND PeriodStart IS NULL AND PeriodEnd IS NULL) OR (ClaimType='Period' AND VehicleActivityId IS NULL AND PeriodStart IS NOT NULL AND PeriodEnd>PeriodStart)),
 CHECK((RequestedAmountMinor IS NULL AND Currency IS NULL) OR (RequestedAmountMinor>=0 AND length(Currency)=3))
);
CREATE TABLE IF NOT EXISTS IncentiveClaimEvent(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,ClaimId INTEGER NOT NULL REFERENCES IncentiveClaim(Id),
 ActorId INTEGER NOT NULL REFERENCES AppUser(Id),Action TEXT NOT NULL,Message TEXT NOT NULL,CreatedAt INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ProviderConcern(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),ProviderId INTEGER NOT NULL REFERENCES Provider(Id),
 RaisedBy INTEGER NOT NULL REFERENCES AppUser(Id),ClaimId INTEGER REFERENCES IncentiveClaim(Id),
 Kind TEXT NOT NULL DEFAULT 'Incentive' CHECK(Kind IN ('Incentive','WorkspaceAccess')),
 RequestedWorkspaceName TEXT NOT NULL DEFAULT '',
 Subject TEXT NOT NULL,Status TEXT NOT NULL DEFAULT 'Open' CHECK(Status IN ('Open','UnderReview','Resolved','Closed')),
 Version INTEGER NOT NULL DEFAULT 1,CreatedAt INTEGER NOT NULL,UpdatedAt INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ProviderConcernMessage(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,ConcernId INTEGER NOT NULL REFERENCES ProviderConcern(Id),
 ActorId INTEGER NOT NULL REFERENCES AppUser(Id),Message TEXT NOT NULL,CreatedAt INTEGER NOT NULL
);
CREATE TRIGGER IF NOT EXISTS ClaimEventFrozenUpdate BEFORE UPDATE ON IncentiveClaimEvent BEGIN SELECT RAISE(ABORT,'Claim history is append-only');END;
CREATE TRIGGER IF NOT EXISTS ClaimEventFrozenDelete BEFORE DELETE ON IncentiveClaimEvent BEGIN SELECT RAISE(ABORT,'Claim history is append-only');END;
CREATE TRIGGER IF NOT EXISTS ConcernMessageFrozenUpdate BEFORE UPDATE ON ProviderConcernMessage BEGIN SELECT RAISE(ABORT,'Concern messages are append-only');END;
CREATE TRIGGER IF NOT EXISTS ConcernMessageFrozenDelete BEFORE DELETE ON ProviderConcernMessage BEGIN SELECT RAISE(ABORT,'Concern messages are append-only');END;
CREATE INDEX IF NOT EXISTS IX_ClaimScope ON IncentiveClaim(ParentCompanyId,ProviderId,Status);
CREATE INDEX IF NOT EXISTS IX_ConcernScope ON ProviderConcern(ParentCompanyId,ProviderId,Status);
INSERT OR IGNORE INTO SchemaMigration(Version,AppliedAt) VALUES('provider-signup-claims-v1',strftime('%Y-%m-%dT%H:%M:%SZ','now'));
COMMIT;
