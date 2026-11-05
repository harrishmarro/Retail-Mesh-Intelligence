import { describe, it, expect, vi } from "vitest";
import {
  makeStore,
  loadSession,
  loadWorkspace,
  loadRun,
  askQuestion,
  actions,
  signedOut,
  selectAwardTotals,
} from "./store";
import type { AuthStatus, Summary, Run } from "./types";
import { auth, summary, run, populatedStore } from "./test-fixtures";
describe("scope-safe Redux state", () => {
  it("uses the authenticated company list for initial selection", () =>
    expect(populatedStore().getState().workspace.companyId).toBe(1));
  it("clears previous company records, decision and narration synchronously", () => {
    const s = populatedStore();
    s.dispatch(actions.aiChanged(true));
    s.dispatch(actions.selectCompany(2));
    expect(s.getState().workspace.summary.activities).toEqual([]);
    expect(s.getState().workspace.run).toBeNull();
    expect(s.getState().ui.useAI).toBe(false);
  });
  it("ignores late responses from a previously selected company", () => {
    const s = populatedStore();
    s.dispatch(loadWorkspace.pending("old", 1));
    s.dispatch(actions.selectCompany(2));
    s.dispatch(
      loadWorkspace.fulfilled({ companyId: 1, summary, members: [] }, "old", 1),
    );
    expect(s.getState().workspace.summary.activities).toEqual([]);
    expect(s.getState().workspace.companyId).toBe(2);
  });
  it("ignores stale workspace requests even when returning to the same company", () => {
    const s = populatedStore();
    s.dispatch(loadWorkspace.pending("old", 1));
    s.dispatch(loadWorkspace.pending("new", 1));
    s.dispatch(
      loadWorkspace.fulfilled({ companyId: 1, summary, members: [] }, "old", 1),
    );
    expect(s.getState().workspace.requestId).toBe("new");
  });
  it("does not restore authenticated state from a pre-logout response", () => {
    const s = populatedStore();
    s.dispatch(loadSession.pending("old"));
    s.dispatch(signedOut);
    s.dispatch(loadSession.fulfilled(auth, "old"));
    expect(s.getState().session.data).toBeNull();
  });
  it("clears privileged data after role downgrade", () => {
    const s = populatedStore();
    s.dispatch(loadSession.pending("new"));
    s.dispatch(
      loadSession.fulfilled(
        {
          ...auth,
          workspaces: [
            { ...auth.workspaces[0], Role: "Provider", ProviderId: 4 },
          ],
        },
        "new",
      ),
    );
    expect(s.getState().workspace.summary.activities).toEqual([]);
    expect(s.getState().workspace.members).toEqual([]);
    expect(s.getState().workspace.companyId).toBe(1);
  });
  it("drops a revoked company and selects only a remaining membership", () => {
    const s = populatedStore();
    s.dispatch(loadSession.pending("new"));
    s.dispatch(
      loadSession.fulfilled(
        { ...auth, workspaces: [auth.workspaces[1]] },
        "new",
      ),
    );
    expect(s.getState().workspace.companyId).toBe(2);
    expect(s.getState().workspace.summary.providers).toEqual([]);
  });
  it("resets all scoped data on API session expiration", () => {
    const s = populatedStore();
    s.dispatch(loadWorkspace.pending("req", 1));
    s.dispatch(
      loadWorkspace.rejected(null, "req", 1, {
        status: 401,
        message: "Expired",
      }),
    );
    expect(s.getState().session.data).toBeNull();
    expect(s.getState().workspace.summary.runs).toEqual([]);
  });
  it("does not accept an old run after another run request begins", () => {
    const s = populatedStore();
    s.dispatch(loadRun.pending("a", { companyId: 1, runId: 1 }));
    s.dispatch(loadRun.pending("b", { companyId: 1, runId: 2 }));
    s.dispatch(
      loadRun.fulfilled({ companyId: 1, run }, "a", { companyId: 1, runId: 1 }),
    );
    expect(s.getState().workspace.run).toBeNull();
  });
  it("does not show narration from a previous run", () => {
    const s = populatedStore();
    s.dispatch(loadRun.pending("run", { companyId: 1, runId: 1 }));
    s.dispatch(
      loadRun.fulfilled({ companyId: 1, run }, "run", {
        companyId: 1,
        runId: 1,
      }),
    );
    s.dispatch(askQuestion.pending("ask"));
    s.dispatch(actions.clearRun());
    s.dispatch(
      askQuestion.fulfilled(
        {
          companyId: 1,
          runId: 1,
          answer: {
            answer: "Old answer",
            mode: "test",
            sources: [],
            ai_status: "not_requested",
            live_llm: false,
          },
        },
        "ask",
      ),
    );
    expect(s.getState().workspace.answer).toBeNull();
  });
  it("keeps currencies separate and excludes duplicate/rejected runs", () => {
    const s = populatedStore();
    const next = {
      ...summary,
      runs: [
        summary.runs[0],
        summary.runs[0],
        { ...summary.runs[0], id: 2, currency: "USD", amount_minor: 2000 },
        {
          ...summary.runs[0],
          id: 3,
          result: "Rejected" as const,
          amount_minor: null,
        },
      ],
    };
    s.dispatch(loadWorkspace.pending("next", 1));
    s.dispatch(
      loadWorkspace.fulfilled(
        { companyId: 1, summary: next, members: [] },
        "next",
        1,
      ),
    );
    expect(selectAwardTotals(s.getState())).toEqual({ CAD: 15000, USD: 2000 });
  });
  it("rejected request preserves the last good data for retry", () => {
    const s = populatedStore();
    s.dispatch(loadWorkspace.pending("retry", 1));
    s.dispatch(
      loadWorkspace.rejected(null, "retry", 1, {
        status: 500,
        message: "Network unavailable",
      }),
    );
    expect(s.getState().workspace.summary.activities).toHaveLength(3);
    expect(s.getState().workspace.phase).toBe("error");
  });
});

