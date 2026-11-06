-- Generated from the supplied ER model; edit the generator, then regenerate.

PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE ParentCompany (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  RegistrationJurisdiction TEXT NOT NULL CHECK (RegistrationJurisdiction IS NULL OR length(trim(RegistrationJurisdiction)) > 0),
  BusinessRegistrationNumber TEXT NOT NULL CHECK (BusinessRegistrationNumber IS NULL OR length(trim(BusinessRegistrationNumber)) > 0),
  LegalName TEXT NOT NULL CHECK (LegalName IS NULL OR length(trim(LegalName)) > 0),
  CONSTRAINT UK_ParentCompany_BusinessKey UNIQUE (RegistrationJurisdiction, BusinessRegistrationNumber)
);

CREATE TABLE ProviderAuthorization (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ParentCompanyId INTEGER NOT NULL,
  ProviderId INTEGER NOT NULL,
  ValidFrom TEXT NOT NULL CHECK (ValidFrom IS NULL OR length(trim(ValidFrom)) > 0) CHECK (ValidFrom IS NULL OR (length(ValidFrom)=10 AND date(ValidFrom, '+0 days') IS NOT NULL AND date(ValidFrom, '+0 days')=ValidFrom)),
  ValidTo TEXT CHECK (ValidTo IS NULL OR length(trim(ValidTo)) > 0) CHECK (ValidTo IS NULL OR (length(ValidTo)=10 AND date(ValidTo, '+0 days') IS NOT NULL AND date(ValidTo, '+0 days')=ValidTo)),
  AuthorizationStatus TEXT NOT NULL CHECK (AuthorizationStatus IS NULL OR length(trim(AuthorizationStatus)) > 0),
  CONSTRAINT UK_ProviderAuthorization_BusinessKey UNIQUE (ParentCompanyId, ProviderId, ValidFrom),
  CONSTRAINT FK_ProviderAuthorization_ParentCompanyId_2_ParentCompany_Id FOREIGN KEY (ParentCompanyId) REFERENCES ParentCompany(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_ProviderAuthorization_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((ValidTo IS NULL OR ValidTo > ValidFrom))
);

CREATE INDEX IX_ProviderAuthorization_ParentCompanyId ON ProviderAuthorization(ParentCompanyId);

CREATE INDEX IX_ProviderAuthorization_ProviderId ON ProviderAuthorization(ProviderId);

CREATE TABLE VehicleModel (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  Manufacturer TEXT NOT NULL CHECK (Manufacturer IS NULL OR length(trim(Manufacturer)) > 0),
  CatalogueNamespace TEXT NOT NULL CHECK (CatalogueNamespace IS NULL OR length(trim(CatalogueNamespace)) > 0),
  ManufacturerModelCode TEXT NOT NULL CHECK (ManufacturerModelCode IS NULL OR length(trim(ManufacturerModelCode)) > 0),
  ModelYear INTEGER NOT NULL,
  TrimCode TEXT NOT NULL CHECK (TrimCode IS NULL OR length(trim(TrimCode)) > 0),
  ModelName TEXT NOT NULL CHECK (ModelName IS NULL OR length(trim(ModelName)) > 0),
  CONSTRAINT UK_VehicleModel_BusinessKey UNIQUE (Manufacturer, CatalogueNamespace, ManufacturerModelCode, ModelYear, TrimCode)
);

CREATE TABLE IncentiveProgram (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ParentCompanyId INTEGER NOT NULL,
  OfficialProgramReference TEXT NOT NULL CHECK (OfficialProgramReference IS NULL OR length(trim(OfficialProgramReference)) > 0),
  ProgramName TEXT NOT NULL CHECK (ProgramName IS NULL OR length(trim(ProgramName)) > 0),
  ActiveFrom TEXT NOT NULL CHECK (ActiveFrom IS NULL OR length(trim(ActiveFrom)) > 0) CHECK (ActiveFrom IS NULL OR (length(ActiveFrom)=10 AND date(ActiveFrom, '+0 days') IS NOT NULL AND date(ActiveFrom, '+0 days')=ActiveFrom)),
  ActiveTo TEXT CHECK (ActiveTo IS NULL OR length(trim(ActiveTo)) > 0) CHECK (ActiveTo IS NULL OR (length(ActiveTo)=10 AND date(ActiveTo, '+0 days') IS NOT NULL AND date(ActiveTo, '+0 days')=ActiveTo)),
  EventVersionPolicy TEXT NOT NULL CHECK (EventVersionPolicy IS NULL OR length(trim(EventVersionPolicy)) > 0),
  PeriodVersionPolicy TEXT NOT NULL CHECK (PeriodVersionPolicy IS NULL OR length(trim(PeriodVersionPolicy)) > 0),
  CONSTRAINT UK_IncentiveProgram_BusinessKey UNIQUE (ParentCompanyId, OfficialProgramReference),
  CONSTRAINT FK_IncentiveProgram_ParentCompanyId_2_ParentCompany_Id FOREIGN KEY (ParentCompanyId) REFERENCES ParentCompany(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((ActiveTo IS NULL OR ActiveTo > ActiveFrom))
);

CREATE INDEX IX_IncentiveProgram_ParentCompanyId ON IncentiveProgram(ParentCompanyId);

CREATE TABLE MetricDefinitionVersion (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ParentCompanyId INTEGER NOT NULL,
  OfficialMetricCode TEXT NOT NULL CHECK (OfficialMetricCode IS NULL OR length(trim(OfficialMetricCode)) > 0),
  EffectiveFrom TEXT NOT NULL CHECK (EffectiveFrom IS NULL OR length(trim(EffectiveFrom)) > 0) CHECK (EffectiveFrom IS NULL OR (length(EffectiveFrom)=10 AND date(EffectiveFrom, '+0 days') IS NOT NULL AND date(EffectiveFrom, '+0 days')=EffectiveFrom)),
  EffectiveTo TEXT CHECK (EffectiveTo IS NULL OR length(trim(EffectiveTo)) > 0) CHECK (EffectiveTo IS NULL OR (length(EffectiveTo)=10 AND date(EffectiveTo, '+0 days') IS NOT NULL AND date(EffectiveTo, '+0 days')=EffectiveTo)),
  MetricName TEXT NOT NULL CHECK (MetricName IS NULL OR length(trim(MetricName)) > 0),
  DefinitionExpression TEXT NOT NULL CHECK (DefinitionExpression IS NULL OR length(trim(DefinitionExpression)) > 0),
  UnitScheme TEXT NOT NULL CHECK (UnitScheme IS NULL OR length(trim(UnitScheme)) > 0),
  UnitCode TEXT NOT NULL CHECK (UnitCode IS NULL OR length(trim(UnitCode)) > 0),
  CONSTRAINT UK_MetricDefinitionVersion_BusinessKey UNIQUE (ParentCompanyId, OfficialMetricCode, EffectiveFrom),
  CONSTRAINT FK_MetricDefinitionVersion_ParentCompanyId_2_ParentCompany_Id FOREIGN KEY (ParentCompanyId) REFERENCES ParentCompany(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((EffectiveTo IS NULL OR EffectiveTo > EffectiveFrom))
);

CREATE INDEX IX_MetricDefinitionVersion_ParentCompanyId ON MetricDefinitionVersion(ParentCompanyId);

CREATE TABLE Provider (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  RegistrationJurisdiction TEXT NOT NULL CHECK (RegistrationJurisdiction IS NULL OR length(trim(RegistrationJurisdiction)) > 0),
  BusinessRegistrationNumber TEXT NOT NULL CHECK (BusinessRegistrationNumber IS NULL OR length(trim(BusinessRegistrationNumber)) > 0),
  LegalName TEXT NOT NULL CHECK (LegalName IS NULL OR length(trim(LegalName)) > 0),
  CONSTRAINT UK_Provider_BusinessKey UNIQUE (RegistrationJurisdiction, BusinessRegistrationNumber)
);

CREATE TABLE CustomerAccount (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ProviderId INTEGER NOT NULL,
  SourceNamespace TEXT NOT NULL CHECK (SourceNamespace IS NULL OR length(trim(SourceNamespace)) > 0),
  ExistingCustomerReference TEXT NOT NULL CHECK (ExistingCustomerReference IS NULL OR length(trim(ExistingCustomerReference)) > 0),
  DisplayName TEXT NOT NULL CHECK (DisplayName IS NULL OR length(trim(DisplayName)) > 0),
  Email TEXT CHECK (Email IS NULL OR length(trim(Email)) > 0),
  PhoneNo TEXT CHECK (PhoneNo IS NULL OR length(trim(PhoneNo)) > 0),
  CONSTRAINT UK_CustomerAccount_BusinessKey UNIQUE (ProviderId, SourceNamespace, ExistingCustomerReference),
  CONSTRAINT FK_CustomerAccount_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_CustomerAccount_ProviderId ON CustomerAccount(ProviderId);

CREATE TABLE Vehicle (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  VIN TEXT NOT NULL CHECK (VIN IS NULL OR length(trim(VIN)) > 0),
  LifecycleStatus TEXT NOT NULL CHECK (LifecycleStatus IS NULL OR length(trim(LifecycleStatus)) > 0),
  VehicleModelId INTEGER NOT NULL,
  CONSTRAINT UK_Vehicle_BusinessKey UNIQUE (VIN),
  CONSTRAINT FK_Vehicle_VehicleModelId_2_VehicleModel_Id FOREIGN KEY (VehicleModelId) REFERENCES VehicleModel(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK (length(VIN)=17 AND VIN NOT GLOB '*[^A-HJ-NPR-Z0-9]*')
);

CREATE INDEX IX_Vehicle_VehicleModelId ON Vehicle(VehicleModelId);

CREATE TABLE ProgramEnrollment (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  IncentiveProgramId INTEGER NOT NULL,
  ProviderId INTEGER NOT NULL,
  ValidFrom TEXT NOT NULL CHECK (ValidFrom IS NULL OR length(trim(ValidFrom)) > 0) CHECK (ValidFrom IS NULL OR (length(ValidFrom)=10 AND date(ValidFrom, '+0 days') IS NOT NULL AND date(ValidFrom, '+0 days')=ValidFrom)),
  ValidTo TEXT CHECK (ValidTo IS NULL OR length(trim(ValidTo)) > 0) CHECK (ValidTo IS NULL OR (length(ValidTo)=10 AND date(ValidTo, '+0 days') IS NOT NULL AND date(ValidTo, '+0 days')=ValidTo)),
  EnrollmentStatus TEXT NOT NULL CHECK (EnrollmentStatus IS NULL OR length(trim(EnrollmentStatus)) > 0),
  CONSTRAINT UK_ProgramEnrollment_BusinessKey UNIQUE (IncentiveProgramId, ProviderId, ValidFrom),
  CONSTRAINT FK_ProgramEnrollment_IncentiveProgramId_2_IncentiveProgram_Id FOREIGN KEY (IncentiveProgramId) REFERENCES IncentiveProgram(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_ProgramEnrollment_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((ValidTo IS NULL OR ValidTo > ValidFrom))
);

CREATE INDEX IX_ProgramEnrollment_IncentiveProgramId ON ProgramEnrollment(IncentiveProgramId);

CREATE INDEX IX_ProgramEnrollment_ProviderId ON ProgramEnrollment(ProviderId);

CREATE TABLE PerformanceMeasurement (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ProviderId INTEGER NOT NULL,
  MetricDefinitionVersionId INTEGER NOT NULL,
  PeriodStart TEXT NOT NULL CHECK (PeriodStart IS NULL OR length(trim(PeriodStart)) > 0) CHECK (PeriodStart IS NULL OR (length(PeriodStart)=10 AND date(PeriodStart, '+0 days') IS NOT NULL AND date(PeriodStart, '+0 days')=PeriodStart)),
  PeriodEnd TEXT NOT NULL CHECK (PeriodEnd IS NULL OR length(trim(PeriodEnd)) > 0) CHECK (PeriodEnd IS NULL OR (length(PeriodEnd)=10 AND date(PeriodEnd, '+0 days') IS NOT NULL AND date(PeriodEnd, '+0 days')=PeriodEnd)),
  MeasuredValue NUMERIC NOT NULL,
  CalculatedAt TEXT NOT NULL CHECK (CalculatedAt IS NULL OR length(trim(CalculatedAt)) > 0) CHECK (CalculatedAt IS NULL OR (length(CalculatedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',CalculatedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',CalculatedAt, '+0 days')=CalculatedAt)),
  CONSTRAINT UK_PerformanceMeasurement_BusinessKey UNIQUE (ProviderId, MetricDefinitionVersionId, PeriodStart, PeriodEnd),
  CONSTRAINT FK_PerformanceMeasurement_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PerformanceMeasurement_MetricDefinitionVersionId_2_MetricDefinitionVersion_Id FOREIGN KEY (MetricDefinitionVersionId) REFERENCES MetricDefinitionVersion(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((PeriodEnd IS NULL OR PeriodEnd > PeriodStart))
);

CREATE INDEX IX_PerformanceMeasurement_ProviderId ON PerformanceMeasurement(ProviderId);

CREATE INDEX IX_PerformanceMeasurement_MetricDefinitionVersionId ON PerformanceMeasurement(MetricDefinitionVersionId);

CREATE TABLE EventAwardComponent (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  EventAwardId INTEGER NOT NULL,
  RewardType TEXT NOT NULL CHECK (RewardType IS NULL OR length(trim(RewardType)) > 0),
  UnitScheme TEXT NOT NULL CHECK (UnitScheme IS NULL OR length(trim(UnitScheme)) > 0),
  UnitCode TEXT NOT NULL CHECK (UnitCode IS NULL OR length(trim(UnitCode)) > 0),
  BenefitValue NUMERIC NOT NULL,
  Currency TEXT CHECK (Currency IS NULL OR length(trim(Currency)) > 0),
  ValidFrom TEXT NOT NULL CHECK (ValidFrom IS NULL OR length(trim(ValidFrom)) > 0) CHECK (ValidFrom IS NULL OR (length(ValidFrom)=10 AND date(ValidFrom, '+0 days') IS NOT NULL AND date(ValidFrom, '+0 days')=ValidFrom)),
  ValidTo TEXT CHECK (ValidTo IS NULL OR length(trim(ValidTo)) > 0) CHECK (ValidTo IS NULL OR (length(ValidTo)=10 AND date(ValidTo, '+0 days') IS NOT NULL AND date(ValidTo, '+0 days')=ValidTo)),
  CONSTRAINT UK_EventAwardComponent_BusinessKey UNIQUE (EventAwardId, RewardType, UnitScheme, UnitCode),
  CONSTRAINT UK_EventAwardComponent_0 UNIQUE (Id, EventAwardId),
  CONSTRAINT FK_EventAwardComponent_EventAwardId_2_EventAward_Id FOREIGN KEY (EventAwardId) REFERENCES EventAward(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((ValidTo IS NULL OR ValidTo > ValidFrom)),
  CHECK (BenefitValue >= 0),
  CHECK ((Currency IS NULL OR (length(Currency)=3 AND Currency NOT GLOB '*[^A-Z]*'))),
  CHECK ((RewardType != 'Cash' OR (Currency IS NOT NULL AND UnitScheme='ISO4217' AND UnitCode=Currency))),
  CHECK ((RewardType != 'Points' OR Currency IS NULL))
);

CREATE INDEX IX_EventAwardComponent_EventAwardId ON EventAwardComponent(EventAwardId);

CREATE TABLE Outlet (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ProviderId INTEGER NOT NULL,
  ExistingOutletReference TEXT NOT NULL CHECK (ExistingOutletReference IS NULL OR length(trim(ExistingOutletReference)) > 0),
  OutletName TEXT NOT NULL CHECK (OutletName IS NULL OR length(trim(OutletName)) > 0),
  Address TEXT NOT NULL CHECK (Address IS NULL OR length(trim(Address)) > 0),
  CONSTRAINT UK_Outlet_BusinessKey UNIQUE (ProviderId, ExistingOutletReference),
  CONSTRAINT FK_Outlet_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_Outlet_ProviderId ON Outlet(ProviderId);

CREATE TABLE CustomerIdentityLink (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  AccountAId INTEGER NOT NULL,
  AccountBId INTEGER NOT NULL,
  VerificationStatus TEXT NOT NULL CHECK (VerificationStatus IS NULL OR length(trim(VerificationStatus)) > 0),
  VerificationMethod TEXT NOT NULL CHECK (VerificationMethod IS NULL OR length(trim(VerificationMethod)) > 0),
  VerifiedAt TEXT CHECK (VerifiedAt IS NULL OR length(trim(VerifiedAt)) > 0) CHECK (VerifiedAt IS NULL OR (length(VerifiedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',VerifiedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',VerifiedAt, '+0 days')=VerifiedAt)),
  RevokedAt TEXT CHECK (RevokedAt IS NULL OR length(trim(RevokedAt)) > 0) CHECK (RevokedAt IS NULL OR (length(RevokedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',RevokedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',RevokedAt, '+0 days')=RevokedAt)),
  EvidenceReference TEXT NOT NULL CHECK (EvidenceReference IS NULL OR length(trim(EvidenceReference)) > 0),
  CONSTRAINT UK_CustomerIdentityLink_BusinessKey UNIQUE (AccountAId, AccountBId),
  CONSTRAINT FK_CustomerIdentityLink_AccountAId_2_CustomerAccount_Id FOREIGN KEY (AccountAId) REFERENCES CustomerAccount(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_CustomerIdentityLink_AccountBId_2_CustomerAccount_Id FOREIGN KEY (AccountBId) REFERENCES CustomerAccount(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK (AccountAId < AccountBId),
  CHECK (VerificationStatus IN ('Pending','Verified','Revoked','Rejected')),
  CHECK ((VerificationStatus != 'Verified' OR (VerifiedAt IS NOT NULL AND RevokedAt IS NULL)))
);

CREATE INDEX IX_CustomerIdentityLink_AccountAId ON CustomerIdentityLink(AccountAId);

CREATE INDEX IX_CustomerIdentityLink_AccountBId ON CustomerIdentityLink(AccountBId);

CREATE TABLE VehicleActivity (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  IssuingOutletId INTEGER NOT NULL,
  SourceNamespace TEXT NOT NULL CHECK (SourceNamespace IS NULL OR length(trim(SourceNamespace)) > 0),
  ActivityKind TEXT NOT NULL CHECK (ActivityKind IS NULL OR length(trim(ActivityKind)) > 0),
  OfficialActivityReference TEXT NOT NULL CHECK (OfficialActivityReference IS NULL OR length(trim(OfficialActivityReference)) > 0),
  ActivityStatus TEXT NOT NULL CHECK (ActivityStatus IS NULL OR length(trim(ActivityStatus)) > 0),
  StartedAt TEXT NOT NULL CHECK (StartedAt IS NULL OR length(trim(StartedAt)) > 0) CHECK (StartedAt IS NULL OR (length(StartedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',StartedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',StartedAt, '+0 days')=StartedAt)),
  EndedAt TEXT CHECK (EndedAt IS NULL OR length(trim(EndedAt)) > 0) CHECK (EndedAt IS NULL OR (length(EndedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',EndedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',EndedAt, '+0 days')=EndedAt)),
  RecordedAt TEXT NOT NULL CHECK (RecordedAt IS NULL OR length(trim(RecordedAt)) > 0) CHECK (RecordedAt IS NULL OR (length(RecordedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',RecordedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',RecordedAt, '+0 days')=RecordedAt)),
  CustomerAccountId INTEGER NOT NULL,
  VehicleId INTEGER NOT NULL,
  SaleId INTEGER,
  RentalId INTEGER,
  ServiceId INTEGER,
  CONSTRAINT UK_VehicleActivity_BusinessKey UNIQUE (IssuingOutletId, SourceNamespace, ActivityKind, OfficialActivityReference),
  CONSTRAINT UK_VehicleActivity_0 UNIQUE (Id, SaleId),
  CONSTRAINT UK_VehicleActivity_1 UNIQUE (Id, RentalId),
  CONSTRAINT UK_VehicleActivity_2 UNIQUE (Id, ServiceId),
  CONSTRAINT FK_VehicleActivity_IssuingOutletId_2_Outlet_Id FOREIGN KEY (IssuingOutletId) REFERENCES Outlet(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_VehicleActivity_CustomerAccountId_2_CustomerAccount_Id FOREIGN KEY (CustomerAccountId) REFERENCES CustomerAccount(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_VehicleActivity_VehicleId_2_Vehicle_Id FOREIGN KEY (VehicleId) REFERENCES Vehicle(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_VehicleActivity_SaleId_2_Sale_Id FOREIGN KEY (SaleId, Id) REFERENCES Sale(Id,VehicleActivityId) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_VehicleActivity_RentalId_2_Rental_Id FOREIGN KEY (RentalId, Id) REFERENCES Rental(Id,VehicleActivityId) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_VehicleActivity_ServiceId_2_Service_Id FOREIGN KEY (ServiceId, Id) REFERENCES Service(Id,VehicleActivityId) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((EndedAt IS NULL OR EndedAt > StartedAt)),
  CHECK (ActivityKind IN ('Sale','Rental','Service')),
  CHECK ((ActivityKind='Sale' AND SaleId IS NOT NULL AND RentalId IS NULL AND ServiceId IS NULL) OR (ActivityKind='Rental' AND RentalId IS NOT NULL AND SaleId IS NULL AND ServiceId IS NULL) OR (ActivityKind='Service' AND ServiceId IS NOT NULL AND SaleId IS NULL AND RentalId IS NULL))
);

CREATE INDEX IX_VehicleActivity_IssuingOutletId ON VehicleActivity(IssuingOutletId);

CREATE INDEX IX_VehicleActivity_CustomerAccountId ON VehicleActivity(CustomerAccountId);

CREATE INDEX IX_VehicleActivity_VehicleId ON VehicleActivity(VehicleId);

CREATE INDEX IX_VehicleActivity_SaleId ON VehicleActivity(SaleId);

CREATE INDEX IX_VehicleActivity_RentalId ON VehicleActivity(RentalId);

CREATE INDEX IX_VehicleActivity_ServiceId ON VehicleActivity(ServiceId);

CREATE TABLE IncentiveRule (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  IncentiveProgramId INTEGER NOT NULL,
  OfficialRuleCode TEXT NOT NULL CHECK (OfficialRuleCode IS NULL OR length(trim(OfficialRuleCode)) > 0),
  RuleName TEXT NOT NULL CHECK (RuleName IS NULL OR length(trim(RuleName)) > 0),
  AssessmentBasis TEXT NOT NULL CHECK (AssessmentBasis IS NULL OR length(trim(AssessmentBasis)) > 0),
  CONSTRAINT UK_IncentiveRule_BusinessKey UNIQUE (IncentiveProgramId, OfficialRuleCode),
  CONSTRAINT FK_IncentiveRule_IncentiveProgramId_2_IncentiveProgram_Id FOREIGN KEY (IncentiveProgramId) REFERENCES IncentiveProgram(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK (AssessmentBasis IN ('Event','Period'))
);

CREATE INDEX IX_IncentiveRule_IncentiveProgramId ON IncentiveRule(IncentiveProgramId);

CREATE TABLE EventEvaluation (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  VehicleActivityId INTEGER NOT NULL,
  RuleVersionId INTEGER NOT NULL,
  Result TEXT NOT NULL CHECK (Result IS NULL OR length(trim(Result)) > 0),
  Reason TEXT NOT NULL CHECK (Reason IS NULL OR length(trim(Reason)) > 0),
  QualificationDate TEXT NOT NULL CHECK (QualificationDate IS NULL OR length(trim(QualificationDate)) > 0) CHECK (QualificationDate IS NULL OR (length(QualificationDate)=10 AND date(QualificationDate, '+0 days') IS NOT NULL AND date(QualificationDate, '+0 days')=QualificationDate)),
  EvaluatedAt TEXT NOT NULL CHECK (EvaluatedAt IS NULL OR length(trim(EvaluatedAt)) > 0) CHECK (EvaluatedAt IS NULL OR (length(EvaluatedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',EvaluatedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',EvaluatedAt, '+0 days')=EvaluatedAt)),
  DecisionEvidenceReference TEXT NOT NULL CHECK (DecisionEvidenceReference IS NULL OR length(trim(DecisionEvidenceReference)) > 0),
  CONSTRAINT UK_EventEvaluation_BusinessKey UNIQUE (VehicleActivityId, RuleVersionId),
  CONSTRAINT FK_EventEvaluation_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId) REFERENCES VehicleActivity(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventEvaluation_RuleVersionId_2_RuleVersion_Id FOREIGN KEY (RuleVersionId) REFERENCES RuleVersion(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK (Result IN ('Qualified','Rejected'))
);

CREATE INDEX IX_EventEvaluation_VehicleActivityId ON EventEvaluation(VehicleActivityId);

CREATE INDEX IX_EventEvaluation_RuleVersionId ON EventEvaluation(RuleVersionId);

CREATE TABLE EventAward (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  VehicleActivityId INTEGER NOT NULL,
  IncentiveRuleId INTEGER NOT NULL,
  AwardStatus TEXT NOT NULL CHECK (AwardStatus IS NULL OR length(trim(AwardStatus)) > 0),
  IssuedAt TEXT NOT NULL CHECK (IssuedAt IS NULL OR length(trim(IssuedAt)) > 0) CHECK (IssuedAt IS NULL OR (length(IssuedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',IssuedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',IssuedAt, '+0 days')=IssuedAt)),
  AcceptedEvaluationId INTEGER NOT NULL,
  FirstComponentId INTEGER NOT NULL,
  CONSTRAINT UK_EventAward_BusinessKey UNIQUE (VehicleActivityId, IncentiveRuleId),
  CONSTRAINT UK_EventAward_0 UNIQUE (AcceptedEvaluationId),
  CONSTRAINT FK_EventAward_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId) REFERENCES VehicleActivity(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventAward_IncentiveRuleId_2_IncentiveRule_Id FOREIGN KEY (IncentiveRuleId) REFERENCES IncentiveRule(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventAward_AcceptedEvaluationId_2_EventEvaluation_Id FOREIGN KEY (AcceptedEvaluationId) REFERENCES EventEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventAward_FirstComponentId_2_EventAwardComponent_Id FOREIGN KEY (FirstComponentId, Id) REFERENCES EventAwardComponent(Id,EventAwardId) DEFERRABLE INITIALLY DEFERRED,
  CHECK (AwardStatus IN ('Issued','Cancelled'))
);

CREATE INDEX IX_EventAward_VehicleActivityId ON EventAward(VehicleActivityId);

CREATE INDEX IX_EventAward_IncentiveRuleId ON EventAward(IncentiveRuleId);

CREATE INDEX IX_EventAward_AcceptedEvaluationId ON EventAward(AcceptedEvaluationId);

CREATE INDEX IX_EventAward_FirstComponentId ON EventAward(FirstComponentId);

CREATE TABLE Capability (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ExistingCapabilityDesignation TEXT NOT NULL CHECK (ExistingCapabilityDesignation IS NULL OR length(trim(ExistingCapabilityDesignation)) > 0),
  Description TEXT NOT NULL CHECK (Description IS NULL OR length(trim(Description)) > 0),
  CONSTRAINT UK_Capability_BusinessKey UNIQUE (ExistingCapabilityDesignation)
);

CREATE TABLE CapabilityAuthorization (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ProviderAuthorizationId INTEGER NOT NULL,
  OutletId INTEGER NOT NULL,
  CapabilityId INTEGER NOT NULL,
  ValidFrom TEXT NOT NULL CHECK (ValidFrom IS NULL OR length(trim(ValidFrom)) > 0) CHECK (ValidFrom IS NULL OR (length(ValidFrom)=10 AND date(ValidFrom, '+0 days') IS NOT NULL AND date(ValidFrom, '+0 days')=ValidFrom)),
  ValidTo TEXT CHECK (ValidTo IS NULL OR length(trim(ValidTo)) > 0) CHECK (ValidTo IS NULL OR (length(ValidTo)=10 AND date(ValidTo, '+0 days') IS NOT NULL AND date(ValidTo, '+0 days')=ValidTo)),
  AuthorizationStatus TEXT NOT NULL CHECK (AuthorizationStatus IS NULL OR length(trim(AuthorizationStatus)) > 0),
  CONSTRAINT UK_CapabilityAuthorization_BusinessKey UNIQUE (ProviderAuthorizationId, OutletId, CapabilityId, ValidFrom),
  CONSTRAINT FK_CapabilityAuthorization_ProviderAuthorizationId_2_ProviderAuthorization_Id FOREIGN KEY (ProviderAuthorizationId) REFERENCES ProviderAuthorization(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_CapabilityAuthorization_OutletId_2_Outlet_Id FOREIGN KEY (OutletId) REFERENCES Outlet(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_CapabilityAuthorization_CapabilityId_2_Capability_Id FOREIGN KEY (CapabilityId) REFERENCES Capability(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((ValidTo IS NULL OR ValidTo > ValidFrom))
);

CREATE INDEX IX_CapabilityAuthorization_ProviderAuthorizationId ON CapabilityAuthorization(ProviderAuthorizationId);

CREATE INDEX IX_CapabilityAuthorization_OutletId ON CapabilityAuthorization(OutletId);

CREATE INDEX IX_CapabilityAuthorization_CapabilityId ON CapabilityAuthorization(CapabilityId);

CREATE TABLE RuleVersion (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  IncentiveRuleId INTEGER NOT NULL,
  EffectiveFrom TEXT NOT NULL CHECK (EffectiveFrom IS NULL OR length(trim(EffectiveFrom)) > 0) CHECK (EffectiveFrom IS NULL OR (length(EffectiveFrom)=10 AND date(EffectiveFrom, '+0 days') IS NOT NULL AND date(EffectiveFrom, '+0 days')=EffectiveFrom)),
  EffectiveTo TEXT CHECK (EffectiveTo IS NULL OR length(trim(EffectiveTo)) > 0) CHECK (EffectiveTo IS NULL OR (length(EffectiveTo)=10 AND date(EffectiveTo, '+0 days') IS NOT NULL AND date(EffectiveTo, '+0 days')=EffectiveTo)),
  ConditionExpression TEXT NOT NULL CHECK (ConditionExpression IS NULL OR length(trim(ConditionExpression)) > 0),
  RewardSpecification TEXT NOT NULL CHECK (RewardSpecification IS NULL OR length(trim(RewardSpecification)) > 0),
  CONSTRAINT UK_RuleVersion_BusinessKey UNIQUE (IncentiveRuleId, EffectiveFrom),
  CONSTRAINT FK_RuleVersion_IncentiveRuleId_2_IncentiveRule_Id FOREIGN KEY (IncentiveRuleId) REFERENCES IncentiveRule(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((EffectiveTo IS NULL OR EffectiveTo > EffectiveFrom))
);

CREATE INDEX IX_RuleVersion_IncentiveRuleId ON RuleVersion(IncentiveRuleId);

CREATE TABLE PeriodEvaluation (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ProviderId INTEGER NOT NULL,
  RuleVersionId INTEGER NOT NULL,
  PeriodStart TEXT NOT NULL CHECK (PeriodStart IS NULL OR length(trim(PeriodStart)) > 0) CHECK (PeriodStart IS NULL OR (length(PeriodStart)=10 AND date(PeriodStart, '+0 days') IS NOT NULL AND date(PeriodStart, '+0 days')=PeriodStart)),
  PeriodEnd TEXT NOT NULL CHECK (PeriodEnd IS NULL OR length(trim(PeriodEnd)) > 0) CHECK (PeriodEnd IS NULL OR (length(PeriodEnd)=10 AND date(PeriodEnd, '+0 days') IS NOT NULL AND date(PeriodEnd, '+0 days')=PeriodEnd)),
  Result TEXT NOT NULL CHECK (Result IS NULL OR length(trim(Result)) > 0),
  Reason TEXT NOT NULL CHECK (Reason IS NULL OR length(trim(Reason)) > 0),
  QualificationDate TEXT NOT NULL CHECK (QualificationDate IS NULL OR length(trim(QualificationDate)) > 0) CHECK (QualificationDate IS NULL OR (length(QualificationDate)=10 AND date(QualificationDate, '+0 days') IS NOT NULL AND date(QualificationDate, '+0 days')=QualificationDate)),
  EvaluatedAt TEXT NOT NULL CHECK (EvaluatedAt IS NULL OR length(trim(EvaluatedAt)) > 0) CHECK (EvaluatedAt IS NULL OR (length(EvaluatedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',EvaluatedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',EvaluatedAt, '+0 days')=EvaluatedAt)),
  DecisionEvidenceReference TEXT NOT NULL CHECK (DecisionEvidenceReference IS NULL OR length(trim(DecisionEvidenceReference)) > 0),
  CONSTRAINT UK_PeriodEvaluation_BusinessKey UNIQUE (ProviderId, RuleVersionId, PeriodStart, PeriodEnd),
  CONSTRAINT FK_PeriodEvaluation_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodEvaluation_RuleVersionId_2_RuleVersion_Id FOREIGN KEY (RuleVersionId) REFERENCES RuleVersion(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((PeriodEnd IS NULL OR PeriodEnd > PeriodStart)),
  CHECK (Result IN ('Qualified','Rejected'))
);

CREATE INDEX IX_PeriodEvaluation_ProviderId ON PeriodEvaluation(ProviderId);

CREATE INDEX IX_PeriodEvaluation_RuleVersionId ON PeriodEvaluation(RuleVersionId);

CREATE TABLE PeriodAward (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  ProviderId INTEGER NOT NULL,
  IncentiveRuleId INTEGER NOT NULL,
  PeriodStart TEXT NOT NULL CHECK (PeriodStart IS NULL OR length(trim(PeriodStart)) > 0) CHECK (PeriodStart IS NULL OR (length(PeriodStart)=10 AND date(PeriodStart, '+0 days') IS NOT NULL AND date(PeriodStart, '+0 days')=PeriodStart)),
  PeriodEnd TEXT NOT NULL CHECK (PeriodEnd IS NULL OR length(trim(PeriodEnd)) > 0) CHECK (PeriodEnd IS NULL OR (length(PeriodEnd)=10 AND date(PeriodEnd, '+0 days') IS NOT NULL AND date(PeriodEnd, '+0 days')=PeriodEnd)),
  AwardStatus TEXT NOT NULL CHECK (AwardStatus IS NULL OR length(trim(AwardStatus)) > 0),
  IssuedAt TEXT NOT NULL CHECK (IssuedAt IS NULL OR length(trim(IssuedAt)) > 0) CHECK (IssuedAt IS NULL OR (length(IssuedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',IssuedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',IssuedAt, '+0 days')=IssuedAt)),
  AcceptedEvaluationId INTEGER NOT NULL,
  FirstComponentId INTEGER NOT NULL,
  CONSTRAINT UK_PeriodAward_BusinessKey UNIQUE (ProviderId, IncentiveRuleId, PeriodStart, PeriodEnd),
  CONSTRAINT UK_PeriodAward_0 UNIQUE (AcceptedEvaluationId),
  CONSTRAINT FK_PeriodAward_ProviderId_2_Provider_Id FOREIGN KEY (ProviderId) REFERENCES Provider(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodAward_IncentiveRuleId_2_IncentiveRule_Id FOREIGN KEY (IncentiveRuleId) REFERENCES IncentiveRule(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodAward_AcceptedEvaluationId_2_PeriodEvaluation_Id FOREIGN KEY (AcceptedEvaluationId) REFERENCES PeriodEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodAward_FirstComponentId_2_PeriodAwardComponent_Id FOREIGN KEY (FirstComponentId, Id) REFERENCES PeriodAwardComponent(Id,PeriodAwardId) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((PeriodEnd IS NULL OR PeriodEnd > PeriodStart)),
  CHECK (AwardStatus IN ('Issued','Cancelled'))
);

CREATE INDEX IX_PeriodAward_ProviderId ON PeriodAward(ProviderId);

CREATE INDEX IX_PeriodAward_IncentiveRuleId ON PeriodAward(IncentiveRuleId);

CREATE INDEX IX_PeriodAward_AcceptedEvaluationId ON PeriodAward(AcceptedEvaluationId);

CREATE INDEX IX_PeriodAward_FirstComponentId ON PeriodAward(FirstComponentId);

CREATE TABLE Rental (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  VehicleActivityId INTEGER NOT NULL,
  RentalCharge NUMERIC NOT NULL,
  Currency TEXT NOT NULL CHECK (Currency IS NULL OR length(trim(Currency)) > 0),
  ReturnedAt TEXT CHECK (ReturnedAt IS NULL OR length(trim(ReturnedAt)) > 0) CHECK (ReturnedAt IS NULL OR (length(ReturnedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',ReturnedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',ReturnedAt, '+0 days')=ReturnedAt)),
  ReplacementForServiceId INTEGER,
  ReplacementPurpose TEXT CHECK (ReplacementPurpose IS NULL OR length(trim(ReplacementPurpose)) > 0),
  CONSTRAINT UK_Rental_BusinessKey UNIQUE (VehicleActivityId),
  CONSTRAINT UK_Rental_0 UNIQUE (Id, VehicleActivityId),
  CONSTRAINT FK_Rental_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId,Id) REFERENCES VehicleActivity(Id,RentalId) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_Rental_ReplacementForServiceId_2_Service_Id FOREIGN KEY (ReplacementForServiceId) REFERENCES Service(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK (RentalCharge >= 0),
  CHECK ((Currency IS NULL OR (length(Currency)=3 AND Currency NOT GLOB '*[^A-Z]*'))),
  CHECK ((ReplacementForServiceId IS NULL AND ReplacementPurpose IS NULL) OR (ReplacementForServiceId IS NOT NULL AND ReplacementPurpose IS NOT NULL))
);

CREATE INDEX IX_Rental_VehicleActivityId ON Rental(VehicleActivityId);

CREATE INDEX IX_Rental_ReplacementForServiceId ON Rental(ReplacementForServiceId);

CREATE TABLE Sale (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  VehicleActivityId INTEGER NOT NULL,
  SalePrice NUMERIC NOT NULL,
  Currency TEXT NOT NULL CHECK (Currency IS NULL OR length(trim(Currency)) > 0),
  CompletedAt TEXT NOT NULL CHECK (CompletedAt IS NULL OR length(trim(CompletedAt)) > 0) CHECK (CompletedAt IS NULL OR (length(CompletedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',CompletedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',CompletedAt, '+0 days')=CompletedAt)),
  CONSTRAINT UK_Sale_BusinessKey UNIQUE (VehicleActivityId),
  CONSTRAINT UK_Sale_0 UNIQUE (Id, VehicleActivityId),
  CONSTRAINT FK_Sale_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId,Id) REFERENCES VehicleActivity(Id,SaleId) DEFERRABLE INITIALLY DEFERRED,
  CHECK (SalePrice >= 0),
  CHECK ((Currency IS NULL OR (length(Currency)=3 AND Currency NOT GLOB '*[^A-Z]*')))
);

CREATE INDEX IX_Sale_VehicleActivityId ON Sale(VehicleActivityId);

CREATE TABLE Service (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  VehicleActivityId INTEGER NOT NULL,
  ServiceType TEXT NOT NULL CHECK (ServiceType IS NULL OR length(trim(ServiceType)) > 0),
  Outcome TEXT NOT NULL CHECK (Outcome IS NULL OR length(trim(Outcome)) > 0),
  CompletedAt TEXT NOT NULL CHECK (CompletedAt IS NULL OR length(trim(CompletedAt)) > 0) CHECK (CompletedAt IS NULL OR (length(CompletedAt)=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',CompletedAt, '+0 days') IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',CompletedAt, '+0 days')=CompletedAt)),
  CONSTRAINT UK_Service_BusinessKey UNIQUE (VehicleActivityId),
  CONSTRAINT UK_Service_0 UNIQUE (Id, VehicleActivityId),
  CONSTRAINT FK_Service_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId,Id) REFERENCES VehicleActivity(Id,ServiceId) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_Service_VehicleActivityId ON Service(VehicleActivityId);

CREATE TABLE PeriodAwardComponent (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  PeriodAwardId INTEGER NOT NULL,
  RewardType TEXT NOT NULL CHECK (RewardType IS NULL OR length(trim(RewardType)) > 0),
  UnitScheme TEXT NOT NULL CHECK (UnitScheme IS NULL OR length(trim(UnitScheme)) > 0),
  UnitCode TEXT NOT NULL CHECK (UnitCode IS NULL OR length(trim(UnitCode)) > 0),
  BenefitValue NUMERIC NOT NULL,
  Currency TEXT CHECK (Currency IS NULL OR length(trim(Currency)) > 0),
  ValidFrom TEXT NOT NULL CHECK (ValidFrom IS NULL OR length(trim(ValidFrom)) > 0) CHECK (ValidFrom IS NULL OR (length(ValidFrom)=10 AND date(ValidFrom, '+0 days') IS NOT NULL AND date(ValidFrom, '+0 days')=ValidFrom)),
  ValidTo TEXT CHECK (ValidTo IS NULL OR length(trim(ValidTo)) > 0) CHECK (ValidTo IS NULL OR (length(ValidTo)=10 AND date(ValidTo, '+0 days') IS NOT NULL AND date(ValidTo, '+0 days')=ValidTo)),
  CONSTRAINT UK_PeriodAwardComponent_BusinessKey UNIQUE (PeriodAwardId, RewardType, UnitScheme, UnitCode),
  CONSTRAINT UK_PeriodAwardComponent_0 UNIQUE (Id, PeriodAwardId),
  CONSTRAINT FK_PeriodAwardComponent_PeriodAwardId_2_PeriodAward_Id FOREIGN KEY (PeriodAwardId) REFERENCES PeriodAward(Id) DEFERRABLE INITIALLY DEFERRED,
  CHECK ((ValidTo IS NULL OR ValidTo > ValidFrom)),
  CHECK (BenefitValue >= 0),
  CHECK ((Currency IS NULL OR (length(Currency)=3 AND Currency NOT GLOB '*[^A-Z]*'))),
  CHECK ((RewardType != 'Cash' OR (Currency IS NOT NULL AND UnitScheme='ISO4217' AND UnitCode=Currency))),
  CHECK ((RewardType != 'Points' OR Currency IS NULL))
);

CREATE INDEX IX_PeriodAwardComponent_PeriodAwardId ON PeriodAwardComponent(PeriodAwardId);

CREATE TABLE MeasurementContribution (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  PerformanceMeasurementId INTEGER NOT NULL,
  VehicleActivityId INTEGER NOT NULL,
  ContributionRole TEXT NOT NULL CHECK (ContributionRole IS NULL OR length(trim(ContributionRole)) > 0),
  CONSTRAINT UK_MeasurementContribution_BusinessKey UNIQUE (PerformanceMeasurementId, VehicleActivityId),
  CONSTRAINT FK_MeasurementContribution_PerformanceMeasurementId_2_PerformanceMeasurement_Id FOREIGN KEY (PerformanceMeasurementId) REFERENCES PerformanceMeasurement(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_MeasurementContribution_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId) REFERENCES VehicleActivity(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_MeasurementContribution_PerformanceMeasurementId ON MeasurementContribution(PerformanceMeasurementId);

CREATE INDEX IX_MeasurementContribution_VehicleActivityId ON MeasurementContribution(VehicleActivityId);

CREATE TABLE RuleMetric (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  RuleVersionId INTEGER NOT NULL,
  MetricDefinitionVersionId INTEGER NOT NULL,
  MetricRole TEXT NOT NULL CHECK (MetricRole IS NULL OR length(trim(MetricRole)) > 0),
  CONSTRAINT UK_RuleMetric_BusinessKey UNIQUE (RuleVersionId, MetricDefinitionVersionId),
  CONSTRAINT FK_RuleMetric_RuleVersionId_2_RuleVersion_Id FOREIGN KEY (RuleVersionId) REFERENCES RuleVersion(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_RuleMetric_MetricDefinitionVersionId_2_MetricDefinitionVersion_Id FOREIGN KEY (MetricDefinitionVersionId) REFERENCES MetricDefinitionVersion(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_RuleMetric_RuleVersionId ON RuleMetric(RuleVersionId);

CREATE INDEX IX_RuleMetric_MetricDefinitionVersionId ON RuleMetric(MetricDefinitionVersionId);

CREATE TABLE EventEvaluationMeasurement (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  EventEvaluationId INTEGER NOT NULL,
  PerformanceMeasurementId INTEGER NOT NULL,
  EvidenceRole TEXT NOT NULL CHECK (EvidenceRole IS NULL OR length(trim(EvidenceRole)) > 0),
  CONSTRAINT UK_EventEvaluationMeasurement_BusinessKey UNIQUE (EventEvaluationId, PerformanceMeasurementId),
  CONSTRAINT FK_EventEvaluationMeasurement_EventEvaluationId_2_EventEvaluation_Id FOREIGN KEY (EventEvaluationId) REFERENCES EventEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventEvaluationMeasurement_PerformanceMeasurementId_2_PerformanceMeasurement_Id FOREIGN KEY (PerformanceMeasurementId) REFERENCES PerformanceMeasurement(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_EventEvaluationMeasurement_EventEvaluationId ON EventEvaluationMeasurement(EventEvaluationId);

CREATE INDEX IX_EventEvaluationMeasurement_PerformanceMeasurementId ON EventEvaluationMeasurement(PerformanceMeasurementId);

CREATE TABLE EventEvaluationActivity (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  EventEvaluationId INTEGER NOT NULL,
  VehicleActivityId INTEGER NOT NULL,
  EvidenceRole TEXT NOT NULL CHECK (EvidenceRole IS NULL OR length(trim(EvidenceRole)) > 0),
  CONSTRAINT UK_EventEvaluationActivity_BusinessKey UNIQUE (EventEvaluationId, VehicleActivityId),
  CONSTRAINT FK_EventEvaluationActivity_EventEvaluationId_2_EventEvaluation_Id FOREIGN KEY (EventEvaluationId) REFERENCES EventEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventEvaluationActivity_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId) REFERENCES VehicleActivity(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_EventEvaluationActivity_EventEvaluationId ON EventEvaluationActivity(EventEvaluationId);

CREATE INDEX IX_EventEvaluationActivity_VehicleActivityId ON EventEvaluationActivity(VehicleActivityId);

CREATE TABLE EventEvaluationIdentity (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  EventEvaluationId INTEGER NOT NULL,
  CustomerIdentityLinkId INTEGER NOT NULL,
  VerificationOutcomeUsed TEXT NOT NULL CHECK (VerificationOutcomeUsed IS NULL OR length(trim(VerificationOutcomeUsed)) > 0),
  VerifiedAtUsed TEXT NOT NULL CHECK (VerifiedAtUsed IS NULL OR length(trim(VerifiedAtUsed)) > 0),
  EvidenceReferenceUsed TEXT NOT NULL CHECK (EvidenceReferenceUsed IS NULL OR length(trim(EvidenceReferenceUsed)) > 0),
  CONSTRAINT UK_EventEvaluationIdentity_BusinessKey UNIQUE (EventEvaluationId, CustomerIdentityLinkId),
  CONSTRAINT FK_EventEvaluationIdentity_EventEvaluationId_2_EventEvaluation_Id FOREIGN KEY (EventEvaluationId) REFERENCES EventEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_EventEvaluationIdentity_CustomerIdentityLinkId_2_CustomerIdentityLink_Id FOREIGN KEY (CustomerIdentityLinkId) REFERENCES CustomerIdentityLink(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_EventEvaluationIdentity_EventEvaluationId ON EventEvaluationIdentity(EventEvaluationId);

CREATE INDEX IX_EventEvaluationIdentity_CustomerIdentityLinkId ON EventEvaluationIdentity(CustomerIdentityLinkId);

CREATE TABLE PeriodEvaluationMeasurement (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  PeriodEvaluationId INTEGER NOT NULL,
  PerformanceMeasurementId INTEGER NOT NULL,
  EvidenceRole TEXT NOT NULL CHECK (EvidenceRole IS NULL OR length(trim(EvidenceRole)) > 0),
  CONSTRAINT UK_PeriodEvaluationMeasurement_BusinessKey UNIQUE (PeriodEvaluationId, PerformanceMeasurementId),
  CONSTRAINT FK_PeriodEvaluationMeasurement_PeriodEvaluationId_2_PeriodEvaluation_Id FOREIGN KEY (PeriodEvaluationId) REFERENCES PeriodEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodEvaluationMeasurement_PerformanceMeasurementId_2_PerformanceMeasurement_Id FOREIGN KEY (PerformanceMeasurementId) REFERENCES PerformanceMeasurement(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_PeriodEvaluationMeasurement_PeriodEvaluationId ON PeriodEvaluationMeasurement(PeriodEvaluationId);

CREATE INDEX IX_PeriodEvaluationMeasurement_PerformanceMeasurementId ON PeriodEvaluationMeasurement(PerformanceMeasurementId);

CREATE TABLE PeriodEvaluationActivity (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  PeriodEvaluationId INTEGER NOT NULL,
  VehicleActivityId INTEGER NOT NULL,
  EvidenceRole TEXT NOT NULL CHECK (EvidenceRole IS NULL OR length(trim(EvidenceRole)) > 0),
  CONSTRAINT UK_PeriodEvaluationActivity_BusinessKey UNIQUE (PeriodEvaluationId, VehicleActivityId),
  CONSTRAINT FK_PeriodEvaluationActivity_PeriodEvaluationId_2_PeriodEvaluation_Id FOREIGN KEY (PeriodEvaluationId) REFERENCES PeriodEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodEvaluationActivity_VehicleActivityId_2_VehicleActivity_Id FOREIGN KEY (VehicleActivityId) REFERENCES VehicleActivity(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_PeriodEvaluationActivity_PeriodEvaluationId ON PeriodEvaluationActivity(PeriodEvaluationId);

CREATE INDEX IX_PeriodEvaluationActivity_VehicleActivityId ON PeriodEvaluationActivity(VehicleActivityId);

CREATE TABLE PeriodEvaluationIdentity (
  Id INTEGER PRIMARY KEY AUTOINCREMENT,
  PeriodEvaluationId INTEGER NOT NULL,
  CustomerIdentityLinkId INTEGER NOT NULL,
  VerificationOutcomeUsed TEXT NOT NULL CHECK (VerificationOutcomeUsed IS NULL OR length(trim(VerificationOutcomeUsed)) > 0),
  VerifiedAtUsed TEXT NOT NULL CHECK (VerifiedAtUsed IS NULL OR length(trim(VerifiedAtUsed)) > 0),
  EvidenceReferenceUsed TEXT NOT NULL CHECK (EvidenceReferenceUsed IS NULL OR length(trim(EvidenceReferenceUsed)) > 0),
  CONSTRAINT UK_PeriodEvaluationIdentity_BusinessKey UNIQUE (PeriodEvaluationId, CustomerIdentityLinkId),
  CONSTRAINT FK_PeriodEvaluationIdentity_PeriodEvaluationId_2_PeriodEvaluation_Id FOREIGN KEY (PeriodEvaluationId) REFERENCES PeriodEvaluation(Id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT FK_PeriodEvaluationIdentity_CustomerIdentityLinkId_2_CustomerIdentityLink_Id FOREIGN KEY (CustomerIdentityLinkId) REFERENCES CustomerIdentityLink(Id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IX_PeriodEvaluationIdentity_PeriodEvaluationId ON PeriodEvaluationIdentity(PeriodEvaluationId);

CREATE INDEX IX_PeriodEvaluationIdentity_CustomerIdentityLinkId ON PeriodEvaluationIdentity(CustomerIdentityLinkId);

COMMIT;
