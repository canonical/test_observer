// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { apiFetch } from "./client.js";
import type { TestResultsSearchResult } from "$lib/types/test-result.js";
import type { TestResultsFilters } from "$lib/types/filters.js";
import { filtersToSearchParams } from "$lib/utils/filters.js";

export function searchTestResults(
  filters: TestResultsFilters,
  fetchFn: typeof fetch = fetch,
): Promise<TestResultsSearchResult> {
  const qs = filtersToSearchParams(filters).toString();
  const path = qs ? `/v1/test-results?${qs}` : "/v1/test-results";
  return apiFetch<TestResultsSearchResult>(path, {
    method: "GET",
  }, fetchFn);
}

export function submitTestResult(
  testExecutionId: number,
  data: Record<string, unknown>,
  fetchFn: typeof fetch = fetch,
): Promise<void> {
  return apiFetch<void>(`/v1/test-executions/${testExecutionId}/test-results`, {
    method: "POST",
    body: JSON.stringify(data),
  }, fetchFn);
}
