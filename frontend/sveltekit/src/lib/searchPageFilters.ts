// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { TestExecutionStatus } from "$lib/types/openapi";

export const SEARCH_FILTER_LIST_KEYS = [
  "families",
  "test_result_statuses",
  "artefacts",
  "artefact_versions",
  "artefact_tracks",
  "environments",
  "test_cases",
  "test_plans",
  "artefact_stages",
  "test_execution_statuses",
  "template_ids",
] as const;

export type SearchFilterListKey = (typeof SEARCH_FILTER_LIST_KEYS)[number];
export type SearchIdFilter = number[] | "any" | "none";
export interface SearchMetadataCondition {
  category: string;
  values: string[];
}

export interface SearchFilters {
  families: string[];
  test_result_statuses: string[];
  artefacts: string[];
  artefact_versions: string[];
  artefact_tracks: string[];
  environments: string[];
  test_cases: string[];
  test_plans: string[];
  artefact_stages: string[];
  test_execution_statuses: TestExecutionStatus[];
  template_ids: string[];
  artefact_is_archived: boolean | null;
  rerun_is_requested: boolean | null;
  execution_is_latest: boolean | null;
  issues: SearchIdFilter;
  reviewer_ids: SearchIdFilter;
  execution_metadata: SearchMetadataCondition[];
  from_date: string | null;
  until_date: string | null;
}

export interface ParsedSearchFilters {
  filters: SearchFilters;
  problems: string[];
}

const RESULT_STATUSES = new Set(["PASSED", "FAILED", "SKIPPED"]);
const EXECUTION_STATUSES = new Set<TestExecutionStatus>([
  "NOT_STARTED",
  "NOT_TESTED",
  "IN_PROGRESS",
  "ENDED_PREMATURELY",
  "FAILED",
  "PASSED",
]);
const PAGINATION_KEYS = new Set(["page", "page_size"]);
const DATE_KEYS = ["from_date", "until_date"] as const;
const BOOLEAN_KEYS = [
  "artefact_is_archived",
  "rerun_is_requested",
  "execution_is_latest",
] as const;
const ID_KEYS = ["issues", "reviewer_ids"] as const;
const KNOWN_KEYS = new Set<string>([
  ...SEARCH_FILTER_LIST_KEYS,
  ...DATE_KEYS,
  ...BOOLEAN_KEYS,
  ...ID_KEYS,
  "execution_metadata",
  ...PAGINATION_KEYS,
]);

export function emptySearchFilters(): SearchFilters {
  return {
    families: [],
    test_result_statuses: [],
    artefacts: [],
    artefact_versions: [],
    artefact_tracks: [],
    environments: [],
    test_cases: [],
    test_plans: [],
    artefact_stages: [],
    test_execution_statuses: [],
    template_ids: [],
    artefact_is_archived: null,
    rerun_is_requested: null,
    execution_is_latest: null,
    issues: [],
    reviewer_ids: [],
    execution_metadata: [],
    from_date: null,
    until_date: null,
  };
}

