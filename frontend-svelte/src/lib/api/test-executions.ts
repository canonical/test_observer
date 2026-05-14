// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { TestResult } from "$lib/types/test-result.js";
import type { TestEvent, RerunRequest } from "$lib/types/test-execution.js";

export function startTestExecution(
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>("/v1/test-executions/start-test", {
    method: "PUT",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function createReruns(
  data: RerunRequest[],
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>("/v1/test-executions/reruns", {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function deleteReruns(
  data: RerunRequest[],
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>("/v1/test-executions/reruns", {
    method: "DELETE",
    body: JSON.stringify(data),
  }, fetchFn);
}

export function getTestExecutionResults(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<TestResult[]> {
  return apiFetch<TestResult[]>(`/v1/test-executions/${id}/test-results`, {}, fetchFn);
}

export function getTestExecutionEvents(
  id: number,
  fetchFn: typeof fetch = fetch,
): Promise<TestEvent[]> {
  return apiFetch<TestEvent[]>(`/v1/test-executions/${id}/status_update`, {}, fetchFn);
}
