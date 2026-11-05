-- Additive product slice; the baseline 34-relation course model is unchanged.
PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS SchemaMigration(Id INTEGER PRIMARY KEY AUTOINCREMENT, Version TEXT NOT NULL UNIQUE, AppliedAt TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS Fleet(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),
 OwnerAccountId INTEGER NOT NULL REFERENCES CustomerAccount(Id),
 FleetReference TEXT NOT NULL CHECK(length(trim(FleetReference))>0),
 FleetName TEXT NOT NULL CHECK(length(trim(FleetName))>0),
 UNIQUE(ParentCompanyId,FleetReference)
);
CREATE TABLE IF NOT EXISTS FleetVehicleAssignment(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 FleetId INTEGER NOT NULL REFERENCES Fleet(Id),
 VehicleId INTEGER NOT NULL REFERENCES Vehicle(Id),
 ValidFrom TEXT NOT NULL CHECK(strftime('%Y-%m-%dT%H:%M:%SZ',ValidFrom,'+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',ValidFrom,'+0 days')=ValidFrom),
 ValidTo TEXT CHECK(ValidTo IS NULL OR (strftime('%Y-%m-%dT%H:%M:%SZ',ValidTo,'+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',ValidTo,'+0 days')=ValidTo AND ValidTo>ValidFrom)),
 EvidenceReference TEXT NOT NULL CHECK(length(trim(EvidenceReference))>0),
 UNIQUE(FleetId,VehicleId,ValidFrom)
);
CREATE TRIGGER IF NOT EXISTS FleetAssignmentOverlap_insert BEFORE INSERT ON FleetVehicleAssignment
WHEN EXISTS(SELECT 1 FROM FleetVehicleAssignment x WHERE x.VehicleId=NEW.VehicleId AND (x.ValidTo IS NULL OR NEW.ValidFrom<x.ValidTo) AND (NEW.ValidTo IS NULL OR x.ValidFrom<NEW.ValidTo))
BEGIN SELECT RAISE(ABORT,'Vehicle has an overlapping fleet assignment'); END;
CREATE TRIGGER IF NOT EXISTS FleetAssignmentOverlap_update BEFORE UPDATE ON FleetVehicleAssignment
WHEN EXISTS(SELECT 1 FROM FleetVehicleAssignment x WHERE x.Id!=OLD.Id AND x.VehicleId=NEW.VehicleId AND (x.ValidTo IS NULL OR NEW.ValidFrom<x.ValidTo) AND (NEW.ValidTo IS NULL OR x.ValidFrom<NEW.ValidTo))
BEGIN SELECT RAISE(ABORT,'Vehicle has an overlapping fleet assignment'); END;
CREATE TABLE IF NOT EXISTS IncentiveRun(
 Id INTEGER PRIMARY KEY AUTOINCREMENT,
 ParentCompanyId INTEGER NOT NULL REFERENCES ParentCompany(Id),
 VehicleActivityId INTEGER NOT NULL REFERENCES VehicleActivity(Id),
 IncentiveRuleId INTEGER NOT NULL REFERENCES IncentiveRule(Id),
 RuleVersionId INTEGER NOT NULL REFERENCES RuleVersion(Id),
 InputHash TEXT NOT NULL CHECK(length(InputHash)=64),
 Result TEXT NOT NULL CHECK(Result IN ('Qualified','Rejected')),
 SnapshotJson TEXT NOT NULL,
 CreatedAt TEXT NOT NULL,
 EventEvaluationId INTEGER REFERENCES EventEvaluation(Id),
 EventAwardId INTEGER REFERENCES EventAward(Id),
 UNIQUE(VehicleActivityId,RuleVersionId,InputHash),
 CHECK((Result='Qualified' AND EventEvaluationId IS NOT NULL AND EventAwardId IS NOT NULL) OR (Result='Rejected' AND EventEvaluationId IS NULL AND EventAwardId IS NULL))
);
CREATE TRIGGER IF NOT EXISTS IncentiveRunFrozen_update BEFORE UPDATE ON IncentiveRun BEGIN SELECT RAISE(ABORT,'Incentive run snapshots are immutable'); END;
CREATE TRIGGER IF NOT EXISTS IncentiveRunFrozen_delete BEFORE DELETE ON IncentiveRun BEGIN SELECT RAISE(ABORT,'Incentive run snapshots are immutable'); END;
INSERT OR IGNORE INTO SchemaMigration(Version,AppliedAt) VALUES('fleet-engine-v1',strftime('%Y-%m-%dT%H:%M:%SZ','now'));
-- Engine-issued amounts are fixed; future corrections require an adjustment workflow.
CREATE TRIGGER IF NOT EXISTS EngineAwardComponentFrozen_update BEFORE UPDATE ON EventAwardComponent
WHEN EXISTS(SELECT 1 FROM IncentiveRun WHERE EventAwardId=OLD.EventAwardId)
BEGIN SELECT RAISE(ABORT,'Engine-issued benefit is immutable; adjustment workflow required'); END;
CREATE TRIGGER IF NOT EXISTS EngineAwardComponentFrozen_delete BEFORE DELETE ON EventAwardComponent
WHEN EXISTS(SELECT 1 FROM IncentiveRun WHERE EventAwardId=OLD.EventAwardId)
BEGIN SELECT RAISE(ABORT,'Engine-issued benefit is immutable; adjustment workflow required'); END;
CREATE TRIGGER IF NOT EXISTS EngineAwardFrozen_update BEFORE UPDATE ON EventAward
WHEN EXISTS(SELECT 1 FROM IncentiveRun WHERE EventAwardId=OLD.Id)
BEGIN SELECT RAISE(ABORT,'Engine-issued award is immutable; adjustment workflow required'); END;
CREATE TRIGGER IF NOT EXISTS EngineAwardFrozen_delete BEFORE DELETE ON EventAward
WHEN EXISTS(SELECT 1 FROM IncentiveRun WHERE EventAwardId=OLD.Id)
BEGIN SELECT RAISE(ABORT,'Engine-issued award is immutable; adjustment workflow required'); END;

COMMIT;