/** Parse supported conditions and fail closed on every unknown or malformed key. */
export function parseSearchFilters(
  params: Pick<URLSearchParams, "getAll" | "keys">,
  familyNames?: readonly string[],
): ParsedSearchFilters {
  const filters = emptySearchFilters();
  const listFilters = filters as unknown as Record<
    SearchFilterListKey,
    string[]
  >;
  const problems: string[] = [];

  for (const key of SEARCH_FILTER_LIST_KEYS) {
    const values = params.getAll(key);
    if (
      values.some(
        (value) =>
          value.trim() === "" && !(key === "artefact_stages" && value === ""),
      )
    ) {
      problems.push(`Invalid ${key}: values must not be empty.`);
    }
    listFilters[key] = [...new Set(values)];
  }

  for (const key of BOOLEAN_KEYS) {
    const values = params.getAll(key);
    if (values.length > 1) {
      problems.push(
        `Invalid ${key}: provide at most one lowercase true or false value.`,
      );
      continue;
    }
    if (!values.length) continue;
    if (values[0] !== "true" && values[0] !== "false") {
      problems.push(`Invalid ${key}: expected lowercase true or false.`);
      continue;
    }
    filters[key] = values[0] === "true";
  }

  for (const key of ID_KEYS) {
    const values = params.getAll(key);
    if (!values.length) continue;
    if (values.length === 1 && (values[0] === "any" || values[0] === "none")) {
      filters[key] = values[0];
      continue;
    }
    if (values.some((value) => value === "any" || value === "none")) {
      problems.push(`Invalid ${key}: any/none must be the sole value.`);
      continue;
    }
    const ids: number[] = [];
    let invalid = false;
    for (const value of values) {
      if (!/^[1-9]\d*$/.test(value)) {
        invalid = true;
        break;
      }
      const id = Number(value);
      if (!Number.isSafeInteger(id) || id <= 0 || id > 2_147_483_647) {
        invalid = true;
        break;
      }
      ids.push(id);
    }
    if (invalid)
      problems.push(
        `Invalid ${key}: use positive supported integer IDs, or only any/none.`,
      );
    else filters[key] = [...new Set(ids)];
  }

  const metadataValues = params.getAll("execution_metadata");
  if (metadataValues.length) {
    try {
      filters.execution_metadata = parseExecutionMetadata(metadataValues);
    } catch (error) {
      problems.push(
        `Invalid execution_metadata: ${error instanceof Error ? error.message : "Invalid metadata pair."}`,
      );
    }
  }

  for (const key of DATE_KEYS) {
    const values = params.getAll(key);
    if (values.length > 1) {
      problems.push(`Invalid ${key}: provide at most one timestamp.`);
    }
    const value = values.length === 0 ? null : values[0];
    filters[key] = value;
    if (value !== null && parseUtcTimestamp(value) === null) {
      problems.push(`Invalid ${key}: expected a valid ISO-8601 UTC timestamp.`);
    }
  }

  const fromTimestamp =
    filters.from_date === null ? null : parseUtcTimestamp(filters.from_date);
  const untilTimestamp =
    filters.until_date === null ? null : parseUtcTimestamp(filters.until_date);
  if (
    fromTimestamp !== null &&
    untilTimestamp !== null &&
    fromTimestamp > untilTimestamp
  ) {
    problems.push(
      "Invalid date range: Created from must not be after Created to.",
    );
  }

  if (familyNames !== undefined) {
    const knownFamilyNames = new Set(familyNames);
    for (const family of filters.families) {
      if (!knownFamilyNames.has(family)) {
        problems.push(
          `Invalid families: unsupported family value “${family}”.`,
        );
      }
    }
  }
  for (const status of filters.test_result_statuses) {
    if (!RESULT_STATUSES.has(status)) {
      problems.push(
        `Invalid test_result_statuses: unsupported result status “${status}”.`,
      );
    }
  }
  for (const status of filters.test_execution_statuses) {
    if (!EXECUTION_STATUSES.has(status)) {
      problems.push(
        `Invalid test_execution_statuses: unsupported execution status “${status}”.`,
      );
    }
  }

  const unknown = [
    ...new Set([...params.keys()].filter((key) => !KNOWN_KEYS.has(key))),
  ].sort();
  for (const key of unknown) {
    problems.push(
      `Unsupported search parameter: ${key}. Clear all filters to remove it.`,
    );
  }

  return { filters, problems };
}

export function validateSearchFilters(
  filters: SearchFilters,
  familyNames?: readonly string[],
): string[] {
  const params = searchFilterRequestParams(filters);
  return parseSearchFilters(params, familyNames).problems;
}

/** Canonically serialize valid filter state. Lists remain repeated exact values. */
export function serializeSearchFilters(
  filters: SearchFilters,
  source: Pick<URLSearchParams, "getAll"> = new URLSearchParams(),
): URLSearchParams {
  const problems = validateSearchFilters(filters);
  if (problems.length) throw new RangeError(problems.join(" "));

  const params = new URLSearchParams();
  const pageSizes = source.getAll("page_size");
  if (
    pageSizes.length === 1 &&
    ["25", "50", "100"].includes(pageSizes[0] ?? "")
  ) {
    params.set("page_size", pageSizes[0] ?? "50");
  }
  params.set("page", "1");
  appendFilterParams(params, filters);
  return params;
}

export function searchFilterRequestParams(
  filters: SearchFilters,
): URLSearchParams {
  const params = new URLSearchParams();
  appendFilterParams(params, filters);
  return params;
}

function appendFilterParams(
  params: URLSearchParams,
  filters: SearchFilters,
): void {
  for (const key of SEARCH_FILTER_LIST_KEYS) {
    const values = [...new Set(filters[key])].sort();
    for (const value of values) params.append(key, value);
  }
  for (const key of BOOLEAN_KEYS) {
    const value = filters[key];
    if (value !== null) params.set(key, String(value));
  }
  for (const key of ID_KEYS) {
    const value = filters[key];
    if (Array.isArray(value)) {
      for (const id of [...new Set(value)].sort((a, b) => a - b))
        params.append(key, String(id));
    } else {
      params.set(key, value);
    }
  }
  for (const pair of serializeExecutionMetadata(filters.execution_metadata)) {
    params.append("execution_metadata", pair);
  }
  for (const key of DATE_KEYS) {
    const value = filters[key];
    if (value !== null) params.set(key, value);
  }
}

