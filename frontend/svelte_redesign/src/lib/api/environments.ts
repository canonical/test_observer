// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { EnvironmentIssue } from "$lib/types/environment.js";

export function searchEnvironments(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<string[]> {
  const qs = new URLSearchParams(params).toString();
  return apiFetch<string[]>(`/v1/environments?${qs}`, {}, fetchFn);
}

export function getEnvironmentIssues(
  fetchFn: typeof fetch = fetch,
): Promise<EnvironmentIssue[]> {
  return apiFetch<EnvironmentIssue[]>("/v1/environments/reported-issues", {}, fetchFn);
}

export function createEnvironmentIssue(
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<EnvironmentIssue> {
  return apiFetch<EnvironmentIssue>("/v1/environments/reported-issues", {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function updateEnvironmentIssue(
  id: number,
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<EnvironmentIssue> {
  return apiFetch<EnvironmentIssue>(`/v1/environments/reported-issues/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function deleteEnvironmentIssue(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>(`/v1/environments/reported-issues/${id}`, {
    method: "DELETE",
  }, fetchFn);
}
