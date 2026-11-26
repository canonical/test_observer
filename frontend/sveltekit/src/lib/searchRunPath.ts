// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { TestResultSearchPageRow } from "$lib/types/test-results-search-page";
import type { FamilyResponse } from "$lib/types/openapi";
import { familyDetailRoute } from "$lib/families";

/** Build the configured artefact route focused on one Search result and run. */
export function searchRunPath(
  row: Pick<
    TestResultSearchPageRow,
    "test_result" | "test_execution" | "artefact"
  >,
  families: readonly FamilyResponse[] | null,
  basePath: string,
): string | null {
  const family = families?.find(
    (candidate) => candidate.name === row.artefact.family,
  );
  if (!family?.name) return null;

  const base = basePath.replace(/\/+$/, "");
  const params = new URLSearchParams({
    testExecutionId: String(row.test_execution.id),
    testResultId: String(row.test_result.id),
  });
  return `${base}/${familyDetailRoute(family, row.artefact.id)}?${params}`;
}
