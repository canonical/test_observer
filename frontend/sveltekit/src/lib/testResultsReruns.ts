// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { silentApi } from "$lib/api/client";
import { FILTER_DEFINITIONS } from "$lib/testResultsFilters";
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
