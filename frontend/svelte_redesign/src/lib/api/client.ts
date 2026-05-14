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
  return response.json() as Promise<T>;
}
