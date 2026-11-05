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
import { loadSession, loadWorkspace } from "../app/store";
import type { Role } from "../app/types";
import ProviderSignup, { ProviderApplicationStatus } from "./ProviderSignup";
import { Claims, Concerns, ProviderChat } from "./ProviderWorkspace";
import Shell from "./Shell";
import { Settings } from "./Settings";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  history.replaceState(null, "", "/");
});
function roleStore(role: Role = "Provider") {
  const s = populatedStore();
  s.dispatch(loadSession.pending("role"));
  s.dispatch(
    loadSession.fulfilled(
      {
        ...auth,
        workspaces: [
          {
            ...auth.workspaces[0],
            Role: role,
            ProviderId: role === "Provider" ? 4 : null,
          },
        ],
      },
      "role",
    ),
  );
  s.dispatch(loadWorkspace.pending("scope", 1));
  s.dispatch(
    loadWorkspace.fulfilled(
      { companyId: 1, summary: { ...summary, role }, members: [] },
      "scope",
      1,
    ),
  );
  return s;
}
function mount(node: React.ReactNode, s = roleStore()) {
  return { s, ...render(<Provider store={s}>{node}</Provider>) };
}
function fetcher(
  resolver: (path: string, data?: Record<string, unknown>) => unknown,
) {
  const f = vi.fn(async (path: string, init?: RequestInit) => ({
    ok: true,
    json: async () =>
      resolver(path, init?.body ? JSON.parse(String(init.body)) : undefined),
  }));
  vi.stubGlobal("fetch", f);
  return f;
}
const portal = {
  company_name: "Cascadia (fictional)",
  capability_options: ["VehicleSale"],
  programs: [{ Id: 1, ProgramName: "Partner incentives" }],
};
const applicant = {
  ...portal,
  Id: 10,
  Version: 2,
  LegalName: "Applicant (fictional)",
  RegistrationJurisdiction: "DEMO",
  BusinessRegistrationNumber: "APP-001",
  ContactName: "Applicant Contact",
  ContactEmail: "applicant@example.invalid",
  ContactPhone: "+12505550199",
  OutletName: "Main",
  OutletAddress: "Synthetic address",
  Website: "",
  ApplicantEvidenceReferences: "synthetic:documents",
  capabilities: ["VehicleSale"],
  program_ids: [1],
  State: "Submitted",
  decision: "Submitted",
  review_note: "",
  activation_available: false,
};
const claim = {
  Id: 9,
  Reference: "CLM-EXAMPLE",
  ProviderId: 4,
  ProviderName: "Provider (fictional)",
  IncentiveRuleId: 2,
  ClaimType: "Period",
  VehicleActivityId: null,
  PeriodStart: "2026-07-01",
  PeriodEnd: "2026-10-01",
  Statement: "Please review my quarterly incentive",
  EvidenceReference: "synthetic:claim",
  RequestedAmountMinor: 25000,
  Currency: "CAD",
  Status: "Submitted",
  ReviewNote: "",
  Version: 1,
  CreatedAt: 1793800000,
  UpdatedAt: 1793800000,
  history: [],
};
const claimData = {
  claims: [claim],
  role: "Provider",
  options: {
    rules: [{ Id: 2, RuleName: "Quarterly review", AssessmentBasis: "Period" }],
    activities: [],
  },
};
describe("public provider and operator workflow", () => {
  it("keeps public signup separate from sign-in and does not create a password field before acceptance", async () => {
    history.replaceState(
      null,
      "",
      "/#provider-signup?code=public-code-example",
    );
    fetcher(() => portal);
    mount(<ProviderSignup />);
    expect(
      await screen.findByRole("heading", { name: "Cascadia (fictional)" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Legal business name")).toBeRequired();
    expect(screen.getByLabelText("Contact phone")).toBeRequired();
    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Submit application for review" }),
    ).toBeEnabled();
  });
  it("submits business details and keeps the private tracking token outside Redux", async () => {
    history.replaceState(
      null,
      "",
      "/#provider-signup?code=public-code-example",
    );
    const f = fetcher((path) =>
      path.includes("/provider-submit")
        ? {
            tracking_token: "private-tracking-token-example-12345",
            application_reference: "APP-10",
          }
        : portal,
    );
    const u = userEvent.setup();
    const { s } = mount(<ProviderSignup />);
    await screen.findByLabelText("Legal business name");
    for (const [name, value] of [
      ["Legal business name", "Applicant"],
      ["Registration jurisdiction", "DEMO"],
      ["Business registration number", "APP-001"],
      ["Contact name", "Contact"],
      ["Contact email", "applicant@example.invalid"],
      ["Contact phone", "+12505550199"],
      ["Outlet name", "Main"],
      ["Outlet address", "Synthetic address"],
      ["Supporting evidence references", "synthetic:references"],
    ])
      await u.type(screen.getByLabelText(name), value);
    await u.click(screen.getByLabelText("VehicleSale"));
    await u.click(
      screen.getByRole("button", { name: "Submit application for review" }),
    );
    expect(
      (
        (await screen.findByRole("textbox", {
          name: "Private application tracking link",
        })) as HTMLInputElement
      ).value,
    ).toContain("#provider-application?token=private-tracking");
    expect(JSON.stringify(s.getState())).not.toContain("private-tracking");
    const sent = f.mock.calls.find(([path]) =>
      path.includes("provider-submit"),
    );
    expect(JSON.parse(String(sent?.[1]?.body)).capabilities).toEqual([
      "VehicleSale",
    ]);
  });
  it("shows operator changes and lets the applicant resubmit without account access", async () => {
    history.replaceState(
      null,
      "",
      "/#provider-application?token=private-tracking-token-example-12345",
    );
    fetcher(() => ({
      ...applicant,
      State: "NeedsChanges",
      decision: "Changes needed",
      review_note: "Correct the outlet address",
    }));
    mount(<ProviderApplicationStatus />);
    expect(
      await screen.findByText("Correct the outlet address"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Submit changes for review" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", {
        name: "Activate accepted provider account",
      }),
    ).not.toBeInTheDocument();
    expect(location.hash).toBe("#provider-application");
  });
  it("shows account activation only after accepted review", async () => {
    history.replaceState(
      null,
      "",
      "/#provider-application?token=private-tracking-token-example-12345",
    );
    fetcher(() => ({
      ...applicant,
      State: "Approved",
      decision: "Accepted",
      activation_available: true,
    }));
    mount(<ProviderApplicationStatus />);
    expect(
      await screen.findByRole("button", {
        name: "Activate accepted provider account",
      }),
    ).toBeEnabled();
    expect(screen.getByLabelText("Password")).toBeRequired();
  });
  it("provider sees own claim status and cannot approve a claim", async () => {
    fetcher(() => claimData);
    mount(<Claims />);
    expect(
      await screen.findByRole("heading", { name: "CLM-EXAMPLE" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Request incentive claim" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "Start claim review" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Approved" }),
    ).not.toBeInTheDocument();
  });
  it("provider can edit only a claim returned for changes", async () => {
    fetcher(() => ({
      ...claimData,
      claims: [
        {
          ...claim,
          Status: "ChangesNeeded",
          ReviewNote: "Add source evidence",
        },
      ],
    }));
    const u = userEvent.setup();
    mount(<Claims />);
    await u.click(
      await screen.findByRole("button", { name: "Edit and resubmit claim" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Update incentive claim" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Evidence reference")).toHaveValue(
      "synthetic:claim",
    );
  });
  it("operator can review claims but does not get provider submission controls", async () => {
    fetcher(() => ({ ...claimData, role: "CompanyOperator", options: null }));
    mount(<Claims />, roleStore("CompanyOperator"));
    expect(
      await screen.findByRole("button", { name: "Start claim review" }),
    ).toBeEnabled();
    expect(
      screen.queryByRole("button", { name: "Request incentive claim" }),
    ).not.toBeInTheDocument();
  });
  it("provider can request workspace access without workspace creation controls", async () => {
    fetcher(() => ({ role: "Provider", concerns: [] }));
    const u = userEvent.setup();
    mount(<Concerns />);
    await u.click(
      await screen.findByRole("button", { name: "Request workspace access" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Request workspace access" }),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Requested workspace or company"),
    ).toBeRequired();
    expect(screen.getByText(/submission grants no access/)).toBeInTheDocument();
  });
  it("provider chatbot gives sourced policy text without graph links", async () => {
    const f = fetcher(() => ({
      answer: "At least two completed services qualify for 500 POINT.",
      sources: [{ type: "RuleVersion", id: 4 }],
      live_llm: false,
    }));
    const u = userEvent.setup();
    mount(<ProviderChat />);
    await u.click(
      screen.getByRole("button", { name: "Ask incentive assistant" }),
    );
    expect(
      await screen.findByText(/At least two completed services/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Download OKF" }),
    ).not.toBeInTheDocument();
    expect(f.mock.calls[0][0]).toBe("/api/workspace/provider-chat");
  });
  it("operator gets graph and review navigation but not administrator management", () => {
    mount(
      <Shell>
        <p>Operator console</p>
      </Shell>,
      roleStore("CompanyOperator"),
    );
    expect(
      screen.getByRole("link", { name: "Knowledge base" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Provider applications" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Team members" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Observability" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Create company workspace" }),
    ).not.toBeInTheDocument();
  });
  it("provider account settings never offer workspace creation", () => {
    mount(<Settings />);
    expect(
      screen.queryByRole("button", { name: "Create another workspace" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        /Workspace creation is controlled by the company administrator/,
      ),
    ).toBeInTheDocument();
  });
});
