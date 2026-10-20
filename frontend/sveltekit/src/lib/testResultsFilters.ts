// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

/* eslint-disable @typescript-eslint/no-unnecessary-type-parameters -- Generic
 * keys preserve the correlation between a field and its codec in indexed calls
 * and assignments. A union key would require an impossible intersection. */

/** Backend filter values, independent of editor controls and hydrated labels. */
export type IdFilter = number[] | "any" | "none";
export interface MetadataCondition {
  category: string;
  values: string[];
}
export type IsoInstant = string & { readonly __isoInstant: unique symbol };

export interface SearchFilters {
  families: string[];
  test_result_statuses: string[];
  artefacts: string[];
  artefact_versions: string[];
  artefact_tracks: string[];
  environments: string[];
  test_plans: string[];
  test_cases: string[];
  artefact_stages: string[];
  artefact_is_archived: boolean | null;
  rerun_is_requested: boolean | null;
  execution_is_latest: boolean | null;
  issues: IdFilter;
  reviewer_ids: IdFilter;
  execution_metadata: MetadataCondition[];
  from_date: IsoInstant | null;
  until_date: IsoInstant | null;
  template_ids: string[];
}
export type SearchFilter = keyof SearchFilters;

/** Only these fields have editors today. The other contracts are URL-only. */
export const EDITABLE_SEARCH_FILTERS = [
  "families",
  "test_result_statuses",
  "artefacts",
  "artefact_versions",
  "artefact_tracks",
  "environments",
  "test_plans",
  "test_cases",
] as const satisfies readonly SearchFilter[];
export type EditableSearchFilter = (typeof EDITABLE_SEARCH_FILTERS)[number];

interface FilterDefinition<T> {
  label: string;
  kind: "list" | "boolean" | "ids" | "metadata" | "instant";
  empty: () => T;
  parse: (values: string[]) => T;
  serialize: (value: T) => string[];
  clone: (value: T) => T;
}

/** Flutter-compatible page lists; API requests always use repeated keys. */
export function listValues(values: string[], keepEmpty = false): string[] {
  return [
    ...new Set(
      values
        .flatMap((value) => value.split(","))
        .map((value) => value.trim())
        .filter((value) => keepEmpty || value !== ""),
    ),
  ];
}

function list(label: string, keepEmpty = false): FilterDefinition<string[]> {
  return {
    label,
    kind: "list",
    empty: () => [],
    parse: (values) => listValues(values, keepEmpty),
    serialize: (values) => [...values],
    clone: (values) => [...values],
  };
}

function boolean(label: string): FilterDefinition<boolean | null> {
  return {
    label,
    kind: "boolean",
    empty: () => null,
    parse(values) {
      if (!values.length) return null;
      if (values.length !== 1 || !/^(true|false)$/i.test(values[0]))
        throw new Error("Expected one true or false value.");
      return values[0].toLowerCase() === "true";
    },
    serialize: (value) => (value === null ? [] : [String(value)]),
    clone: (value) => value,
  };
}

function ids(label: string): FilterDefinition<IdFilter> {
  return {
    label,
    kind: "ids",
    empty: () => [],
    parse(input) {
      const values = listValues(input, true);
      if (values.length === 1 && (values[0] === "any" || values[0] === "none"))
        return values[0];
      if (
        values.some(
          (value) =>
            !/^\d+$/.test(value) ||
            !Number.isSafeInteger(Number(value)) ||
            Number(value) <= 0,
        )
      )
        throw new Error("Use positive integer IDs, or only 'any' or 'none'.");
      return [...new Set(values.map(Number))];
    },
    serialize: (value) => (Array.isArray(value) ? value.map(String) : [value]),
    clone: (value) => (Array.isArray(value) ? [...value] : value),
  };
}

/** Standard padded Base64 of UTF-8, NOT the presentation view's base64url. */
export function encodeMetadataPart(value: string): string {
  let binary = "";
  for (const byte of new TextEncoder().encode(value))
    binary += String.fromCharCode(byte);
  return btoa(binary);
}

