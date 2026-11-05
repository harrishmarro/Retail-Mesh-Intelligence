import type { Failure } from "./types";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function request<T>(
  path: string,
  data?: unknown,
  csrf = "",
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, {
    method: data === undefined ? "GET" : "POST",
    credentials: "same-origin",
    signal,
    headers:
      data === undefined
        ? {}
        : { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  const payload = await response.json();
  if (!response.ok)
    throw new ApiError(
      payload.error || "The request could not be completed.",
      response.status,
    );
  return payload as T;
}
export function failure(error: unknown): Failure {
  return {
    message:
      error instanceof Error
        ? error.message
        : "Something went wrong. Try again.",
    status: error instanceof ApiError ? error.status : 0,
  };
}
