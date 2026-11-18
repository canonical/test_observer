// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { isFamilyName } from "./types/openapi";

export const SEARCH_FILTER_LIST_KEYS = [
  "families",
  "test_result_statuses",
  "artefacts",
  "artefact_versions",
  "artefact_tracks",
  "environments",
  "test_cases",
  "test_plans",
] as const;

export type SearchFilterListKey = (typeof SEARCH_FILTER_LIST_KEYS)[number];

export interface SearchFilters {
  families: string[];
  test_result_statuses: string[];
  artefacts: string[];
  artefact_versions: string[];
  artefact_tracks: string[];
  environments: string[];
  test_cases: string[];
  test_plans: string[];
  from_date: string | null;
  until_date: string | null;
}

export interface ParsedSearchFilters {
  filters: SearchFilters;
  problems: string[];
}

const RESULT_STATUSES = new Set(["PASSED", "FAILED", "SKIPPED"]);
const PAGINATION_KEYS = new Set(["page", "page_size"]);
const DATE_KEYS = ["from_date", "until_date"] as const;
const KNOWN_KEYS = new Set<string>([
  ...SEARCH_FILTER_LIST_KEYS,
  ...DATE_KEYS,
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
    from_date: null,
    until_date: null,
  };
}

/** Parse only the supported search condition keys; unknown keys fail closed. */
export function parseSearchFilters(
  params: Pick<URLSearchParams, "getAll" | "keys">,
): ParsedSearchFilters {
  const filters = emptySearchFilters();
  const problems: string[] = [];

  for (const key of SEARCH_FILTER_LIST_KEYS) {
    const values = params.getAll(key);
    if (values.some((value) => value.trim() === "")) {
      problems.push(`Invalid ${key}: values must not be empty.`);
    }
    filters[key] = [...new Set(values)];
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

  for (const family of filters.families) {
    if (!isFamilyName(family)) {
      problems.push(`Invalid families: unsupported family value “${family}”.`);
    }
  }
  for (const status of filters.test_result_statuses) {
    if (!RESULT_STATUSES.has(status)) {
      problems.push(
        `Invalid test_result_statuses: unsupported result status “${status}”.`,
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

export function validateSearchFilters(filters: SearchFilters): string[] {
  const params = new URLSearchParams();
  for (const key of SEARCH_FILTER_LIST_KEYS) {
    for (const value of filters[key]) params.append(key, value);
  }
  for (const key of DATE_KEYS) {
    if (filters[key] !== null) params.append(key, filters[key]);
  }
  return parseSearchFilters(params).problems;
}

/** Canonically serialize valid filter state as repeated list-valued keys. */
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

  for (const key of SEARCH_FILTER_LIST_KEYS) {
    for (const value of [...new Set(filters[key])].sort()) {
      params.append(key, value);
    }
  }
  for (const key of DATE_KEYS) {
    const value = filters[key];
    if (value !== null) params.set(key, value);
  }
  return params;
}

export function searchFilterRequestParams(
  filters: SearchFilters,
): URLSearchParams {
  const params = new URLSearchParams();
  for (const key of SEARCH_FILTER_LIST_KEYS) {
    for (const value of filters[key]) params.append(key, value);
  }
  for (const key of DATE_KEYS) {
    const value = filters[key];
    if (value !== null) params.set(key, value);
  }
  return params;
}

export function searchFiltersEqual(
  left: SearchFilters,
  right: SearchFilters,
): boolean {
  return (
    SEARCH_FILTER_LIST_KEYS.every((key) => {
      const leftValues = new Set(left[key]);
      const rightValues = new Set(right[key]);
      return (
        leftValues.size === rightValues.size &&
        [...leftValues].every((value) => rightValues.has(value))
      );
    }) &&
    left.from_date === right.from_date &&
    left.until_date === right.until_date
  );
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

/** Escape a list so each value can be edited on one text-area line. */
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
