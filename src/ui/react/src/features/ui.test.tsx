import { describe, it, expect, vi, afterEach } from "vitest";
import {
  render,
  screen,
  cleanup,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import Auth from "./Auth";
import Overview from "./Overview";
import { Activities } from "./Records";
import { DecisionDetail } from "./RunDetail";
import { Members, Modals } from "./Settings";
import { Dialog } from "../components/ui";
import {
  makeStore,
  loadSession,
  loadWorkspace,
  loadRun,
  actions,
} from "../app/store";
import { auth, summary, run, populatedStore } from "../app/test-fixtures";
// Fixtures are fictional. No live service or external AI requests are made.
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function mount(element: React.ReactNode, store = populatedStore()) {
  return { store, ...render(<Provider store={store}>{element}</Provider>) };
}
describe("operations components", () => {
  it("renders monetary totals from loaded runs without growth claims", () => {
    mount(<Overview />);
    expect(
      screen.getByRole("heading", { name: "Operations overview" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("CAD 150.00").length).toBeGreaterThan(0);
    expect(screen.queryByText(/12\.5%/)).not.toBeInTheDocument();
  });
  it("renders a useful first-run state without fake awards", () => {
    const s = populatedStore();
    s.dispatch(actions.selectCompany(1));
    mount(<Overview />, s);
    expect(screen.getByText("CAD 0.00")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Prepare demo journey/ }),
    ).toBeEnabled();
    expect(screen.getByText("No evaluations yet")).toBeInTheDocument();
  });
  it("filters actual activity rows by reference", async () => {
    const u = userEvent.setup();
    mount(<Activities />);
    await u.type(
      screen.getByRole("textbox", { name: "Search reference or provider" }),
      "RENTAL",
    );
    expect(screen.getByText("NS-RENTAL-001")).toBeInTheDocument();
    expect(screen.queryByText("NS-SALE-001")).not.toBeInTheDocument();
  });
  it("filters activity type through keyboard-capable tabs", async () => {
    const u = userEvent.setup();
    mount(<Activities />);
    await u.click(screen.getByRole("tab", { name: "Service" }));
    expect(screen.getByText("NS-SERVICE-001")).toBeInTheDocument();
    expect(screen.queryByText("NS-SALE-001")).not.toBeInTheDocument();
  });
  it("does not offer mutation controls to an analyst", () => {
    const s = populatedStore();
    s.dispatch(loadSession.pending("analyst"));
    s.dispatch(
      loadSession.fulfilled(
        { ...auth, workspaces: [{ ...auth.workspaces[0], Role: "Analyst" }] },
        "analyst",
      ),
    );
    mount(<Overview />, s);
    expect(screen.getByText("Read-only access")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Evaluate incentive/ }),
    ).not.toBeInTheDocument();
  });
  it("shows a scoped provider decision without graph export links", () => {
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
    s.dispatch(loadRun.pending("r", { companyId: 1, runId: 1 }));
    s.dispatch(
      loadRun.fulfilled({ companyId: 1, run }, "r", { companyId: 1, runId: 1 }),
    );
    mount(<DecisionDetail />, s);
    expect(
      screen.queryByRole("link", { name: "Turtle" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("switch", { name: "Use optional OpenAI narration" }),
    ).toBeDisabled();
    expect(
      screen.getByText(/Full cross-provider evidence is restricted/),
    ).toBeInTheDocument();
  });
  it("keeps optional AI disabled when not configured", () => {
    const s = populatedStore();
    s.dispatch(loadRun.pending("r", { companyId: 1, runId: 1 }));
    s.dispatch(
      loadRun.fulfilled({ companyId: 1, run }, "r", { companyId: 1, runId: 1 }),
    );
    mount(<DecisionDetail />, s);
    expect(
      screen.getByRole("switch", { name: "Use optional OpenAI narration" }),
    ).not.toBeChecked();
    expect(
      screen.getByText("No external model is configured."),
    ).toBeInTheDocument();
  });
  it("uses accessible dialog semantics and closes on Escape", async () => {
    const onChange = vi.fn();
    const u = userEvent.setup();
    mount(
      <Dialog
        open
        onOpenChange={onChange}
        title="Create company"
        description="Independent company context"
      >
        <button>Save</button>
      </Dialog>,
    );
    expect(
      screen.getByRole("dialog", { name: "Create company" }),
    ).toBeInTheDocument();
    await u.keyboard("{Escape}");
    expect(onChange).toHaveBeenCalledWith(false);
  });
  it("requires a named confirmation before revoking access", async () => {
    const u = userEvent.setup();
    const s = populatedStore();
    s.dispatch(loadWorkspace.pending("members", 1));
    s.dispatch(
      loadWorkspace.fulfilled(
        {
          companyId: 1,
          summary,
          members: [
            {
              Id: 2,
              Email: "analyst@example.invalid",
              DisplayName: "Avery Analyst",
              Role: "Analyst",
              ProviderId: null,
              Status: "Active",
            },
          ],
        },
        "members",
        1,
      ),
    );
    mount(
      <>
        <Members />
        <Modals />
      </>,
      s,
    );
    await u.click(screen.getByRole("button", { name: "Revoke access" }));
    expect(
      screen.getByRole("dialog", { name: "Revoke company access?" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Avery Analyst will lose access/),
    ).toBeInTheDocument();
  });
  it("submits login credentials outside Redux actions", async () => {
    const s = makeStore();
    s.dispatch(loadSession.pending("initial"));
    s.dispatch(
      loadSession.fulfilled(
        { ...auth, user: null, workspaces: [], needs_setup: false },
        "initial",
      ),
    );
    const dispatch = vi.spyOn(s, "dispatch");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ csrf: "new" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...auth }) });
    vi.stubGlobal("fetch", fetchMock);
    const u = userEvent.setup();
    mount(<Auth />, s);
    await u.type(
      screen.getByLabelText("Email address"),
      "preview@example.invalid",
    );
    await u.type(screen.getByLabelText("Password"), "Secret-Only-In-Form");
    await u.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const actionsJson = JSON.stringify(
      dispatch.mock.calls.filter(([a]) => typeof a !== "function"),
    );
    expect(actionsJson).not.toContain("Secret-Only-In-Form");
    expect(JSON.stringify(s.getState())).not.toContain("Secret-Only-In-Form");
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });
});
