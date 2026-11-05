import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  cleanup,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { populatedStore, auth, summary } from "../app/test-fixtures";
import { actions, loadSession, loadResource } from "../app/store";
import KnowledgeBase from "./KnowledgeBase";
import ProviderOnboarding from "./ProviderOnboarding";
import Observability from "./Observability";
import Shell from "./Shell";
import Auth from "./Auth";
import App from "../App";
import Overview from "./Overview";
import { loadWorkspace } from "../app/store";
import { ChangePassword, ActivateProvider } from "./AccountAccess";
import type {
  ApplicationsDocument,
  KnowledgeDocument,
  ProviderApplication,
} from "../app/types";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  history.replaceState(null, "", "/");
});
function mount(node: React.ReactNode, s = populatedStore()) {
  return { s, ...render(<Provider store={s}>{node}</Provider>) };
}
function stubResource(data: unknown) {
  const fetcher = vi.fn(async (path: string, init?: RequestInit) => ({
    ok: true,
    json: async () =>
      path.includes("/api/workspace/status")
        ? summary
        : path.includes("/api/workspace/members")
          ? []
          : data,
  }));
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
const a: ProviderApplication = {
  Id: 1,
  ParentCompanyId: 1,
  LegalName: "New Provider (fictional)",
  RegistrationJurisdiction: "DEMO",
  BusinessRegistrationNumber: "NEW-APP",
  ContactName: "New Contact",
  ContactEmail: "new@example.invalid",
  OutletName: "Main",
  OutletAddress: "Synthetic location",
  capabilities: ["VehicleSale"],
  State: "Draft",
  ProviderId: null,
  Version: 1,
  checks: [],
  history: [],
};
function application(
  state: ProviderApplication["State"] = "Submitted",
): ApplicationsDocument {
  return {
    applications: [{ ...a, State: state }],
    check_definitions: {
      business_registration: "Business registration evidence",
      contact_authority: "Authorized contact evidence",
      capability_compliance: "Capability and compliance evidence",
    },
    capability_options: ["VehicleSale"],
  };
}
const prefix = "urn:retail-mesh:company:1:record:";
const knowledge = {
  scope: { company_id: 1, role: "CompanyAdmin", provider_id: null },
  "@graph": [
    {
      "@id": prefix + "ParentCompany:1",
      "@type": ["rm:Record", "rm:ParentCompany"],
      "rm:sourceTable": "ParentCompany",
      "rm:sourceRowId": 1,
      "rm:LegalName": "Company source (fictional)",
    },
    {
      "@id": prefix + "Provider:4",
      "@type": ["rm:Record", "rm:Provider"],
      "rm:sourceTable": "Provider",
      "rm:sourceRowId": 4,
      "rm:LegalName": "Harbourview source provider",
    },
    {
      "@id": prefix + "ProviderAuthorization:1",
      "@type": ["rm:Record", "rm:ProviderAuthorization"],
      "rm:sourceTable": "ProviderAuthorization",
      "rm:sourceRowId": 1,
      "rm:ParentCompanyId": { "@id": prefix + "ParentCompany:1" },
      "rm:ProviderId": { "@id": prefix + "Provider:4" },
    },
  ],
  summary: {
    nodes: 3,
    edges: 2,
    tables: { ParentCompany: 1, Provider: 1, ProviderAuthorization: 1 },
    imported_awards: 0,
  },
  snapshot_sha256: "a".repeat(64),
  provenance: {
    sources: [],
    nature: "Synthetic",
    decision_semantics: "Imported manual decisions stay separate.",
  },
  validation: { conforms: true },
} as KnowledgeDocument;
describe("operational feature views", () => {
  it("keeps imported activities separate from the fleet-demo preparation state", () => {
    const s = populatedStore();
    s.dispatch(loadWorkspace.pending("imported", 1));
    s.dispatch(
      loadWorkspace.fulfilled(
        {
          companyId: 1,
          summary: {
            ...summary,
            demo_ready: false,
            activities: summary.activities.map((a) => ({
              ...a,
              SourceNamespace: "urn:synthetic:imported",
            })),
            runs: [],
          },
          members: [],
        },
        "imported",
        1,
      ),
    );
    mount(<Overview />, s);
    expect(
      screen.getByRole("button", { name: /Prepare demo journey/ }),
    ).toBeEnabled();
    expect(
      screen.queryByText("Activities recorded. Ready for evaluation."),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Cedar Logistics · Fictional acceptance scenario"),
    ).not.toBeInTheDocument();
  });

  it("opens a provider activation link when only the URL fragment changes", async () => {
    const s = populatedStore();
    s.dispatch(loadSession.pending("anonymous"));
    s.dispatch(
      loadSession.fulfilled(
        { ...auth, user: null, workspaces: [] },
        "anonymous",
      ),
    );
    stubResource({});
    mount(<App />, s);
    expect(
      screen.getByRole("heading", { name: "Sign in to Retail-Mesh" }),
    ).toBeInTheDocument();
    location.hash = "activate?token=test-activation-fragment-1234567890";
    fireEvent(window, new HashChangeEvent("hashchange"));
    expect(
      await screen.findByRole("heading", { name: "Activate provider access" }),
    ).toBeInTheDocument();
  });

  it("starts the first administrator in the supplied companies without duplicate registration fields", async () => {
    const s = populatedStore();
    s.dispatch(loadSession.pending("setup"));
    s.dispatch(
      loadSession.fulfilled(
        {
          ...auth,
          user: null,
          workspaces: [],
          needs_setup: true,
          imported_company_count: 2,
        },
        "setup",
      ),
    );
    const u = userEvent.setup();
    mount(<Auth />, s);
    expect(screen.getByRole("checkbox")).toBeChecked();
    expect(
      screen.queryByLabelText("Company legal name"),
    ).not.toBeInTheDocument();
    await u.click(screen.getByRole("checkbox"));
    expect(screen.getByLabelText("Company legal name")).toBeRequired();
  });

  it("browses knowledge source records without an engine run", async () => {
    stubResource(knowledge);
    mount(<KnowledgeBase />);
    expect(await screen.findByText("3")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download OKF" })).toHaveAttribute(
      "href",
      "/api/workspace/knowledge-export?company_id=1",
    );
    expect(
      screen.getByRole("heading", { name: "Knowledge base" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Company source (fictional)", { selector: "h2" }),
    ).toBeInTheDocument();
  });
  it("filters records and follows exact relationship targets", async () => {
    stubResource(knowledge);
    const u = userEvent.setup();
    mount(<KnowledgeBase />);
    await screen.findByText("3");
    await u.type(
      screen.getByRole("textbox", { name: "Search knowledge records" }),
      "Harbourview",
    );
    expect(
      screen.getByRole("heading", { name: "Harbourview source provider" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Incoming · ProviderId")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /Relationship graph/ }),
    ).toBeInTheDocument();
  });
  it("reviews provider-submitted applications without an admin creation form", async () => {
    stubResource(application());
    mount(<ProviderOnboarding />);
    expect(
      await screen.findByRole("button", { name: "Start application review" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "Accept application" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Reissue activation link" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("Not inserted; application under review"),
    ).toBeInTheDocument();
  });
  it("disables validation until all evidence checks are present", async () => {
    stubResource(application("UnderReview"));
    mount(<ProviderOnboarding />);
    expect(
      await screen.findByRole("button", { name: "Accept application" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Record validated evidence" }),
    ).toBeEnabled();
  });
  it("offers activation only after approval and leaves token out of Redux", async () => {
    const u = userEvent.setup();
    const data = application("Approved");
    const fetcher = vi.fn(async (path: string, init?: RequestInit) => ({
      ok: true,
      json: async () =>
        path.endsWith("application-invite")
          ? {
              token: "private-activation-token-123456789",
              expires_at: 2000000000,
              contact_email: a.ContactEmail,
            }
          : path.includes("/status")
            ? summary
            : path.includes("/members")
              ? []
              : data,
    }));
    vi.stubGlobal("fetch", fetcher);
    const { s } = mount(<ProviderOnboarding />);
    await u.click(
      await screen.findByRole("button", { name: "Reissue activation link" }),
    );
    expect(
      (
        (await screen.findByRole("textbox", {
          name: "Replacement activation link",
        })) as HTMLInputElement
      ).value,
    ).toContain("#activate?token=private-activation-token");
    expect(JSON.stringify(s.getState())).not.toContain(
      "private-activation-token",
    );
    expect(screen.getByText(/No email was sent/)).toBeInTheDocument();
  });
  it("hides administrator pages from provider navigation", () => {
    stubResource({});
    const s = populatedStore();
    s.dispatch(loadSession.pending("p"));
    s.dispatch(
      loadSession.fulfilled(
        {
          ...auth,
          workspaces: [
            { ...auth.workspaces[0], Role: "Provider", ProviderId: 4 },
          ],
        },
        "p",
      ),
    );
    mount(
      <Shell>
        <p>Scoped provider</p>
      </Shell>,
      s,
    );
    expect(
      screen.queryByRole("link", { name: "Provider applications" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Observability" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Knowledge base" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Incentive assistant" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Create company workspace" }),
    ).not.toBeInTheDocument();
  });
  it("requires matching new passwords without sending a request", async () => {
    const fetcher = stubResource({});
    const u = userEvent.setup();
    mount(<ChangePassword />);
    await u.type(
      screen.getByLabelText("Current password"),
      "Old-password-2026",
    );
    await u.type(screen.getByLabelText("New password"), "New-password-2026");
    await u.type(
      screen.getByLabelText("Confirm new password"),
      "Other-password-2026",
    );
    await u.click(
      screen.getByRole("button", { name: "Change password and sign out" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "New passwords must match",
    );
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("changes a password outside Redux and clears the authenticated state", async () => {
    const fetcher = vi.fn(async (path: string, init?: RequestInit) => ({
      ok: true,
      json: async () =>
        path.includes("/auth/status")
          ? { ...auth, user: null, workspaces: [] }
          : {},
    }));
    vi.stubGlobal("fetch", fetcher);
    const u = userEvent.setup();
    const { s } = mount(<ChangePassword />);
    for (const [name, value] of [
      ["Current password", "Old-password-2026"],
      ["New password", "New-password-2026"],
      ["Confirm new password", "New-password-2026"],
    ])
      await u.type(screen.getByLabelText(name), value);
    await u.click(
      screen.getByRole("button", { name: "Change password and sign out" }),
    );
    await waitFor(() => expect(s.getState().session.data?.user).toBeNull());
    expect(JSON.stringify(s.getState())).not.toContain("New-password");
    expect(JSON.parse(String(fetcher.mock.calls[0][1]?.body ?? "{}"))).toEqual({
      current_password: "Old-password-2026",
      new_password: "New-password-2026",
    });
  });
  it("activation consumes the fragment locally and submits no token in the URL", async () => {
    history.replaceState(
      null,
      "",
      "/#activate?token=single-use-token-1234567890123456789",
    );
    const fetcher = stubResource({ message: "Activated" });
    const u = userEvent.setup();
    const { s } = mount(<ActivateProvider />);
    expect(location.hash).toBe("#activate");
    await u.type(screen.getByLabelText("Password"), "Provider-password-2026");
    await u.click(
      screen.getByRole("button", { name: "Activate provider access" }),
    );
    expect(
      await screen.findByText(/Your provider access is active/),
    ).toBeInTheDocument();
    expect(fetcher.mock.calls[0][0]).toBe("/api/auth/activate-provider");
    expect(JSON.stringify(s.getState())).not.toContain("single-use-token");
    expect(JSON.stringify(s.getState())).not.toContain("Provider-password");
  });
  it("renders observability from scoped metrics and shows empty latency honestly", async () => {
    stubResource({
      generated_at: "2026-11-04T10:00:00Z",
      companies: [
        {
          company_id: 1,
          company_name: "Company A",
          providers: 7,
          activities: 35,
          engine_runs: 0,
          recorded_awards: 9,
          recorded_cash: { CAD: "175" },
          other_benefits: { "loyalty:points": "20" },
          pending_applications: 2,
          onboarding_states: { Submitted: 2 },
          active_members: 1,
          requests_24h: 0,
          errors_24h: 0,
          p95_ms: null,
          imports: [],
        },
      ],
      events: [],
      service: {
        database: "reachable",
        request_window_hours: 24,
        retention_days: 7,
      },
      scope: "Only administered companies.",
      limitations: ["Local telemetry only."],
    });
    mount(<Observability />);
    expect(
      await screen.findByRole("heading", { name: "Company A" }),
    ).toBeInTheDocument();
    expect(screen.getByText("p95 No samples")).toBeInTheDocument();
    expect(screen.getByText("CAD 175.00")).toBeInTheDocument();
  });
});
