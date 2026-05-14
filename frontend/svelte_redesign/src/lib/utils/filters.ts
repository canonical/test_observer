// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { TestResultsFilters, IntListFilter } from "$lib/types/filters.js";
import type { TestResultStatus } from "$lib/types/test-result.js";

function encodeIntListFilter(key: string, filter: IntListFilter, params: URLSearchParams): void {
  if (filter.type === "any") {
    params.set(key, "any");
  } else if (filter.type === "none") {
    params.set(key, "none");
  } else {
    for (const v of filter.values) {
      params.append(key, String(v));
    }
  }
}

function decodeIntListFilter(key: string, params: URLSearchParams): IntListFilter {
  const raw = params.getAll(key);
  if (raw.length === 1 && raw[0] === "any") return { type: "any" };
  if (raw.length === 1 && raw[0] === "none") return { type: "none" };
  if (raw.length === 0) return { type: "any" };
  return { type: "list", values: raw.map(Number).filter((n) => !Number.isNaN(n)) };
}

export function filtersToSearchParams(filters: TestResultsFilters): URLSearchParams {
  const params = new URLSearchParams();

  for (const f of filters.families) params.append("families", f);
  for (const s of filters.testResultStatuses) params.append("testResultStatuses", s);
  for (const a of filters.artefacts) params.append("artefacts", a);
  for (const e of filters.environments) params.append("environments", e);
  for (const t of filters.testCases) params.append("testCases", t);
  for (const t of filters.templateIds) params.append("templateIds", t);

  if (filters.artefactIsArchived !== undefined) {
    params.set("artefactIsArchived", String(filters.artefactIsArchived));
  }
  if (filters.rerunIsRequested !== undefined) {
    params.set("rerunIsRequested", String(filters.rerunIsRequested));
  }
  if (filters.executionIsLatest !== undefined) {
    params.set("executionIsLatest", String(filters.executionIsLatest));
  }
  if (filters.fromDate) params.set("fromDate", filters.fromDate);
  if (filters.untilDate) params.set("untilDate", filters.untilDate);
  if (filters.offset !== undefined) params.set("offset", String(filters.offset));
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));

  encodeIntListFilter("issues", filters.issues, params);
  encodeIntListFilter("assignees", filters.assignees, params);

  return params;
}

export function searchParamsToFilters(params: URLSearchParams): TestResultsFilters {
  return {
    families: params.getAll("families"),
    testResultStatuses: params.getAll("testResultStatuses") as TestResultStatus[],
    artefacts: params.getAll("artefacts"),
    environments: params.getAll("environments"),
    testCases: params.getAll("testCases"),
    templateIds: params.getAll("templateIds"),
    executionMetadata: { data: {} },
    artefactIsArchived: params.has("artefactIsArchived")
      ? params.get("artefactIsArchived") === "true"
      : undefined,
    rerunIsRequested: params.has("rerunIsRequested")
      ? params.get("rerunIsRequested") === "true"
      : undefined,
    executionIsLatest: params.has("executionIsLatest")
      ? params.get("executionIsLatest") === "true"
      : undefined,
    fromDate: params.get("fromDate") ?? undefined,
    untilDate: params.get("untilDate") ?? undefined,
    offset: params.has("offset") ? Number(params.get("offset")) : undefined,
    limit: params.has("limit") ? Number(params.get("limit")) : undefined,
    issues: decodeIntListFilter("issues", params),
    assignees: decodeIntListFilter("assignees", params),
  };
}
