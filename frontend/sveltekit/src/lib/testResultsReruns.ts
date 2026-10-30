// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { silentApi } from "$lib/api/client";
import {
  FILTER_DEFINITIONS,
  emptyFilters,
  parseFilters,
} from "$lib/testResultsFilters";
import { predicateFilters } from "$lib/testResultsPredicate";
import { EXECUTION_STATUSES } from "$lib/testResultsSearch";
import {
  executionIds,
  type BulkTarget,
  type TestResultMutationFilters,
} from "$lib/testResultsBulk";

export type RerunOperation = "create" | "delete";

/** The server's bulk gate counts deduplicated execution IDs, not result IDs. */
export function rerunIsBulk(target: BulkTarget): boolean {
  if (target.kind === "query") return true;
  const ids = executionIds(target);
  return !ids.ok || ids.value.length > 1;
}

/** Count-only GET codec, deliberately separate from page pagination (limit>=1).
 * Mutation metadata is raw JSON; GET requires repeated UTF-8 Base64 pairs. */
export function rerunCountParams(
  filters: TestResultMutationFilters,
): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (key === "execution_metadata") {
      for (const pair of FILTER_DEFINITIONS.execution_metadata.serialize(
        Object.entries(filters.execution_metadata ?? {}).map(
          ([category, values]) => ({ category, values: [...values] }),
        ),
      ))
        params.append(key, pair);
    } else {
      for (const entry of Array.isArray(value) ? value : [value])
        params.append(key, String(entry));
    }
  }
  params.set("limit", "0");
  return params;
}

/** Opt-in local Search destination and effective operation filters only. Search
 * parses list commas/whitespace, unlike mutation JSON: never offer a link that
 * would silently split, trim or drop a constraint. Keep the count GET's shared
 * metadata codec, but not its count-only pagination. */
export function rerunSearchUrl(
  filters: TestResultMutationFilters,
  destination: string,
): string | null {
  if (!/^\/(?!\/)[^?#\\\s]*$/.test(destination)) return null;
  try {
    const metadata: unknown = filters.execution_metadata;
    if (
      metadata !== undefined &&
      (!metadata || typeof metadata !== "object" || Array.isArray(metadata))
    )
      return null;
    const typed = predicateFilters({
      ...emptyFilters(),
      ...filters,
      execution_metadata: Object.entries(
        (metadata ?? {}) as Record<string, unknown>,
      ).map(([category, values]) => {
        if (!Array.isArray(values)) throw new Error("Invalid metadata values.");
        return { category, values: [...(values as unknown[])] };
      }),
    });
    if (
      typed.test_execution_statuses.some(
        (value) => !EXECUTION_STATUSES.some((status) => status === value),
      )
    )
      return null;
    const params = rerunCountParams(filters);
    params.delete("limit");
    const parsed = parseFilters(params);
    // Both sides use the strict typed predicate normalizer, not a serialized
    // comparison (which could hide a lossy UTF-8 metadata round trip).
    if (
      parsed.problems.length ||
      JSON.stringify(typed) !== JSON.stringify(predicateFilters(parsed.filters))
    )
      return null;
    return `${destination}?${params}`;
  } catch {
    return null;
  }
}

export async function previewRerunCount(
  filters: TestResultMutationFilters,
  signal: AbortSignal,
): Promise<number> {
  const body = await silentApi<{ count: number }>(
    `test-results?${rerunCountParams(filters)}`,
    { signal },
  );
  if (!body || !Number.isSafeInteger(body.count) || body.count < 0)
    throw new Error(
      "The server returned an invalid result count. Start a new preview.",
    );
  return body.count;
}
