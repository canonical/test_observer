// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import {
  DEFAULT_LIMIT,
  emptyFilters,
  type AppliedSearch,
  type SearchFilters,
  FILTER_DEFINITIONS,
  compareInstants,
} from "$lib/testResultsSearch";

export const ISSUE_RESULT_LISTS = [
  "families",
  "artefacts",
  "environments",
  "test_cases",
] as const;
export type IssueResultList = (typeof ISSUE_RESULT_LISTS)[number];
/** Raw date text is intentional: invalid edits must not reuse a previous valid
 * bound or silently remove it. Only a validated snapshot may be applied. */
export type IssueResultFilters = Record<IssueResultList, string[]> & {
  from_date: string;
  until_date: string;
};

export function emptyIssueResultFilters(): IssueResultFilters {
  return {
    families: [],
    artefacts: [],
    environments: [],
    test_cases: [],
    from_date: "",
    until_date: "",
  };
}

export function issueResultGroupCount(filters: SearchFilters): number {
  return (
    ISSUE_RESULT_LISTS.filter((key) => filters[key].length > 0).length +
    Number(filters.from_date !== null || filters.until_date !== null)
  );
}

/** Allowlist only the issue page's optional dimensions. Runtime validation also
 * protects the pinned ID from malformed/untyped callers. Invalid input blocks
 * reads; it never falls back to a broader issue or recent-results query. */
export function issueResultsQuery(
  issueId: number,
  optional: Partial<IssueResultFilters> | null = {},
): AppliedSearch {
  const filters = emptyFilters();
  const problems: string[] = [];
  const valid = Number.isSafeInteger(issueId) && issueId > 0;
  if (!valid) problems.push("A positive, safe issue ID is required.");
  filters.issues = valid ? [issueId] : [];
  if (!optional || typeof optional !== "object" || Array.isArray(optional)) {
    problems.push(
      "Optional filters must be an object. Clear optional drafts to repair them.",
    );
  } else {
    for (const key of Object.keys(optional))
      if (![...ISSUE_RESULT_LISTS, "from_date", "until_date"].includes(key))
        problems.push(
          `Unsupported optional filter: ${key}. Clear optional drafts to remove it.`,
        );
    for (const key of ISSUE_RESULT_LISTS) {
      const values = optional[key];
      if (values === undefined) continue;
      if (
        !Array.isArray(values) ||
        values.some(
          (value) =>
            typeof value !== "string" ||
            value.length === 0 ||
            value !== value.trim() ||
            value.includes(","),
        )
      ) {
        problems.push(
          `Invalid ${FILTER_DEFINITIONS[key].label}: select exact nonempty values without commas or surrounding whitespace.`,
        );
      } else {
        filters[key] = FILTER_DEFINITIONS[key].parse(values);
      }
    }
    for (const key of ["from_date", "until_date"] as const) {
      const text = optional[key];
      if (text === undefined || text === "") continue;
      try {
        if (typeof text !== "string")
          throw new Error("Expected one ISO timestamp.");
        filters[key] = FILTER_DEFINITIONS[key].parse([text]);
      } catch (cause) {
        problems.push(
          `Invalid ${FILTER_DEFINITIONS[key].label}: ${cause instanceof Error ? cause.message : "Invalid timestamp."} Correct or clear this bound before applying.`,
        );
      }
    }
    if (
      filters.from_date &&
      filters.until_date &&
      compareInstants(filters.from_date, filters.until_date) > 0
    )
      problems.push(
        "From must not be after Until (inclusive bounds). Correct or clear a bound before applying.",
      );
  }
  // Freeze the condition as well as its containers: no grid/filter consumer can
  // replace the pinned issue or append another ID between block requests.
  for (const value of Object.values(filters))
    if (Array.isArray(value)) Object.freeze(value);
  Object.freeze(filters);
  Object.freeze(problems);
  return Object.freeze({
    filters,
    limit: DEFAULT_LIMIT,
    offset: 0,
    hasFilters: true,
    problems,
  });
}
