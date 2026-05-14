<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";
  import { Breadcrumbs } from "@canonical/svelte-ds-app-launchpad";
  import {
    TestResultsFiltersPanel,
    TestResultsTable,
    BulkActionsBar,
  } from "$lib/components/test-results/index.js";
  import type { TestResultsFilters } from "$lib/types/filters.js";
  import { filtersToSearchParams, searchParamsToFilters } from "$lib/utils/filters.js";

  let { data } = $props();

  let selectedIds = $state<Set<number>>(new Set());
  let loadingMore = $state(false);

  const defaultFilters: TestResultsFilters = {
    families: [],
    testResultStatuses: [],
    artefacts: [],
    environments: [],
    testCases: [],
    templateIds: [],
    executionMetadata: { data: {} },
    issues: { type: "any" },
    assignees: { type: "any" },
  };

  function applyFilters(filters: TestResultsFilters): void {
    selectedIds = new Set();
    const params = filtersToSearchParams(filters);
    goto(`${base}/test-results?${params.toString()}`);
  }

  function resetFilters(): void {
    selectedIds = new Set();
    goto(`${base}/test-results`);
  }

  function loadMore(): void {
    const currentCount = data.results.testResults.length;
    const params = filtersToSearchParams({
      ...data.filters,
      offset: currentCount,
      limit: data.filters.limit ?? 50,
    });
    loadingMore = true;
    goto(`${base}/test-results?${params.toString()}`).finally(() => {
      loadingMore = false;
    });
  }

  function handleAttachIssue(): void {
    // Bulk attach issue - placeholder for modal integration
  }

  function handleRequestReruns(): void {
    // Bulk request reruns - placeholder for modal integration
  }

  function handleDeselectAll(): void {
    selectedIds = new Set();
  }

  const breadcrumbSegments = [{ label: "Test Results", href: `${base}/test-results` }];
</script>

<svelte:head>
  <title>Test Results — Test Observer</title>
</svelte:head>

<div class="ds test-results-page">
  <Breadcrumbs segments={breadcrumbSegments} />

  <h1>Search Test Results</h1>

  <TestResultsFiltersPanel
    filters={data.filters}
    familyOptions={data.familyOptions}
    onapply={applyFilters}
    onreset={resetFilters}
  />

  <TestResultsTable
    results={data.results}
    {selectedIds}
    onselectionchange={(ids) => { selectedIds = ids; }}
    onloadmore={loadMore}
    loading={loadingMore}
  />

  <BulkActionsBar
    selectedCount={selectedIds.size}
    onattachissue={handleAttachIssue}
    onrequestreruns={handleRequestReruns}
    ondeselectall={handleDeselectAll}
  />
</div>

<style>
  .ds.test-results-page {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
</style>
