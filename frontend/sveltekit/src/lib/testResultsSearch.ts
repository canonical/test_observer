// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { Family } from "$lib/types";
import type { GridFilterState } from "@svgrid/grid";
import type {
  ExecutionMetadata,
  MinimalIssueResponse,
  TestExecutionStatus,
  TestResultStatus,
} from "$lib/types/openapi";
import {
  SEARCH_FILTERS,
  FILTER_DEFINITIONS,
  cloneFilters,
  filterEqual,
  filterValues,
  hasFilters,
  parseFilters,
  type SearchFilters,
  type SearchFilter,
} from "$lib/testResultsFilters";
export * from "$lib/testResultsFilters";

export const RESULT_STATUSES: TestResultStatus[] = [
  "PASSED",
  "FAILED",
  "SKIPPED",
];
export const EXECUTION_STATUSES: TestExecutionStatus[] = [
  "NOT_STARTED",
  "NOT_TESTED",
  "IN_PROGRESS",
  "ENDED_PREMATURELY",
  "FAILED",
  "PASSED",
];
export const DEFAULT_LIMIT = 50;
/** Shared Flutter-compatible filter fields used by bulk/query utilities. */
export const TEST_RESULTS_FILTERS: SearchFilter[] = SEARCH_FILTERS.filter(
  (key) => key !== "execution_is_latest",
);
/** Canonical filters accepted by the Search URL and sent to every API block. */
export const SEARCH_PAGE_FILTERS: SearchFilter[] = [...SEARCH_FILTERS];

type GridFilterKey = SearchFilter | "createdAt";

const GRID_FILTER_KEYS: Record<string, GridFilterKey> = {
  status: "test_result_statuses",
  artefact: "artefacts",
  version: "artefact_versions",
  track: "artefact_tracks",
  environment: "environments",
  testCase: "test_cases",
  testPlan: "test_plans",
  createdAt: "createdAt",
  family: "families",
  stage: "artefact_stages",
  archived: "artefact_is_archived",
  rerunRequested: "rerun_is_requested",
  latestExecution: "execution_is_latest",
  executionStatus: "test_execution_statuses",
  templateId: "template_ids",
  issues: "issues",
  reviewers: "reviewer_ids",
  executionMetadata: "execution_metadata",
};

function mapGridFilter(id: string): GridFilterKey {
  if (Object.hasOwn(GRID_FILTER_KEYS, id)) return GRID_FILTER_KEYS[id];
  if (SEARCH_FILTERS.includes(id as SearchFilter)) return id as SearchFilter;
  throw new Error(`SvGrid reported an unsupported column filter: ${id}.`);
}

function exactGridValues(column: GridFilterState["columns"][number]): string[] {
  if (column.operator !== "equals" || column.valueTo !== undefined)
    throw new Error(
      `Unsupported exact-set filter operator: ${column.operator}.`,
    );
  if (column.selectedValues !== undefined) {
    if (column.value !== "")
      throw new Error("Exact-set filters cannot combine text and selections.");
    return [...column.selectedValues];
  }
  return column.value === "" ? [] : [column.value];
}

function parseGridValues<K extends SearchFilter>(
  key: K,
  values: string[],
): SearchFilters[K] {
  return FILTER_DEFINITIONS[key].parse(values);
}

/**
 * Adapt SvGrid's external filter-state callback into the page's API contract.
 * Set-like fields use exact selections, booleans use equality and Created uses
 * inclusive bounds. Encoded IDs and metadata are carried as values only; this
 * adapter never evaluates a predicate against the loaded grid blocks.
 */
