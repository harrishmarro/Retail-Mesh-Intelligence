import { useEffect, useCallback } from "react";
import { useAppDispatch, useAppSelector } from "./hooks";
import { loadResource } from "./store";
import type { Resource } from "./types";
export function useWorkspaceResource<T>(resource: Resource) {
  const dispatch = useAppDispatch();
  const companyId = useAppSelector((s) => s.workspace.companyId);
  const value = useAppSelector((s) => s.workspace.resources[resource]);
  useEffect(() => {
    if (!companyId) return;
    const task = dispatch(loadResource({ companyId, resource }));
    return () => task.abort();
  }, [dispatch, companyId, resource]);
  const reload = useCallback(
    () =>
      companyId ? dispatch(loadResource({ companyId, resource })) : undefined,
    [dispatch, companyId, resource],
  );
  return { ...value, data: value.data as T | null, reload, companyId };
}
