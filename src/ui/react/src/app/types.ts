export type Role = "CompanyAdmin" | "CompanyOperator" | "Analyst" | "Provider";
export interface User {
  Id: number;
  Email: string;
  DisplayName: string;
}
export interface Company {
  company_id: number;
  company_name: string;
  Role: Role;
  ProviderId: number | null;
}
export interface AuthStatus {
  imported_company_count?: number;
  needs_setup: boolean;
  user: User | null;
  csrf: string;
  workspaces: Company[];
  ai: { configured: boolean; model: string | null; provider: string };
}
export interface ProviderRecord {
  Id: number;
  LegalName: string;
}
export interface Activity {
  SourceNamespace?: string;
  Id: number;
  OfficialActivityReference: string;
  ActivityKind: "Sale" | "Service" | "Rental";
  ActivityStatus: string;
  StartedAt: string;
  EndedAt: string | null;
  Provider: string;
}
export interface RunSummary {
  id: number;
  result: "Qualified" | "Rejected";
  created_at: string;
  beneficiary: string;
  beneficiary_id: number;
  amount_minor: number | null;
  currency: string;
  fleet_count_before_sale: number;
}
export interface Fleet {
  Id: number;
  FleetReference: string;
  FleetName: string;
}
export interface Summary {
  demo_ready?: boolean;
  recorded_awards?: RecordedAward[];
  providers: ProviderRecord[];
  activities: Activity[];
  runs: RunSummary[];
  fleets: Fleet[];
  role: Role;
  scope: string;
}
export interface Check {
  name: string;
  passed: boolean;
  detail: string;
}
export interface Run {
  run_id: number;
  company_id: number;
  activity_id: number;
  rule_id: number;
  rule_version_id: number;
  beneficiary_id: number;
  beneficiary: string;
  fleet_count_before_sale: number;
  reward: { amount_minor: number; currency: string };
  result: "Qualified" | "Rejected";
  checks: Check[];
  evaluated_at: string;
  input_hash: string;
  event_award_id: number | null;
  event_evaluation_id: number | null;
  replayed?: boolean;
  review_required?: boolean;
  evidence?: {
    sale: Record<string, unknown>;
    selected?: {
      service: Record<string, unknown>;
      rental: Record<string, unknown>;
    } | null;
  };
}
export interface Member {
  Id: number;
  Email: string;
  DisplayName: string;
  Role: Role;
  ProviderId: number | null;
  Status: string;
}
export interface Answer {
  answer: string;
  mode: string;
  sources: { type: string; id?: number; sha256?: string }[];
  ai_status: string;
  live_llm: boolean;
  ai_narrative?: string;
  graph_validation?: { conforms: boolean; triples: number };
}
export type View =
  | "overview"
  | "activities"
  | "incentives"
  | "providers"
  | "knowledge"
  | "members"
  | "settings"
  | "onboarding"
  | "observability"
  | "claims"
  | "concerns"
  | "chat";
export interface Failure {
  message: string;
  status: number;
}

export interface RecordedAward {
  id: number;
  kind: string;
  status: string;
  issued_at: string;
  evaluation_id: number;
  rule_id: number;
  origin: string;
  components: {
    RewardType: string;
    BenefitValue: number | string;
    UnitScheme: string;
    UnitCode: string;
    Currency: string | null;
  }[];
}
export type Resource =
  "knowledge" | "applications" | "observability" | "claims" | "concerns";
export interface ResourceState {
  data: unknown;
  phase: "idle" | "loading" | "ready" | "error";
  error: Failure | null;
  requestId: string | null;
}
export interface KnowledgeNode {
  "@id": string;
  "@type": string[];
  "rm:sourceTable": string;
  "rm:sourceRowId": number;
  [key: string]: unknown;
}
export interface KnowledgeDocument {
  "@graph": KnowledgeNode[];
  scope: { company_id: number; role: Role; provider_id: number | null };
  summary: {
    nodes: number;
    edges: number;
    tables: Record<string, number>;
    imported_awards: number;
  };
  snapshot_sha256: string;
  provenance: {
    sources: { sha256: string; filename: string }[];
    nature: string;
    decision_semantics: string;
  };
  validation: { conforms: boolean };
}
export interface ProviderApplication {
  ContactPhone?: string;
  Website?: string;
  ApplicantEvidenceReferences?: string;
  RequestedProgramsJson?: string;
  Id: number;
  ParentCompanyId: number;
  LegalName: string;
  RegistrationJurisdiction: string;
  BusinessRegistrationNumber: string;
  ReviewNote?: string;
  ContactName: string;
  ContactEmail: string;
  OutletName: string;
  OutletAddress: string;
  capabilities: string[];
  State:
    | "Draft"
    | "Submitted"
    | "UnderReview"
    | "NeedsChanges"
    | "Validated"
    | "Approved"
    | "Provisioned"
    | "Rejected";
  ProviderId: number | null;
  Version: number;
  checks: {
    CheckCode: string;
    EvidenceReference: string;
    ReviewedBy: number;
    ReviewedAt: number;
  }[];
  history: { Id: number; Action: string; UserId: number; CreatedAt: number }[];
}
export interface ApplicationsDocument {
  signup?: { enabled: boolean; public_code: string | null };
  program_options?: { Id: number; ProgramName: string }[];
  applications: ProviderApplication[];
  check_definitions: Record<string, string>;
  capability_options: string[];
}
export interface ObservabilityDocument {
  generated_at: string;
  companies: {
    company_id: number;
    company_name: string;
    providers: number;
    activities: number;
    engine_runs: number;
    recorded_awards: number;
    recorded_cash: Record<string, string>;
    other_benefits: Record<string, string>;
    pending_applications: number;
    onboarding_states: Record<string, number>;
    active_members: number;
    requests_24h: number;
    errors_24h: number;
    p95_ms: number | null;
    imports: {
      Id: number;
      SourceName: string;
      ContentSha256: string;
      ImportedAt: number;
    }[];
  }[];
  events: {
    Id: number;
    company_id: number;
    company_name: string;
    Action: string;
    TargetReference: string;
    CreatedAt: number;
    UserId: number;
  }[];
  service: {
    database: string;
    request_window_hours: number;
    retention_days: number;
  };
  scope: string;
  limitations: string[];
}

export interface ClaimRecord {
  Id: number;
  Reference: string;
  ProviderId: number;
  ProviderName: string;
  IncentiveRuleId: number;
  ClaimType: "Event" | "Period";
  VehicleActivityId: number | null;
  PeriodStart: string | null;
  PeriodEnd: string | null;
  Statement: string;
  EvidenceReference: string;
  RequestedAmountMinor: number | null;
  Currency: string | null;
  Status: string;
  ReviewNote: string;
  Version: number;
  CreatedAt: number;
  UpdatedAt: number;
  history: {
    ActorId: number;
    Action: string;
    Message: string;
    CreatedAt: number;
  }[];
}
export interface ClaimDocument {
  claims: ClaimRecord[];
  role: Role;
  options: {
    rules: {
      Id: number;
      RuleName: string;
      AssessmentBasis: "Event" | "Period";
    }[];
    activities: Activity[];
  } | null;
}
export interface ConcernRecord {
  Id: number;
  ProviderId: number;
  Kind?: "Incentive" | "WorkspaceAccess";
  RequestedWorkspaceName?: string;
  Subject: string;
  Status: string;
  Version: number;
  CreatedAt: number;
  ClaimId: number | null;
  messages: { ActorId: number; Message: string; CreatedAt: number }[];
}
export interface ConcernDocument {
  concerns: ConcernRecord[];
  role: Role;
}
