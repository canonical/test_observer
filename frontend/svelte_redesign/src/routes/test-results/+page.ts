// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageLoad } from "./$types.js";
import { searchParamsToFilters } from "$lib/utils/filters.js";
import { searchTestResults } from "$lib/api/test-results.js";

export const load: PageLoad = async ({ url, fetch, parent }) => {
  const filters = searchParamsToFilters(url.searchParams);
  const { config } = await parent();

  let results;
  try {
    results = await searchTestResults(filters, fetch);
  } catch {
    results = { count: 0, testResults: [] };
  }

  return {
    filters,
    results,
    familyOptions: config.tabs,
  };
};