function decodeMetadataPart(value: string): string {
  if (
    !value ||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
      value,
    )
  )
    throw new Error("Expected standard padded Base64 category:value pairs.");
  const binary = atob(value);
  if (btoa(binary) !== value)
    throw new Error("Expected canonical Base64 encoding.");
  // Preserve a literal BOM and reject malformed UTF-8 instead of replacing it.
  return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(
    Uint8Array.from(binary, (char) => char.charCodeAt(0)),
  );
}

const metadata: FilterDefinition<MetadataCondition[]> = {
  label: "Execution metadata",
  kind: "metadata",
  empty: () => [],
  parse(input) {
    const categories = new Map<string, Set<string>>();
    // Commas/colons are delimiters only in the encoded wire representation;
    // decoded categories and values may contain either, whitespace or Unicode.
    for (const pair of input.flatMap((value) => value.split(","))) {
      const parts = pair.split(":");
      if (parts.length !== 2)
        throw new Error("Expected Base64 category:value pairs.");
      const category = decodeMetadataPart(parts[0]);
      const value = decodeMetadataPart(parts[1]);
      const values = categories.get(category) ?? new Set<string>();
      values.add(value);
      categories.set(category, values);
    }
    return [...categories].map(([category, values]) => ({
      category,
      values: [...values],
    }));
  },
  serialize: (conditions) =>
    conditions.flatMap(({ category, values }) =>
      values.map(
        (value) =>
          `${encodeMetadataPart(category)}:${encodeMetadataPart(value)}`,
      ),
    ),
  clone: (conditions) =>
    conditions.map(({ category, values }) => ({
      category,
      values: [...values],
    })),
};

/** Validate calendar components and backend microsecond precision before
 * constructing an instant: no rollover, timezone assumptions or truncation. */
function instantParts(value: string): { seconds: number; fraction: string } {
  const match =
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|([+-])(\d{2}):(\d{2}))$/.exec(
      value,
    );
  const invalid = () =>
    new Error(
      "Expected a valid ISO timestamp with an explicit timezone (Z or ±HH:MM).",
    );
  if (!match) throw invalid();
  const [, y, m, d, h, min, sec, fraction = "", zone, sign, zh, zm] = match;
  // Python datetime truncates beyond microseconds. Reject any lost precision
  // rather than silently broadening a lower bound; extra trailing zeros are exact.
  if (/[1-9]/.test(fraction.slice(6)))
    throw new Error(
      "Timestamp must be representable at microsecond precision (at most six fractional digits, except trailing zeros).",
    );
  const [year, month, day, hour, minute, second] = [y, m, d, h, min, sec].map(
    Number,
  );
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const zoneHour = zone === "Z" ? 0 : Number(zh);
  const zoneMinute = zone === "Z" ? 0 : Number(zm);
  if (
    year < 1 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > days[month - 1] ||
    hour > 23 ||
    minute > 59 ||
    second > 59 ||
    zoneHour > 23 ||
    zoneMinute > 59
  )
    throw invalid();
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  date.setUTCHours(hour, minute, second, 0);
  const offset = (zoneHour * 60 + zoneMinute) * 60 * (sign === "-" ? -1 : 1);
  return { seconds: date.getTime() / 1000 - offset, fraction };
}

export function parseIsoInstant(value: string): IsoInstant {
  instantParts(value);
  return value as IsoInstant;
}

export function compareInstants(a: IsoInstant, b: IsoInstant): number {
  const left = instantParts(a);
  const right = instantParts(b);
  if (left.seconds !== right.seconds)
    return left.seconds < right.seconds ? -1 : 1;
  const width = Math.max(left.fraction.length, right.fraction.length);
  const l = left.fraction.padEnd(width, "0");
  const r = right.fraction.padEnd(width, "0");
  return l === r ? 0 : l < r ? -1 : 1;
}

function instant(label: string): FilterDefinition<IsoInstant | null> {
  return {
    label,
    kind: "instant",
    empty: () => null,
    parse(values) {
      if (!values.length) return null;
      if (values.length !== 1) throw new Error("Expected one timestamp.");
      return parseIsoInstant(values[0]);
    },
    serialize: (value) => (value === null ? [] : [value]),
    clone: (value) => value,
  };
}

