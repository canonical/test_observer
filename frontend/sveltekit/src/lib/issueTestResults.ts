// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import {
  DEFAULT_LIMIT,
  emptyFilters,
  type AppliedSearch,
} from "$lib/testResultsSearch";

/** An issue query has no URL/editor input. Even a bad caller must fail closed,
 * never fall back to the unfiltered recent-results query. */
export function issueResultsQuery(issueId: number): AppliedSearch {
  const filters = emptyFilters();
  const valid = Number.isSafeInteger(issueId) && issueId > 0;
  filters.issues = valid ? [issueId] : [];
  // Freeze the condition as well as its containers: no grid/filter consumer can
  // replace the pinned issue or append another ID between block requests.
  for (const value of Object.values(filters))
    if (Array.isArray(value)) Object.freeze(value);
  Object.freeze(filters);
  return Object.freeze({
    filters,
    limit: DEFAULT_LIMIT,
    offset: 0,
    hasFilters: true,
    problems: valid ? [] : ["A positive, safe issue ID is required."],
  });
}
