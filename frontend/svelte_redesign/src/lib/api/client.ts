// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:30000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    body: string,
  ) {
    super(`API error ${status}: ${body}`);
  }
}

/** Convert a single snake_case key to camelCase. */
function snakeToCamel(key: string): string {
  return key.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
}

/** Recursively convert all object keys from snake_case to camelCase. */
function deepCamelCase<T>(val: unknown): T {
  if (Array.isArray(val)) {
    return val.map(deepCamelCase) as T;
  }
  if (val !== null && typeof val === "object") {
    return Object.fromEntries(
      Object.entries(val as Record<string, unknown>).map(([k, v]) => [
        snakeToCamel(k),
        deepCamelCase(v),
      ]),
    ) as T;
  }
  return val as T;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  fetchFn: typeof fetch = fetch,
): Promise<T> {
  const response = await fetchFn(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": "1",
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  const raw: unknown = await response.json();
  return deepCamelCase<T>(raw);
}