import { loadResource } from "./store";
describe("new resource scope protection", () => {
  it("removes cached administrator data when access is denied", () => {
    const s = populatedStore();
    s.dispatch(
      loadResource.pending("first", {
        companyId: 1,
        resource: "observability",
      }),
    );
    s.dispatch(
      loadResource.fulfilled(
        {
          companyId: 1,
          resource: "observability",
          data: ["private-admin-data"],
        },
        "first",
        { companyId: 1, resource: "observability" },
      ),
    );
    s.dispatch(
      loadResource.pending("denied", {
        companyId: 1,
        resource: "observability",
      }),
    );
    s.dispatch(
      loadResource.rejected(
        null,
        "denied",
        { companyId: 1, resource: "observability" },
        { message: "Access denied", status: 403 },
      ),
    );
    expect(s.getState().workspace.resources.observability.data).toBeNull();
  });

  it("clears knowledge and admin resources synchronously on company switch", () => {
    const s = populatedStore();
    s.dispatch(
      loadResource.pending("kg", { companyId: 1, resource: "knowledge" }),
    );
    s.dispatch(
      loadResource.fulfilled(
        {
          companyId: 1,
          resource: "knowledge",
          data: { private: "company-one" },
        },
        "kg",
        { companyId: 1, resource: "knowledge" },
      ),
    );
    s.dispatch(actions.selectCompany(2));
    expect(s.getState().workspace.resources.knowledge.data).toBeNull();
  });
  it("discards a late resource response from another company", () => {
    const s = populatedStore();
    s.dispatch(
      loadResource.pending("kg", { companyId: 1, resource: "knowledge" }),
    );
    s.dispatch(actions.selectCompany(2));
    s.dispatch(
      loadResource.fulfilled(
        {
          companyId: 1,
          resource: "knowledge",
          data: { private: "company-one" },
        },
        "kg",
        { companyId: 1, resource: "knowledge" },
      ),
    );
    expect(s.getState().workspace.resources.knowledge.data).toBeNull();
  });
  it("discards an older same-company resource response", () => {
    const s = populatedStore();
    s.dispatch(
      loadResource.pending("old", { companyId: 1, resource: "applications" }),
    );
    s.dispatch(
      loadResource.pending("new", { companyId: 1, resource: "applications" }),
    );
    s.dispatch(
      loadResource.fulfilled(
        { companyId: 1, resource: "applications", data: ["stale"] },
        "old",
        { companyId: 1, resource: "applications" },
      ),
    );
    expect(s.getState().workspace.resources.applications.data).toBeNull();
  });
  it("clears administrator resources after role downgrade", () => {
    const s = populatedStore();
    s.dispatch(
      loadResource.pending("obs", { companyId: 1, resource: "observability" }),
    );
    s.dispatch(
      loadResource.fulfilled(
        { companyId: 1, resource: "observability", data: ["admin-only"] },
        "obs",
        { companyId: 1, resource: "observability" },
      ),
    );
    s.dispatch(loadSession.pending("downgrade"));
    s.dispatch(
      loadSession.fulfilled(
        { ...auth, workspaces: [{ ...auth.workspaces[0], Role: "Analyst" }] },
        "downgrade",
      ),
    );
    expect(s.getState().workspace.resources.observability.data).toBeNull();
  });
});
