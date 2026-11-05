import {
  combineReducers,
  configureStore,
  createSelector,
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from "@reduxjs/toolkit";
import { request, failure } from "./client";
import type {
  AuthStatus,
  Summary,
  Member,
  Run,
  Answer,
  Failure,
  View,
  Resource,
  ResourceState,
} from "./types";
const emptySummary = (): Summary => ({
  demo_ready: false,
  providers: [],
  activities: [],
  runs: [],
  fleets: [],
  role: "Analyst",
  scope: "workspace_demo_records",
});
const initialSession = {
  phase: "idle" as "idle" | "loading" | "ready" | "error",
  data: null as AuthStatus | null,
  error: null as Failure | null,
  requestId: null as string | null,
};
const initialWorkspace = {
  companyId: null as number | null,
  summary: emptySummary(),
  members: [] as Member[],
  resources: Object.fromEntries(
    ["knowledge", "applications", "observability", "claims", "concerns"].map(
      (key) => [
        key,
        { data: null, phase: "idle", error: null, requestId: null },
      ],
    ),
  ) as Record<Resource, ResourceState>,
  run: null as Run | null,
  answer: null as Answer | null,
  phase: "idle" as "idle" | "loading" | "ready" | "error",
  busy: null as string | null,
  error: null as Failure | null,
  requestId: null as string | null,
  runRequestId: null as string | null,
  answerRequestId: null as string | null,
  updatedAt: null as string | null,
};
const initialUI = {
  view: "overview" as View,
  query: "",
  status: "All",
  mobileOpen: false,
  modal: null as null | "company" | "member" | "revoke",
  revokeId: null as number | null,
  question: "Why did Maple Motors receive CAD 150?",
  useAI: false,
  notice: null as string | null,
};
export const loadSession = createAsyncThunk<
  AuthStatus,
  void,
  { rejectValue: Failure }
>("session/load", async (_, api) => {
  try {
    return await request<AuthStatus>(
      "/api/auth/status",
      undefined,
      "",
      api.signal,
    );
  } catch (e) {
    return api.rejectWithValue(failure(e));
  }
});
type Thunk = { state: RootState; rejectValue: Failure };
export const loadWorkspace = createAsyncThunk<
  { companyId: number; summary: Summary; members: Member[] },
  number,
  Thunk
>("workspace/load", async (companyId, api) => {
  try {
    const role = api
      .getState()
      .session.data?.workspaces.find((c) => c.company_id === companyId)?.Role;
    const [summary, members] = await Promise.all([
      request<Summary>(
        "/api/workspace/status?company_id=" + companyId,
        undefined,
        "",
        api.signal,
      ),
      role === "CompanyAdmin"
        ? request<Member[]>(
            "/api/workspace/members?company_id=" + companyId,
            undefined,
            "",
            api.signal,
          )
        : Promise.resolve([]),
    ]);
    return { companyId, summary, members };
  } catch (e) {
    return api.rejectWithValue(failure(e));
  }
});
export const loadRun = createAsyncThunk<
  { companyId: number; run: Run },
  { companyId: number; runId: number },
  Thunk
>("workspace/run", async ({ companyId, runId }, api) => {
  try {
    return {
      companyId,
      run: await request<Run>(
        `/api/workspace/run?company_id=${companyId}&run_id=${runId}`,
        undefined,
        "",
        api.signal,
      ),
    };
  } catch (e) {
    return api.rejectWithValue(failure(e));
  }
});
export const evaluateRule = createAsyncThunk<
  { companyId: number; run: Run },
  number,
  Thunk
>("workspace/evaluate", async (companyId, api) => {
  try {
    return {
      companyId,
      run: await request<Run>(
        "/api/workspace/evaluate",
        { company_id: companyId },
        api.getState().session.data?.csrf,
        api.signal,
      ),
    };
  } catch (e) {
    return api.rejectWithValue(failure(e));
  }
});
export const askQuestion = createAsyncThunk<
  { companyId: number; runId: number; answer: Answer },
  void,
  Thunk
>("workspace/ask", async (_, api) => {
  const state = api.getState(),
    companyId = state.workspace.companyId!,
    runId = state.workspace.run!.run_id;
  try {
    return {
      companyId,
      runId,
      answer: await request<Answer>(
        "/api/workspace/ask",
        {
          company_id: companyId,
          run_id: runId,
          question: state.ui.question,
          use_ai: state.ui.useAI,
        },
        state.session.data?.csrf,
        api.signal,
      ),
    };
  } catch (e) {
    return api.rejectWithValue(failure(e));
  }
});
export const loadResource = createAsyncThunk<
  { companyId: number; resource: Resource; data: unknown },
  { companyId: number; resource: Resource },
  Thunk
>("workspace/resource", async ({ companyId, resource }, api) => {
  try {
    return {
      companyId,
      resource,
      data: await request(
        `/api/workspace/${resource}?company_id=${companyId}`,
        undefined,
        "",
        api.signal,
      ),
    };
  } catch (e) {
    const problem = failure(e);
    if (problem.status === 403) api.dispatch(loadSession());
    return api.rejectWithValue(problem);
  }
});
const session = createSlice({
  name: "session",
  initialState: initialSession,
  reducers: {},
  extraReducers: (b) => {
    b.addCase(loadSession.pending, (s, a) => {
      s.phase = "loading";
      s.error = null;
      s.requestId = a.meta.requestId;
    })
      .addCase(loadSession.fulfilled, (s, a) => {
        if (s.requestId !== a.meta.requestId) return;
        s.phase = "ready";
        s.data = a.payload;
        s.requestId = null;
      })
      .addCase(loadSession.rejected, (s, a) => {
        if (s.requestId !== a.meta.requestId) return;
        s.phase = "error";
        s.error = a.payload ?? {
          message: "Could not connect to Retail-Mesh.",
          status: 0,
        };
        s.requestId = null;
      });
  },
});
const workspace = createSlice({
  name: "workspace",
  initialState: initialWorkspace,
  reducers: {
    selectCompany: (_, a: PayloadAction<number | null>) => ({
      ...initialWorkspace,
      summary: emptySummary(),
      companyId: a.payload,
    }),
    clearRun: (s) => {
      s.run = null;
      s.answer = null;
      s.runRequestId = null;
      s.answerRequestId = null;
    },
    setBusy: (s, a: PayloadAction<string | null>) => {
      s.busy = a.payload;
    },
    clearError: (s) => {
      s.error = null;
    },
  },
  extraReducers: (b) => {
    b.addCase(loadResource.pending, (s, a) => {
      if (s.companyId !== a.meta.arg.companyId) return;
      const r = s.resources[a.meta.arg.resource];
      r.phase = "loading";
      r.error = null;
      r.requestId = a.meta.requestId;
    })
      .addCase(loadResource.fulfilled, (s, a) => {
        const r = s.resources[a.payload.resource];
        if (
          s.companyId !== a.payload.companyId ||
          r.requestId !== a.meta.requestId
        )
          return;
        r.data = a.payload.data;
        r.phase = "ready";
        r.requestId = null;
      })
      .addCase(loadResource.rejected, (s, a) => {
        const r = s.resources[a.meta.arg.resource];
        if (
          s.companyId !== a.meta.arg.companyId ||
          r.requestId !== a.meta.requestId
        )
          return;
        r.phase = "error";
        if (a.payload?.status === 403) r.data = null;
        r.error = a.payload ?? {
          message: "Could not load this view",
          status: 0,
        };
        r.requestId = null;
      })
      .addCase(loadWorkspace.pending, (s, a) => {
        if (s.companyId !== a.meta.arg) return;
        s.phase = "loading";
        s.error = null;
        s.requestId = a.meta.requestId;
      })
      .addCase(loadWorkspace.fulfilled, (s, a) => {
        if (
          s.companyId !== a.payload.companyId ||
          s.requestId !== a.meta.requestId
        )
          return;
        s.summary = a.payload.summary;
        s.members = a.payload.members;
        s.phase = "ready";
        s.updatedAt = new Date().toISOString();
        s.requestId = null;
      })
      .addCase(loadWorkspace.rejected, (s, a) => {
        if (s.companyId !== a.meta.arg || s.requestId !== a.meta.requestId)
          return;
        s.phase = "error";
        s.error = a.payload ?? {
          message: "Workspace could not be loaded.",
          status: 0,
        };
        s.requestId = null;
      })
      .addCase(loadRun.pending, (s, a) => {
        if (s.companyId !== a.meta.arg.companyId) return;
        s.runRequestId = a.meta.requestId;
        s.run = null;
        s.answer = null;
        s.answerRequestId = null;
        s.busy = "run";
      })
      .addCase(loadRun.fulfilled, (s, a) => {
        if (
          s.companyId !== a.payload.companyId ||
          s.runRequestId !== a.meta.requestId
        )
          return;
        s.run = a.payload.run;
        s.runRequestId = null;
        s.busy = null;
      })
      .addCase(loadRun.rejected, (s, a) => {
        if (s.runRequestId !== a.meta.requestId) return;
        s.busy = null;
        s.error = a.payload ?? null;
      })
      .addCase(evaluateRule.pending, (s, a) => {
        if (s.companyId !== a.meta.arg) return;
        s.busy = "evaluate";
        s.error = null;
        s.runRequestId = a.meta.requestId;
        s.answer = null;
        s.answerRequestId = null;
      })
      .addCase(evaluateRule.fulfilled, (s, a) => {
        if (
          s.companyId !== a.payload.companyId ||
          s.runRequestId !== a.meta.requestId
        )
          return;
        s.run = a.payload.run;
        s.runRequestId = null;
        s.busy = null;
      })
      .addCase(evaluateRule.rejected, (s, a) => {
        if (s.runRequestId !== a.meta.requestId) return;
        s.busy = null;
        s.error = a.payload ?? null;
      })
      .addCase(askQuestion.pending, (s, a) => {
        s.busy = "ask";
        s.answer = null;
        s.answerRequestId = a.meta.requestId;
      })
      .addCase(askQuestion.fulfilled, (s, a) => {
        if (
          s.companyId !== a.payload.companyId ||
          s.run?.run_id !== a.payload.runId ||
          s.answerRequestId !== a.meta.requestId
        )
          return;
        s.answer = a.payload.answer;
        s.busy = null;
        s.answerRequestId = null;
      })
      .addCase(askQuestion.rejected, (s, a) => {
        if (s.answerRequestId !== a.meta.requestId) return;
        s.busy = null;
        s.error = a.payload ?? null;
      });
  },
});
const ui = createSlice({
  name: "ui",
  initialState: initialUI,
  reducers: {
    navigate: (s, a: PayloadAction<View>) => {
      s.view = a.payload;
      s.query = "";
      s.status = "All";
      s.mobileOpen = false;
    },
    queryChanged: (s, a: PayloadAction<string>) => {
      s.query = a.payload;
    },
    statusChanged: (s, a: PayloadAction<string>) => {
      s.status = a.payload;
    },
    mobileChanged: (s, a: PayloadAction<boolean>) => {
      s.mobileOpen = a.payload;
    },
    modalChanged: (s, a: PayloadAction<typeof initialUI.modal>) => {
      s.modal = a.payload;
    },
    revokeChosen: (s, a: PayloadAction<number>) => {
      s.revokeId = a.payload;
      s.modal = "revoke";
    },
    questionChanged: (s, a: PayloadAction<string>) => {
      s.question = a.payload;
    },
    aiChanged: (s, a: PayloadAction<boolean>) => {
      s.useAI = a.payload;
    },
    noticeChanged: (s, a: PayloadAction<string | null>) => {
      s.notice = a.payload;
    },
  },
  extraReducers: (b) => {
    b.addCase(workspace.actions.selectCompany, () => ({ ...initialUI }))
      .addCase(loadRun.pending, (s) => {
        s.useAI = false;
      })
      .addCase(evaluateRule.pending, (s) => {
        s.useAI = false;
      });
  },
});
const combined = combineReducers({
  session: session.reducer,
  workspace: workspace.reducer,
  ui: ui.reducer,
});
export const signedOut = { type: "session/clear" } as const;
export const rootReducer: typeof combined = (state, action) => {
  if (
    action.type === signedOut.type ||
    (action.type.endsWith("/rejected") &&
      (action as { payload?: Failure }).payload?.status === 401)
  )
    return combined(undefined, { type: "reset" });
  const next = combined(state, action);
  if (
    loadSession.fulfilled.match(action) &&
    next.session.data === action.payload
  ) {
    const previousId = state?.session?.data?.user?.Id;
    if (!action.payload.user)
      return {
        ...next,
        workspace: { ...initialWorkspace, summary: emptySummary() },
        ui: { ...initialUI },
      };
    const currentMembership = action.payload.workspaces.find(
      (w) => w.company_id === next.workspace.companyId,
    );
    const oldMembership = state?.session?.data?.workspaces.find(
      (w) => w.company_id === next.workspace.companyId,
    );
    const allowed = !!currentMembership;
    const scopeChanged =
      currentMembership?.Role !== oldMembership?.Role ||
      currentMembership?.ProviderId !== oldMembership?.ProviderId;
    if (previousId !== action.payload.user.Id || !allowed || scopeChanged)
      return {
        ...next,
        workspace: {
          ...initialWorkspace,
          summary: emptySummary(),
          companyId: allowed
            ? next.workspace.companyId
            : (action.payload.workspaces[0]?.company_id ?? null),
        },
        ui: { ...initialUI },
      };
  }
  return next;
};
export function makeStore() {
  return configureStore({ reducer: rootReducer, devTools: false });
}
export const store = makeStore();
export const actions = { ...workspace.actions, ...ui.actions };
export type RootState = ReturnType<typeof combined>;
export type AppDispatch = typeof store.dispatch;
export const selectAwardTotals = createSelector(
  [(state: RootState) => state.workspace.summary.runs],
  (runs) => {
    const sums: Record<string, number> = {};
    const ids = new Set<number>();
    for (const run of runs) {
      if (
        ids.has(run.id) ||
        run.result !== "Qualified" ||
        run.amount_minor === null
      )
        continue;
      ids.add(run.id);
      sums[run.currency] = (sums[run.currency] ?? 0) + run.amount_minor;
    }
    return sums;
  },
);