export function searchFiltersEqual(
  left: SearchFilters,
  right: SearchFilters,
): boolean {
  const leftParams = searchFilterRequestParams(left);
  const rightParams = searchFilterRequestParams(right);
  const keys = [...KNOWN_KEYS]
    .filter((key) => !PAGINATION_KEYS.has(key))
    .sort();
  return keys.every((key) => {
    const a = leftParams.getAll(key).sort();
    const b = rightParams.getAll(key).sort();
    return (
      a.length === b.length && a.every((value, index) => value === b[index])
    );
  });
}

export function searchFilterQueryKey(
  params: Pick<URLSearchParams, "entries">,
): string {
  const entries = [...params.entries()]
    .filter(([key]) => !PAGINATION_KEYS.has(key))
    .sort(([leftKey, leftValue], [rightKey, rightValue]) =>
      leftKey === rightKey
        ? leftValue.localeCompare(rightValue)
        : leftKey.localeCompare(rightKey),
    );
  return new URLSearchParams(entries).toString();
}

export function splitSearchFilterText(text: string): string[] {
  return [
    ...new Set(
      text
        .split(/\r?\n/)
        .filter((value) => value !== "")
        .map(unescapeSearchFilterValue),
    ),
  ];
}

/** Escape list values for the existing one-value-per-line draft controls. */
export function formatSearchFilterText(values: readonly string[]): string {
  return values
    .map((value) =>
      value
        .replaceAll("\\", "\\\\")
        .replaceAll("\r", "\\r")
        .replaceAll("\n", "\\n"),
    )
    .join("\n");
}

function unescapeSearchFilterValue(value: string): string {
  let result = "";
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (character !== "\\" || index + 1 >= value.length) {
      result += character;
      continue;
    }
    const escaped = value[index + 1];
    if (escaped === "n") result += "\n";
    else if (escaped === "r") result += "\r";
    else if (escaped === "\\") result += "\\";
    else result += `\\${escaped}`;
    index += 1;
  }
  return result;
}

export function encodeMetadataPart(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function decodeMetadataPart(value: string): string {
  if (
    !value ||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
      value,
    )
  ) {
    throw new Error(
      "expected canonical padded Base64 UTF-8 category:value pairs.",
    );
  }
  const binary = atob(value);
  if (btoa(binary) !== value)
    throw new Error("expected canonical padded Base64 encoding.");
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(
    bytes,
  );
}

function validateMetadataPart(value: string): void {
  const length = Array.from(value).length;
  if (length < 1 || length > 200) {
    throw new Error(
      "metadata categories and values must contain 1–200 characters.",
    );
  }
}

function parseExecutionMetadata(values: string[]): SearchMetadataCondition[] {
  const grouped = new Map<string, Set<string>>();
  for (const pair of values) {
    const parts = pair.split(":");
    if (parts.length !== 2)
      throw new Error("expected Base64 UTF-8 category:value pairs.");
    const category = decodeMetadataPart(parts[0] ?? "");
    const value = decodeMetadataPart(parts[1] ?? "");
    validateMetadataPart(category);
    validateMetadataPart(value);
    const bucket = grouped.get(category) ?? new Set<string>();
    bucket.add(value);
    grouped.set(category, bucket);
  }
  return [...grouped].map(([category, items]) => ({
    category,
    values: [...items],
  }));
}

function serializeExecutionMetadata(
  conditions: SearchMetadataCondition[],
): string[] {
  return conditions
    .flatMap(({ category, values }) =>
      [...new Set(values)].map(
        (value) =>
          `${encodeMetadataPart(category)}:${encodeMetadataPart(value)}`,
      ),
    )
    .sort();
}

function parseUtcTimestamp(value: string): number | null {
  if (
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(
      value,
    )
  )
    return null;
  const date = new Date(value);
  const timestamp = date.getTime();
  if (!Number.isFinite(timestamp)) return null;
  const datePart = value.slice(0, 10);
  const calendarDate = new Date(`${datePart}T00:00:00Z`);
  if (calendarDate.toISOString().slice(0, 10) !== datePart) return null;
  return timestamp;
}
