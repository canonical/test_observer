// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { TestResultSearchPageRow } from "$lib/types/test-results-search-page";
import type { Family } from "$lib/types";

/** Build the configured artefact route focused on one Search result and run. */
export function searchRunPath(
  row: Pick<
    TestResultSearchPageRow,
    "test_result" | "test_execution" | "artefact"
  >,
  families: readonly Pick<Family, "name" | "api_name">[],
  basePath: string,
): string | null {
  const family = families.find(
    (candidate) => candidate.api_name === row.artefact.family,
  );
  if (!family?.name) return null;

  const base = basePath.replace(/\/+$/, "");
  const params = new URLSearchParams({
    testExecutionId: String(row.test_execution.id),
    testResultId: String(row.test_result.id),
  });
  return `${base}/${encodeURIComponent(family.name)}/${row.artefact.id}?${params}`;
}