/** Definitions own empty/parse/serialize/clone operations, not UI-specific state. */
export const FILTER_DEFINITIONS: {
  [K in SearchFilter]: FilterDefinition<SearchFilters[K]>;
} = {
  families: list("Families"),
  test_result_statuses: list("Test result statuses"),
  artefacts: list("Artefact names"),
  artefact_versions: list("Versions"),
  artefact_tracks: list("Tracks"),
  environments: list("Environments"),
  test_plans: list("Test plans"),
  test_cases: list("Test cases"),
  artefact_stages: list("Stages", true),
  artefact_is_archived: boolean("Archived artefacts"),
  rerun_is_requested: boolean("Rerun requested"),
  execution_is_latest: boolean("Latest execution"),
  issues: ids("Issues"),
  reviewer_ids: ids("Reviewers"),
  execution_metadata: metadata,
  from_date: instant("Results from"),
  until_date: instant("Results until"),
  template_ids: list("Template IDs"),
};
export const SEARCH_FILTERS = Object.keys(FILTER_DEFINITIONS) as SearchFilter[];

export function emptyFilters(): SearchFilters {
  // Each required key is initialized by its own typed definition below.
  const filters = {} as SearchFilters;
  function initialize<K extends SearchFilter>(key: K) {
    filters[key] = FILTER_DEFINITIONS[key].empty();
  }
  SEARCH_FILTERS.forEach(initialize);
  return filters;
}

export function filterValues<K extends SearchFilter>(
  key: K,
  filters: SearchFilters,
): string[] {
  return FILTER_DEFINITIONS[key].serialize(filters[key]);
}

export function filterIsActive(
  key: SearchFilter,
  filters: SearchFilters,
): boolean {
  return filterValues(key, filters).length > 0;
}

export function hasFilters(filters: SearchFilters): boolean {
  return SEARCH_FILTERS.some((key) => filterIsActive(key, filters));
}

export function cloneFilters(filters: SearchFilters): SearchFilters {
  const copy = emptyFilters();
  function clone<K extends SearchFilter>(key: K) {
    copy[key] = FILTER_DEFINITIONS[key].clone(filters[key]);
  }
  SEARCH_FILTERS.forEach(clone);
  return copy;
}

export function clearFilter(
  filters: SearchFilters,
  key: SearchFilter,
): SearchFilters {
  return { ...filters, [key]: FILTER_DEFINITIONS[key].empty() };
}

/** Filter alternatives/categories are sets: ordering and duplicate values don't
 * make an unapplied draft. Values (including false and stage "") remain exact. */
export function filtersEqual(
  left: SearchFilters,
  right: SearchFilters,
): boolean {
  return SEARCH_FILTERS.every((key) => {
    const a = [...new Set(filterValues(key, left))].sort();
    const b = [...new Set(filterValues(key, right))].sort();
    return (
      a.length === b.length && a.every((value, index) => value === b[index])
    );
  });
}

export function parseFilters(params: URLSearchParams): {
  filters: SearchFilters;
  problems: string[];
} {
  const filters = emptyFilters();
  const problems: string[] = [];
  function parse<K extends SearchFilter>(key: K) {
    // Flutter chooses canonical reviewer_ids by presence. The backend also
    // prefers nonempty canonical IDs. An explicitly empty/invalid canonical
    // value blocks here rather than falling back to a potentially broader alias.
    const source =
      key === "reviewer_ids" && !params.has(key) ? "assignee_ids" : key;
    try {
      filters[key] = FILTER_DEFINITIONS[key].parse(params.getAll(source));
    } catch (error) {
      problems.push(
        `Invalid ${key}: ${error instanceof Error ? error.message : "Invalid value."}`,
      );
    }
  }
  SEARCH_FILTERS.forEach(parse);
  if (
    filters.from_date &&
    filters.until_date &&
    compareInstants(filters.from_date, filters.until_date) > 0
  )
    problems.push(
      "Invalid date range: from_date must not be after until_date.",
    );
  return { filters, problems };
}