export function searchFiltersFromGridState(
  state: GridFilterState,
  current: SearchFilters,
): SearchFilters {
  if (state.global.trim())
    throw new Error(
      "Global grid search is not supported by the test-results API.",
    );
  if (state.custom && Object.keys(state.custom).length)
    throw new Error(
      "Custom grid filters are not supported by the test-results API.",
    );

  // The currently rendered grid reports its active filters, but not the
  // canonical fields that do not yet have columns. Clear the represented
  // column conditions first while retaining URL-backed conditions outside
  // this grid; any canonical field present in state is still decoded below.
  const next = cloneFilters(current);
  next.test_result_statuses = [];
  next.artefacts = [];
  next.artefact_versions = [];
  next.artefact_tracks = [];
  next.environments = [];
  next.test_cases = [];
  next.test_plans = [];
  next.families = [];
  next.artefact_stages = [];
  next.test_execution_statuses = [];
  next.template_ids = [];
  next.artefact_is_archived = null;
  next.rerun_is_requested = null;
  next.execution_is_latest = null;
  next.issues = [];
  next.reviewer_ids = [];
  next.execution_metadata = [];
  next.from_date = null;
  next.until_date = null;

  const seen = new Set<string>();
  for (const column of state.columns) {
    const filter = mapGridFilter(column.id);
    const fields =
      filter === "createdAt" ? ["from_date", "until_date"] : [filter];
    const duplicate = fields.find((field) => seen.has(field));
    if (duplicate)
      throw new Error(
        `SvGrid reported duplicate filter state for ${duplicate}.`,
      );
    fields.forEach((field) => seen.add(field));

    if (filter === "createdAt") {
      if (column.selectedValues)
        throw new Error("Date filters cannot use selected values.");
      if (
        column.operator === "greaterThan" &&
        column.value &&
        column.valueTo === undefined
      ) {
        next.from_date = column.value as SearchFilters["from_date"];
      } else if (
        column.operator === "lessThan" &&
        column.value &&
        column.valueTo === undefined
      ) {
        next.until_date = column.value as SearchFilters["until_date"];
      } else if (
        column.operator === "between" &&
        column.value &&
        column.valueTo
      ) {
        next.from_date = column.value as SearchFilters["from_date"];
        next.until_date = column.valueTo as SearchFilters["until_date"];
      } else {
        throw new Error(
          `Unsupported Created-date filter operator: ${column.operator}.`,
        );
      }
      continue;
    }

    if (filter === "from_date" || filter === "until_date") {
      if (
        column.operator !== "equals" ||
        column.selectedValues !== undefined ||
        column.valueTo !== undefined
      )
        throw new Error(
          `Unsupported exact date-bound filter operator: ${column.operator}.`,
        );
      next[filter] = (column.value || null) as SearchFilters[typeof filter];
      continue;
    }

    if (FILTER_DEFINITIONS[filter].kind === "boolean") {
      if (column.operator !== "equals" || column.valueTo !== undefined)
        throw new Error(
          `Unsupported boolean filter operator: ${column.operator}.`,
        );
      const values =
        column.selectedValues === undefined
          ? column.value === ""
            ? []
            : [column.value]
          : column.value === ""
            ? [...column.selectedValues]
            : (() => {
                throw new Error(
                  "Boolean filters cannot combine text and selections.",
                );
              })();
      Reflect.set(next, filter, parseGridValues(filter, values));
      continue;
    }

    Reflect.set(next, filter, parseGridValues(filter, exactGridValues(column)));
  }
  return next;
}

export interface AppliedSearch {
  filters: SearchFilters;
  limit: number;
  offset: number;
  hasFilters: boolean;
  problems: string[];
}

export interface SearchTableResult {
  test_result: {
    id: number;
    name: string;
    category: string;
    created_at: string;
    template_id: string;
    status: TestResultStatus;
    issues: { id: number; key: string; title: string }[];
  };
  test_execution: {
    id: number;
    status: TestExecutionStatus;
    environment: { name: string };
    test_plan: string;
    rerun_is_requested: boolean;
    execution_is_latest: boolean;
    execution_metadata: { category: string; value: string }[];
  };
  artefact: {
    id: number;
    name: string;
    version: string;
    track: string;
    family: string;
    stage: string;
    archived: boolean;
    reviewers: { id: number; name: string; launchpad_handle: string | null }[];
  };
  artefact_build: { architecture: string };
}

