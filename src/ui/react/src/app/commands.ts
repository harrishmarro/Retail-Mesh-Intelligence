import { useStore } from "react-redux";
import { request, failure } from "./client";
import {
  actions,
  loadWorkspace,
  type RootState,
  type AppDispatch,
} from "./store";
import { useAppDispatch, useAppSelector } from "./hooks";
export function useCommand() {
  const dispatch = useAppDispatch();
  const redux = useStore<RootState>();
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const csrf = useAppSelector((s) => s.session.data?.csrf ?? "");
  return async function command<T>(
    name: string,
    path: string,
    data: Record<string, unknown> = {},
  ): Promise<T | null> {
    if (!companyId) return null;
    dispatch(actions.setBusy(name));
    dispatch(actions.clearError());
    try {
      const value = await request<T>(
        path,
        { ...data, company_id: companyId },
        csrf,
      );
      if (redux.getState().workspace.companyId !== companyId) return null;
      await (dispatch as AppDispatch)(loadWorkspace(companyId));
      return value;
    } catch (e) {
      if (redux.getState().workspace.companyId === companyId) {
        dispatch(actions.noticeChanged(failure(e).message));
        if (failure(e).status === 401) dispatch({ type: "session/clear" });
      }
      throw e;
    } finally {
      if (redux.getState().workspace.companyId === companyId)
        dispatch(actions.setBusy(null));
    }
  };
}
