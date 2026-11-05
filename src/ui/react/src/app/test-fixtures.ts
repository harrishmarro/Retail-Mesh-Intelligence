import { makeStore, loadSession, loadWorkspace } from "./store";
import type { AuthStatus, Summary, Run } from "./types";
export const auth: AuthStatus = {
  needs_setup: false,
  user: {
    Id: 1,
    Email: "preview@example.invalid",
    DisplayName: "Harish Sasikala",
  },
  csrf: "csrf-test",
  workspaces: [
    {
      company_id: 1,
      company_name: "Northstar Motors (fictional)",
      Role: "CompanyAdmin",
      ProviderId: null,
    },
    {
      company_id: 2,
      company_name: "Other company (fictional)",
      Role: "Analyst",
      ProviderId: null,
    },
  ],
  ai: { configured: false, model: null, provider: "openai" },
};
export const summary: Summary = {
  demo_ready: true,
  providers: [
    { Id: 4, LegalName: "Maple Motors (fictional)" },
    { Id: 5, LegalName: "Island Rentals (fictional)" },
    { Id: 6, LegalName: "Harbour Service (fictional)" },
  ],
  activities: [
    {
      Id: 4,
      SourceNamespace: "demo.workspace.1",
      OfficialActivityReference: "NS-SALE-001",
      ActivityKind: "Sale",
      ActivityStatus: "Completed",
      StartedAt: "2026-10-01T10:00:00Z",
      EndedAt: "2026-10-01T10:00:00Z",
      Provider: "Maple Motors (fictional)",
    },
    {
      Id: 5,
      SourceNamespace: "demo.workspace.1",
      OfficialActivityReference: "NS-SERVICE-001",
      ActivityKind: "Service",
      ActivityStatus: "Completed",
      StartedAt: "2026-10-10T09:00:00Z",
      EndedAt: "2026-10-12T17:00:00Z",
      Provider: "Harbour Service (fictional)",
    },
    {
      Id: 6,
      SourceNamespace: "demo.workspace.1",
      OfficialActivityReference: "NS-RENTAL-001",
      ActivityKind: "Rental",
      ActivityStatus: "Completed",
      StartedAt: "2026-10-10T12:00:00Z",
      EndedAt: "2026-10-11T12:00:00Z",
      Provider: "Island Rentals (fictional)",
    },
  ],
  runs: [
    {
      id: 1,
      result: "Qualified",
      created_at: "2026-11-04T10:00:00Z",
      beneficiary: "Maple Motors (fictional)",
      beneficiary_id: 4,
      amount_minor: 15000,
      currency: "CAD",
      fleet_count_before_sale: 12,
    },
  ],
  fleets: [
    {
      Id: 1,
      FleetReference: "CEDAR-FLEET",
      FleetName: "Cedar Logistics (fictional)",
    },
  ],
  role: "CompanyAdmin",
  scope: "workspace_demo_records",
};
export const run: Run = {
  run_id: 1,
  company_id: 1,
  activity_id: 4,
  rule_id: 3,
  rule_version_id: 3,
  beneficiary_id: 4,
  beneficiary: "Maple Motors (fictional)",
  fleet_count_before_sale: 12,
  reward: { amount_minor: 15000, currency: "CAD" },
  result: "Qualified",
  checks: [
    {
      name: "pre_sale_fleet",
      passed: true,
      detail: "12 existing same-manufacturer vehicles; minimum 10",
    },
  ],
  evaluated_at: "2026-11-04T10:00:00Z",
  input_hash: "a".repeat(64),
  event_award_id: 2,
  event_evaluation_id: 2,
};
export function populatedStore() {
  const s = makeStore();
  s.dispatch(loadSession.pending("session"));
  s.dispatch(loadSession.fulfilled(auth, "session"));
  s.dispatch(loadWorkspace.pending("workspace", 1));
  s.dispatch(
    loadWorkspace.fulfilled(
      { companyId: 1, summary, members: [] },
      "workspace",
      1,
    ),
  );
  return s;
}
