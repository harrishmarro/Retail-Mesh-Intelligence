PRAGMA foreign_keys=ON;
BEGIN;
INSERT INTO Provider(RegistrationJurisdiction,BusinessRegistrationNumber,LegalName)
VALUES ('CA-BC','CRUD-DEMO-001','Temporary demo provider');
SELECT Id,LegalName FROM Provider WHERE BusinessRegistrationNumber='CRUD-DEMO-001';
UPDATE Provider SET LegalName='Updated demo provider' WHERE BusinessRegistrationNumber='CRUD-DEMO-001';
SELECT Id,LegalName FROM Provider WHERE BusinessRegistrationNumber='CRUD-DEMO-001';
DELETE FROM Provider WHERE BusinessRegistrationNumber='CRUD-DEMO-001';
COMMIT;
