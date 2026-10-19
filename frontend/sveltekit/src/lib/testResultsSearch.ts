// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { Family } from "$lib/types";
import type { TestResult } from "$lib/types/artefact-page";
import type {
  ArtefactResponse,
  ArtefactBuildMinimalResponse,
  TestExecutionResponse,
  TestResultStatus,
} from "$lib/types/openapi";

export const SEARCH_FILTERS = [
  "families",
  "test_result_statuses",
  "artefacts",
  "artefact_versions",
  "artefact_tracks",
  "environments",
  "test_plans",
  "test_cases",
] as const;
export type SearchFilter = (typeof SEARCH_FILTERS)[number];
export type SearchFilters = Record<SearchFilter, string[]>;
export const RESULT_STATUSES: TestResultStatus[] = [
  "PASSED",
  "FAILED",
  "SKIPPED",
];
export const DEFAULT_LIMIT = 50;

export interface AppliedSearch {
  filters: SearchFilters;
  limit: number;
  offset: number;
  hasFilters: boolean;
  problems: string[];
}

export interface SearchResult {
  test_result: TestResult;
  test_execution: TestExecutionResponse;
  artefact: ArtefactResponse;
  artefact_build: ArtefactBuildMinimalResponse;
}

export interface SearchResponse {
  count: number;
  limit: number;
  offset: number;
  test_results: SearchResult[];
}

/** Flutter-compatible URL lists; API requests use repeated keys instead. */
export function listValues(values: string[]): string[] {
  return [
    ...new Set(
      values
        .flatMap((v) => v.split(","))
        .map((v) => v.trim())
        .filter(Boolean),
    ),
  ];
}

export function emptyFilters(): SearchFilters {
  return {
    families: [],
    test_result_statuses: [],
    artefacts: [],
    artefact_versions: [],
    artefact_tracks: [],
    environments: [],
    test_plans: [],
    test_cases: [],
  };
}

export function parseSearch(
  params: URLSearchParams,
  families: Family[],
): AppliedSearch {
  const filters = emptyFilters();
  const problems: string[] = [];
  // `view` is presentation only. It must never become an API filter or make
  // an otherwise empty search eligible for an unfiltered backend request.
  const supported = new Set<string>([
    ...SEARCH_FILTERS,
    "limit",
    "offset",
    "view",
  ]);
  for (const key of new Set(params.keys())) {
    if (!supported.has(key)) problems.push(`Unsupported URL filter: ${key}.`);
  }
  for (const key of SEARCH_FILTERS)
    filters[key] = listValues(params.getAll(key));
  for (const value of filters.families) {
    if (!families.some((f) => f.api_name === value)) {
      problems.push(`Unknown or unavailable family: ${value}.`);
    }
  }
  for (const value of filters.test_result_statuses) {
    if (!RESULT_STATUSES.some((status) => status === value)) {
      problems.push(`Invalid test result status: ${value}.`);
    }
  }
  function integer(
    key: string,
    fallback: number,
    minimum: number,
    maximum: number,
  ): number {
    const values = params.getAll(key);
    if (!values.length) return fallback;
    const value = values[0];
    const number = Number(value);
    if (
      values.length !== 1 ||
      !/^\d+$/.test(value) ||
      !Number.isSafeInteger(number) ||
      number < minimum ||
      number > maximum
    ) {
      problems.push(`Invalid ${key} pagination value.`);
      return fallback;
    }
    return number;
  }
  return {
    filters,
    limit: integer("limit", DEFAULT_LIMIT, 1, 1000),
    offset: integer("offset", 0, 0, Number.MAX_SAFE_INTEGER),
    hasFilters: SEARCH_FILTERS.some((key) => filters[key].length > 0),
    problems,
  };
}

/** Preserve repeated params and validation identity, excluding presentation. */
export function searchQueryString(params: URLSearchParams): string {
  const query = new URLSearchParams(params);
  query.delete("view");
  return query.toString();
}

/** Also used for the applied URL, retaining supported Flutter query names. */
export function searchParams(
  filters: SearchFilters,
  limit = DEFAULT_LIMIT,
  offset = 0,
): URLSearchParams {
  const params = new URLSearchParams();
  for (const key of SEARCH_FILTERS) {
    for (const value of filters[key]) params.append(key, value);
  }
  params.set("limit", String(limit));
  if (offset > 0) params.set("offset", String(offset));
  return params;
}

/** Routes are configuration data, not plurals inferred from an API family. */
export function viewRunPath(
  result: SearchResult,
  families: Family[],
  base: string,
): string | null {
  const family = families.find((f) => f.api_name === result.artefact.family);
  if (!family) return null;
  const params = new URLSearchParams({
    testExecutionId: String(result.test_execution.id),
    testResultId: String(result.test_result.id),
  });
  return `${base}/${encodeURIComponent(family.name)}/${result.artefact.id}?${params}`;
}
