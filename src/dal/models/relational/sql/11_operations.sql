-- Operational extensions; the supplied ER domain relations remain unchanged.
PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS DataImportBatch(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ContentSha256 TEXT NOT NULL UNIQUE,
 SourceName TEXT NOT NULL,
 ImportedAt INTEGER NOT NULL,
 CountsJson TEXT NOT NULL,
 JourneyReportRows INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ImportedRecord(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 BatchId INTEGER NOT NULL REFERENCES DataImportBatch(Id),
 TableName TEXT NOT NULL,
 SourceId INTEGER NOT NULL,
 RecordId INTEGER NOT NULL,
 UNIQUE(BatchId,TableName,SourceId),
 UNIQUE(TableName,RecordId)
);
CREATE TABLE IF NOT EXISTS CompanyActivity(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),
 VehicleActivityId INTEGER NOT NULL REFERENCES VehicleActivity(Id),
 Origin TEXT NOT NULL,
 UNIQUE(ParentCompanyId,VehicleActivityId)
);
CREATE TABLE IF NOT EXISTS ProviderApplication(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),
 LegalName TEXT NOT NULL,
 RegistrationJurisdiction TEXT NOT NULL,
 BusinessRegistrationNumber TEXT NOT NULL,
 ContactName TEXT NOT NULL,
 ContactEmail TEXT NOT NULL,
 OutletName TEXT NOT NULL,
 OutletAddress TEXT NOT NULL,
 CapabilitiesJson TEXT NOT NULL,
 State TEXT NOT NULL DEFAULT 'Draft' CHECK(State IN ('Draft','Submitted','UnderReview','NeedsChanges','Validated','Approved','Provisioned','Rejected')),
 ProviderId INTEGER REFERENCES Provider(Id),
 CreatedBy INTEGER REFERENCES AppUser(Id),
 RequestedProgramsJson TEXT NOT NULL DEFAULT '[]',
 ContactPhone TEXT NOT NULL DEFAULT '',
 Website TEXT NOT NULL DEFAULT '',
 ApplicantEvidenceReferences TEXT NOT NULL DEFAULT '',
 CreatedAt INTEGER NOT NULL,
 UpdatedAt INTEGER NOT NULL,
 Version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(ParentCompanyId,RegistrationJurisdiction,BusinessRegistrationNumber)
);
CREATE TABLE IF NOT EXISTS ProviderValidationCheck(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ApplicationId INTEGER NOT NULL REFERENCES ProviderApplication(Id),
 CheckCode TEXT NOT NULL CHECK(CheckCode IN ('business_registration','contact_authority','capability_compliance')),
 EvidenceReference TEXT NOT NULL,
 ReviewedBy INTEGER NOT NULL REFERENCES AppUser(Id),
 ReviewedAt INTEGER NOT NULL,
 UNIQUE(ApplicationId,CheckCode)
);
CREATE TABLE IF NOT EXISTS ProviderInvitation(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ApplicationId INTEGER NOT NULL REFERENCES ProviderApplication(Id),
 TokenHash TEXT NOT NULL UNIQUE,
 CreatedBy INTEGER NOT NULL REFERENCES AppUser(Id),
 CreatedAt INTEGER NOT NULL,
 ExpiresAt INTEGER NOT NULL,
 UsedAt INTEGER,
 Revoked INTEGER NOT NULL DEFAULT 0 CHECK(Revoked IN (0,1))
);
CREATE TABLE IF NOT EXISTS RequestObservation(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER REFERENCES ParentCompany(Id),
 RequestId TEXT NOT NULL,
 Route TEXT NOT NULL,
 Method TEXT NOT NULL,
 StatusCode INTEGER NOT NULL,
 DurationMs REAL NOT NULL,
 RecordedAt INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS IX_RequestObservation_CompanyTime ON RequestObservation(ParentCompanyId,RecordedAt);
CREATE INDEX IF NOT EXISTS IX_ProviderApplication_CompanyState ON ProviderApplication(ParentCompanyId,State);
CREATE VIEW IF NOT EXISTS JourneyOverview AS
 SELECT a.Id AS ActivityId,a.OfficialActivityReference,a.ActivityKind,a.ActivityStatus,a.StartedAt,a.EndedAt,
        p.LegalName AS Provider,o.OutletName,ca.DisplayName AS ProviderLocalCustomerAccount,
        v.VIN,m.Manufacturer,m.ModelName,m.ModelYear,svc.ServiceType,svc.Outcome,
        rental.ReplacementPurpose,replacement.OfficialActivityReference AS ReplacementForService
 FROM VehicleActivity a JOIN Outlet o ON o.Id=a.IssuingOutletId JOIN Provider p ON p.Id=o.ProviderId
 JOIN CustomerAccount ca ON ca.Id=a.CustomerAccountId JOIN Vehicle v ON v.Id=a.VehicleId
 JOIN VehicleModel m ON m.Id=v.VehicleModelId LEFT JOIN Service svc ON svc.VehicleActivityId=a.Id
 LEFT JOIN Rental rental ON rental.VehicleActivityId=a.Id LEFT JOIN Service replaced ON replaced.Id=rental.ReplacementForServiceId
 LEFT JOIN VehicleActivity replacement ON replacement.Id=replaced.VehicleActivityId;
INSERT OR IGNORE INTO SchemaMigration(Version,AppliedAt) VALUES('operations-knowledge-v1',strftime('%Y-%m-%dT%H:%M:%SZ','now'));
COMMIT;