export interface SearchResultDetails {
  test_result: {
    id: number;
    name: string;
    category: string;
    template_id: string;
    status: TestResultStatus;
    io_log: string;
    issues: {
      issue: Pick<
        MinimalIssueResponse,
        "id" | "source" | "project" | "key" | "title" | "status"
      >;
    }[];
  };
  test_execution: {
    id: number;
    status: TestExecutionStatus;
    environment: { name: string };
    test_plan: string;
    created_at: string;
    execution_metadata: ExecutionMetadata;
  };
  artefact: {
    id: number;
    name: string;
    version: string;
    track: string;
    family: string;
  };
  artefact_build: { architecture: string };
}

export interface SearchTableResponse {
  count: number | null;
  limit: number;
  offset: number;
  rows: SearchTableResult[];
}

/** Flattened data presented by the infinite search grid. */
export interface SearchGridRow extends Record<string, unknown> {
  id: number;
  artefact: string;
  testCase: string;
  category: string;
  status: TestResultStatus;
  execution: number;
  version: string;
  track: string;
  environment: string;
  testPlan: string;
  createdAt: string;
  architecture: string;
  family: string;
  stage: string | null;
  archived: boolean;
  executionStatus: TestExecutionStatus;
  rerunRequested: boolean;
  latestExecution: boolean;
  templateId: string;
  issues: { id: number; key: string; title: string }[];
  reviewers: { id: number; name: string; launchpad_handle: string | null }[];
  executionMetadata: { category: string; value: string }[];
  href: string | null;
}

export function parseSearch(
  params: URLSearchParams,
  families: Family[],
  options: { allowLatest?: boolean } = {},
): AppliedSearch {
  const { filters, problems } = parseFilters(params);
  // `view` is presentation only and never becomes an API filter. An empty
  // search is intentionally valid and requests the recent results page.
  const supported = new Set<string>([
    ...SEARCH_FILTERS,
    "assignee_ids",
    "limit",
    "offset",
    "view",
  ]);
  for (const key of new Set(params.keys())) {
    if (!supported.has(key)) problems.push(`Unsupported URL filter: ${key}.`);
  }
  if (params.has("execution_is_latest") && options.allowLatest === false) {
    problems.push(
      "Latest-execution filtering is unavailable on Search because result rows do not include is_latest.",
    );
  }
  for (const value of filters.families) {
    if (!families.some((family) => family.api_name === value))
      problems.push(`Unknown or unavailable family: ${value}.`);
  }
  for (const value of filters.test_result_statuses) {
    if (!RESULT_STATUSES.some((status) => status === value)) {
      problems.push(`Invalid test result status: ${value}.`);
    }
  }
  for (const value of filters.test_execution_statuses) {
    if (!EXECUTION_STATUSES.some((status) => status === value)) {
      problems.push(`Invalid test execution status: ${value}.`);
    }
  }
  return {
    filters,
    // Legacy page parameters are intentionally ignored by the infinite grid.
    // They are removed from the URL by the route adapter, and can never be
    // added to a block's SvGrid range.
    limit: DEFAULT_LIMIT,
    offset: 0,
    hasFilters: hasFilters(filters),
    problems,
  };
}

/** Parse the shared filter contract, then reject fields not exposed in the
 * current result grid. Other workflows continue using `parseSearch`. */
export function parseSearchPage(
  params: URLSearchParams,
  families: Family[],
): AppliedSearch {
  return parseSearch(params, families);
}

/** Preserve repeated params and validation identity, excluding presentation. */
export function searchQueryString(params: URLSearchParams): string {
  const query = new URLSearchParams(params);
  query.delete("view");
  query.delete("limit");
  query.delete("offset");
  return query.toString();
}

/** The exact, canonical filter conditions shared by every block request. */
export function searchFilterParams(filters: SearchFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const key of SEARCH_FILTERS) {
    for (const value of filterValues(key, filters)) params.append(key, value);
  }
  return params;
}

/**
 * Convert one SvGrid exclusive range into the backend's offset/limit contract.
 * No URL pagination state participates, and an oversized block is rejected
 * instead of accidentally exceeding the endpoint's 1000-row maximum.
 */
