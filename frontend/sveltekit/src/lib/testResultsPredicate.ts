// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import {
  SEARCH_FILTERS,
  FILTER_DEFINITIONS,
  compareInstants,
  emptyFilters,
  parseIsoInstant,
  validateMetadataPart,
  type SearchFilters,
} from "$lib/testResultsFilters";

export type Frozen<T> = T extends object
  ? { readonly [K in keyof T]: Frozen<T[K]> }
  : T;

/** Only JSON-shaped values, never Set/Map (Object.freeze does not protect them). */
export function freezeValue<T>(value: T): Frozen<T> {
  if (value !== null && typeof value === "object") {
    for (const child of Object.values(value)) freezeValue(child);
    Object.freeze(value);
  }
  return value as Frozen<T>;
}

export function positiveId(id: unknown): id is number {
  return typeof id === "number" && Number.isSafeInteger(id) && id > 0;
}

export interface SelectionQuery {
  readonly key: string;
  readonly filters: Frozen<SearchFilters>;
}

/** Validate typed data directly, not via GET serialization/URL parsing. Unknown
 * constraints must block instead of being silently lost by a clone. */
export function predicateFilters(input: unknown): SearchFilters {
  if (
    !input ||
    typeof input !== "object" ||
    Array.isArray(input) ||
    Object.keys(input).some(
      (key) => !SEARCH_FILTERS.includes(key as keyof SearchFilters),
    )
  )
    throw new Error(
      "Unknown search constraint. Correct the applied query first.",
    );
  const copy = emptyFilters();
  const candidate = input as Record<string, unknown>;
  for (const key of SEARCH_FILTERS) {
    const value = candidate[key];
    switch (FILTER_DEFINITIONS[key].kind) {
      case "boolean":
        if (value !== null && typeof value !== "boolean")
          throw new Error(`Invalid ${key}.`);
        Object.assign(copy, { [key]: value });
        break;
      case "instant":
        if (value !== null && typeof value !== "string")
          throw new Error(`Invalid ${key}.`);
        Object.assign(copy, {
          [key]: value === null ? null : parseIsoInstant(value),
        });
        break;
      case "ids":
        if (value === "any" || value === "none") {
          Object.assign(copy, { [key]: value });
        } else {
          if (
            !Array.isArray(value) ||
            ![...(value as unknown[])].every(positiveId)
          )
            throw new Error(`Invalid ${key}: use positive safe integer IDs.`);
          Object.assign(copy, { [key]: [...new Set(value)] });
        }
        break;
      case "list":
        if (
          !Array.isArray(value) ||
          ![...(value as unknown[])].every(
            (item: unknown) =>
              typeof item === "string" &&
              (key === "artefact_stages" || item.length > 0),
          )
        )
          throw new Error(`Invalid ${key}.`);
        if (
          key === "test_result_statuses" &&
          value.some(
            (item: string) => !["PASSED", "FAILED", "SKIPPED"].includes(item),
          )
        )
          throw new Error("Invalid test result status.");
        Object.assign(copy, { [key]: [...new Set(value)] });
        break;
      case "metadata": {
        if (!Array.isArray(value)) throw new Error("Invalid metadata.");
        const categories = new Map<string, Set<string>>();
        for (const item of value as unknown[]) {
          if (!item || typeof item !== "object")
            throw new Error("Invalid metadata condition.");
          const condition = item as Record<string, unknown>;
          if (
            typeof condition.category !== "string" ||
            Object.keys(condition).some(
              (key) => key !== "category" && key !== "values",
            ) ||
            !Array.isArray(condition.values) ||
            !condition.values.length
          )
            throw new Error("Invalid metadata condition.");
          validateMetadataPart(condition.category);
          const values =
            categories.get(condition.category) ?? new Set<string>();
          for (const item of condition.values as unknown[]) {
            if (typeof item !== "string")
              throw new Error("Invalid metadata value.");
            validateMetadataPart(item);
            values.add(item);
          }
          categories.set(condition.category, values);
        }
        copy.execution_metadata = [...categories].map(([category, values]) => ({
          category,
          values: [...values],
        }));
        break;
      }
    }
  }
  if (
    copy.from_date &&
    copy.until_date &&
    compareInstants(copy.from_date, copy.until_date) > 0
  )
    throw new Error("Invalid date range.");
  return copy;
}

/** Set-valued alternatives have semantic identity; dates compare at backend
 * microsecond precision, while the original ISO text is retained for JSON. */
export function selectionQuery(query: {
  filters: Frozen<SearchFilters>;
  hasFilters: boolean;
  problems: readonly string[];
}): SelectionQuery | null {
  if (!query.hasFilters || query.problems.length) return null;
  try {
    const filters = predicateFilters(query.filters);
    const entries = SEARCH_FILTERS.map((key) => {
      const value = filters[key];
      if (key === "from_date" || key === "until_date") {
        const instant = filters[key];
        if (!instant) return [key, null];
        const seconds = instant.replace(/\.\d+(?=Z|[+-]\d{2}:\d{2}$)/, "");
        const fraction = /\.(\d+)/.exec(instant)?.[1] ?? "";
        return [
          key,
          [Date.parse(seconds), fraction.slice(0, 6).padEnd(6, "0")],
        ];
      }
      if (key === "execution_metadata")
        return [
          key,
          filters.execution_metadata
            .map(({ category, values }) => [category, [...values].sort()])
            .sort((a, b) => {
              const left = JSON.stringify(a);
              const right = JSON.stringify(b);
              return left === right ? 0 : left < right ? -1 : 1;
            }),
        ];
      return [key, Array.isArray(value) ? [...value].sort() : value];
    });
    const active = SEARCH_FILTERS.some((key) => {
      const value = filters[key];
      return Array.isArray(value) ? value.length > 0 : value !== null;
    });
    return active
      ? freezeValue({ key: JSON.stringify(entries), filters })
      : null;
  } catch {
    return null;
  }
}
