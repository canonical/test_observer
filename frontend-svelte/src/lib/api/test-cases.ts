// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { TestIssue } from "$lib/types/test-result.js";

export function getTestIssues(
  fetchFn: typeof fetch = fetch,
): Promise<TestIssue[]> {
  return apiFetch<TestIssue[]>("/v1/test-cases/reported-issues", {}, fetchFn);
}

export function createTestIssue(
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<TestIssue> {
  return apiFetch<TestIssue>("/v1/test-cases/reported-issues", {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function updateTestIssue(
  id: number,
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<TestIssue> {
  return apiFetch<TestIssue>(`/v1/test-cases/reported-issues/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function deleteTestIssue(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>(`/v1/test-cases/reported-issues/${id}`, {
    method: "DELETE",
  }, fetchFn);
}

export function searchTestCases(
  params: Record<string, string>,
  fetchFn: typeof fetch = fetch,
): Promise<string[]> {
  const qs = new URLSearchParams(params).toString();
  return apiFetch<string[]>(`/v1/test-cases?${qs}`, {}, fetchFn);
}