export function searchRangeParams(
  filters: SearchFilters,
  startRow: number,
  endRow: number,
): URLSearchParams {
  const limit = endRow - startRow;
  if (
    !Number.isSafeInteger(startRow) ||
    startRow < 0 ||
    !Number.isSafeInteger(endRow) ||
    limit <= 0 ||
    limit > 1000
  ) {
    throw new RangeError("Invalid test result block range.");
  }
  const params = searchFilterParams(filters);
  params.set("offset", String(startRow));
  params.set("limit", String(limit));
  return params;
}

/** Shape one API result for the grid without losing its loaded detail record. */
export function toSearchGridRow(
  result: SearchTableResult,
  families: Family[],
  base: string,
): SearchGridRow {
  return {
    id: result.test_result.id,
    artefact: result.artefact.name,
    testCase: result.test_result.name,
    category: result.test_result.category,
    status: result.test_result.status,
    execution: result.test_execution.id,
    version: result.artefact.version,
    track: result.artefact.track,
    environment: result.test_execution.environment.name,
    testPlan: result.test_execution.test_plan,
    createdAt: result.test_result.created_at,
    architecture: result.artefact_build.architecture,
    // The wire value is the API family name; configure the user-facing label
    // independently so API filters continue to use canonical values.
    family: result.artefact.family,
    // Empty is a configured, explicit stage. A missing value remains distinct
    // and renders as unavailable rather than masquerading as (none).
    stage: Object.hasOwn(result.artefact, "stage")
      ? result.artefact.stage
      : null,
    archived: result.artefact.archived,
    executionStatus: result.test_execution.status,
    rerunRequested: result.test_execution.rerun_is_requested,
    latestExecution: result.test_execution.execution_is_latest,
    templateId: result.test_result.template_id,
    issues: result.test_result.issues.map((issue) => ({ ...issue })),
    reviewers: result.artefact.reviewers.map((reviewer) => ({ ...reviewer })),
    executionMetadata: result.test_execution.execution_metadata.map((pair) => ({
      ...pair,
    })),
    href: viewRunPath(result, families, base),
  };
}

/** Serialize the shared Flutter-compatible filter contract for other consumers. */
export function searchParams(
  filters: SearchFilters,
  limit = DEFAULT_LIMIT,
  offset = 0,
): URLSearchParams {
  const params = new URLSearchParams();
  for (const key of TEST_RESULTS_FILTERS) {
    for (const value of filterValues(key, filters)) params.append(key, value);
  }
  params.set("limit", String(limit));
  if (offset > 0) params.set("offset", String(offset));
  return params;
}

/** Replace only explicitly edited fields (or typed differences for non-UI
 * callers). Untouched malformed/unknown raw constraints must keep blocking.
 * Explicit fixes/clears can replace a malformed field whose typed value is empty. */
export function editedSearchParams(
  filters: SearchFilters,
  source: URLSearchParams,
  editedFields?: readonly SearchFilter[],
): URLSearchParams {
  const params = new URLSearchParams(source);
  const parsedSource = parseFilters(source);
  const restored = parsedSource.filters;
  const changed =
    editedFields ??
    SEARCH_PAGE_FILTERS.filter((key) => !filterEqual(key, filters, restored));
  params.delete("view");
  // Search is an infinite result set: discard legacy page parameters rather
  // than carrying them alongside the grid's range-based offsets.
  params.delete("limit");
  params.delete("offset");
  // Read the legacy alias, but make successful Search writes canonical. Keep
  // malformed reviewer provenance untouched so an unrelated edit cannot turn
  // an invalid condition into a broader query.
  const reviewerInvalid = parsedSource.problems.some((problem) =>
    problem.startsWith("Invalid reviewer_ids:"),
  );
  if (params.has("assignee_ids") && !reviewerInvalid) {
    params.delete("assignee_ids");
    params.delete("reviewer_ids");
    for (const value of filterValues("reviewer_ids", restored))
      params.append("reviewer_ids", value);
  }
  for (const key of changed) {
    params.delete(key);
    if (key === "reviewer_ids") params.delete("assignee_ids");
    for (const value of filterValues(key, filters)) params.append(key, value);
  }
  return params;
}

/** Routes are configuration data, not plurals inferred from an API family. */
export function viewRunPath(
  result:
    | Pick<SearchTableResult, "test_result" | "test_execution" | "artefact">
    | SearchResultDetails,
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
