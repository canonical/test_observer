<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import { page } from "$app/state";
  import { SvelteURL } from "svelte/reactivity";
  import { goto } from "$app/navigation";
  import {
    SvGrid,
    attachAutoSavedView,
    createNamedViews,
    type GridColumns,
    type SvGridApi,
  } from "@svgrid/grid";
  import { silentApi } from "$lib/api/client";
  import { createTrackColumnWidthActions } from "$lib/components/dashboard/trackColumnWidthActions";
  import {
    AUTOSAVE_SLOT,
    createUserResizeViewHost,
    searchGridViewStorage,
  } from "$lib/gridViewUrl";
  import type {
    TestResultSearchPageResponse,
    TestResultSearchPageRow,
  } from "$lib/types/test-results-search-page";
  import {
    emptySearchFilters,
    formatSearchFilterText,
    parseSearchFilters,
    searchFilterQueryKey,
    searchFilterRequestParams,
    searchFiltersEqual,
    serializeSearchFilters,
    splitSearchFilterText,
    validateSearchFilters,
    type SearchFilterListKey,
    type SearchFilters,
  } from "$lib/searchPageFilters";
  import {
    hasValidSearchPageCount,
    parseSearchPageState,
    searchLastPage,
    searchPageItems,
    searchPageParams,
    searchPageRange,
    searchPageRangeLabel,
    searchPageRequestParams,
    searchPageSizeParams,
    searchTotalPages,
  } from "$lib/searchPagination";

  type TestResultGridRow = Record<string, unknown> & {
    id: number;
    createdAt: string;
    artefact: string;
    testCase: string;
    category: string;
    execution: number;
    status: string;
    track: string;
    version: string;
    environmentBuildArchitecture: string;
    testPlan: string;
  };

  let gridApi: SvGridApi<never, TestResultGridRow> | null = null;
  let detachAutosave: (() => void) | null = null;
  let saveCurrentView: (() => void) | null = null;
  let resizeWidthPersistence: ReturnType<
    typeof createUserResizeViewHost
  > | null = null;

  function handleColumnResize(event: { columnId: string; width: number }) {
    resizeWidthPersistence?.recordResize(event.columnId, event.width);
  }

  const trackColumnWidthActions = createTrackColumnWidthActions({
    getPersistence: () => resizeWidthPersistence,
    getCurrentApi: () => gridApi,
  });

  function clearGridPersistence() {
    saveCurrentView?.();
    saveCurrentView = null;
    detachAutosave?.();
    detachAutosave = null;
    resizeWidthPersistence = null;
    gridApi = null;
  }

  function cleanupGridPersistence(_node: HTMLDivElement) {
    return { destroy: clearGridPersistence };
  }

  function handleApiReady(ready: SvGridApi<never, TestResultGridRow>) {
    clearGridPersistence();
    gridApi = ready;

    // Keep fitColumns' effective widths out of autosaved state; only the
    // explicit widths reported by user resize actions belong in this view.
    resizeWidthPersistence = createUserResizeViewHost(ready);
    const viewHost = resizeWidthPersistence.host;
    const views = createNamedViews(viewHost, {
      storage: searchGridViewStorage(),
    });
    views.load(AUTOSAVE_SLOT);
    saveCurrentView = () => views.save(AUTOSAVE_SLOT);
    detachAutosave = attachAutoSavedView(viewHost, views, {
      skipRestore: true,
    });
  }

  function toGridRows(results: TestResultSearchPageRow[]): TestResultGridRow[] {
    return results.map((row) => ({
      id: row.test_result.id,
      createdAt: row.test_result.created_at,
      artefact: row.artefact.name,
      testCase: row.test_result.name,
      category: row.test_result.category,
      execution: row.test_execution.id,
      status: row.test_result.status,
      track: row.artefact.track || "—",
      version: row.artefact.version,
      environmentBuildArchitecture: `${row.test_execution.environment.name} / ${row.artefact_build.architecture}`,
      testPlan: row.test_execution.test_plan,
    }));
  }

  type LoadState = "invalid" | "loading" | "loaded" | "failed";
  let response = $state.raw<TestResultSearchPageResponse | null>(null);
  let loadState = $state<LoadState>("loading");
  let retryGeneration = $state(0);
  let navigationError = $state(false);
  // The URL tag guards against painting a prior response during client navigation.
  let requestUrlState = $state<string | null>(null);
  let requestGeneration = 0;

  type DraftKey = SearchFilterListKey | "from_date" | "until_date";
  function draftTextFor(filters: SearchFilters): Record<DraftKey, string> {
    return {
      families: formatSearchFilterText(filters.families),
      test_result_statuses: formatSearchFilterText(
        filters.test_result_statuses,
      ),
      artefacts: formatSearchFilterText(filters.artefacts),
      artefact_versions: formatSearchFilterText(filters.artefact_versions),
      artefact_tracks: formatSearchFilterText(filters.artefact_tracks),
      environments: formatSearchFilterText(filters.environments),
      test_cases: formatSearchFilterText(filters.test_cases),
      test_plans: formatSearchFilterText(filters.test_plans),
      from_date: filters.from_date ?? "",
      until_date: filters.until_date ?? "",
    };
  }

  const filterFields: { key: SearchFilterListKey; label: string }[] = [
    { key: "families", label: "Family" },
    { key: "test_result_statuses", label: "Result status" },
    { key: "artefacts", label: "Artefact" },
    { key: "artefact_versions", label: "Version" },
    { key: "artefact_tracks", label: "Track" },
    { key: "environments", label: "Environment" },
    { key: "test_cases", label: "Test case" },
    { key: "test_plans", label: "Test plan" },
  ];
  let draftValues = $state<Record<DraftKey, string>>(
    draftTextFor(emptySearchFilters()),
  );
  let draftFilterKey = $state<string | null>(null);
  let editedDraftKeys = $state<string[]>([]);
  let clearAllRequested = $state(false);

  const pageState = $derived(parseSearchPageState(page.url.searchParams));
  const filterState = $derived(parseSearchFilters(page.url.searchParams));
  const appliedFilters = $derived(filterState.filters);
  const draftFilters = $derived.by(() => {
    const filters = emptySearchFilters();
    for (const { key } of filterFields) {
      filters[key] = splitSearchFilterText(draftValues[key]);
    }
    filters.from_date = draftValues.from_date.trim() || null;
    filters.until_date = draftValues.until_date.trim() || null;
    return filters;
  });
  const draftProblems = $derived.by(() => {
    const problems = validateSearchFilters(draftFilters);
    if (clearAllRequested) return problems;
    for (const problem of filterState.problems) {
      if (problem.startsWith("Unsupported search parameter:")) continue;
      const field = problem.match(/^Invalid ([a-z_]+):/)?.[1];
      const isDateRange = problem.startsWith("Invalid date range:");
      const wasEdited = isDateRange
        ? editedDraftKeys.includes("from_date") ||
          editedDraftKeys.includes("until_date")
        : field !== undefined && editedDraftKeys.includes(field);
      if (wasEdited) continue;
      const duplicateProblem = problems.some((draftProblem) =>
        isDateRange
          ? draftProblem.startsWith("Invalid date range:")
          : field !== undefined && draftProblem.startsWith(`Invalid ${field}:`),
      );
      if (!duplicateProblem) problems.push(problem);
    }
    return problems;
  });
  const unknownAppliedFilter = $derived(
    filterState.problems.some((problem) =>
      problem.startsWith("Unsupported search parameter:"),
    ),
  );
  const canApplySearch = $derived(
    draftProblems.length === 0 && (!unknownAppliedFilter || clearAllRequested),
  );
  const unapplied = $derived(
    !searchFiltersEqual(draftFilters, appliedFilters) ||
      (unknownAppliedFilter && clearAllRequested),
  );
  let jumpValue = $derived<number | null>(pageState.page);
  const problems = $derived([...pageState.problems, ...filterState.problems]);
  const isInvalid = $derived(problems.length > 0);
  const isLoading = $derived(
    !isInvalid &&
      (requestUrlState !== page.url.href || loadState === "loading"),
  );
  const isFailed = $derived(
    !isInvalid && requestUrlState === page.url.href && loadState === "failed",
  );
  const currentResponse = $derived(
    requestUrlState === page.url.href && loadState === "loaded"
      ? response
      : null,
  );
  const rows = $derived(
    currentResponse ? toGridRows(currentResponse.test_results) : [],
  );
  const range = $derived(
    currentResponse ? searchPageRange(currentResponse) : null,
  );
  const totalPages = $derived(
    range ? searchTotalPages(range.count, pageState.pageSize) : 0,
  );
  const pageItems = $derived(searchPageItems(pageState.page, totalPages));
  const jumpTarget = $derived(
    jumpValue === null || !Number.isFinite(jumpValue) || totalPages === 0
      ? null
      : Math.min(Math.max(1, Math.trunc(jumpValue)), totalPages),
  );

  const columns: GridColumns<TestResultGridRow> = [
    {
      id: "created",
      header: "Created",
      field: "createdAt",
      cell: ({ row }) => new Date(row.original.createdAt).toLocaleString(),
    },
    {
      id: "artefact",
      header: "Artefact",
      field: "artefact",
    },
    {
      id: "testCase",
      header: "Test Case",
      field: "testCase",
    },
    {
      id: "category",
      header: "Category",
      field: "category",
    },
    {
      id: "execution",
      header: "Test Execution ID",
      field: "execution",
    },
    {
      id: "status",
      header: "Status",
      field: "status",
    },
    {
      id: "track",
      header: "Track",
      field: "track",
    },
    {
      id: "version",
      header: "Version",
      field: "version",
    },
    {
      id: "environmentBuildArchitecture",
      header: "Environment / Build Architecture",
      field: "environmentBuildArchitecture",
    },
    {
      id: "testPlan",
      header: "Test Plan",
      field: "testPlan",
    },
  ];

  $effect.pre(() => {
    const key = searchFilterQueryKey(page.url.searchParams);
    if (key === draftFilterKey) return;
    const parsed = parseSearchFilters(page.url.searchParams);
    untrack(() => {
      draftFilterKey = key;
      draftValues = draftTextFor(parsed.filters);
      editedDraftKeys = [];
      clearAllRequested = false;
    });
  });

  $effect(() => {
    const requestUrl = page.url.href;
    const parsed = parseSearchPageState(page.url.searchParams);
    const parsedFilters = parseSearchFilters(page.url.searchParams);
    const attempt = retryGeneration;
    const generation = ++requestGeneration;
    response = null;
    requestUrlState = requestUrl;
    navigationError = false;

    if (parsed.problems.length > 0 || parsedFilters.problems.length > 0) {
      loadState = "invalid";
      return;
    }

    const controller = new AbortController();
    const params = searchPageRequestParams(parsed.page, parsed.pageSize);
    for (const [key, value] of searchFilterRequestParams(
      parsedFilters.filters,
    )) {
      params.append(key, value);
    }
    loadState = "loading";
    void silentApi<TestResultSearchPageResponse>(
      `test-results/search-page?${params}`,
      { signal: controller.signal },
    )
      .then(async (result) => {
        if (
          generation !== requestGeneration ||
          attempt !== retryGeneration ||
          requestUrl !== page.url.href ||
          controller.signal.aborted
        )
          return;
        if (!result || !hasValidSearchPageCount(result)) {
          throw new Error(
            "The search page did not return its exact result count.",
          );
        }
        if (!Array.isArray(result.test_results)) {
          throw new Error(
            "The search page response did not contain result rows.",
          );
        }

        const lastPage = searchLastPage(result.count, parsed.pageSize);
        if (parsed.page > lastPage) {
          const corrected = new SvelteURL(page.url.href);
          corrected.search = searchPageParams(
            corrected.searchParams,
            lastPage,
          ).toString();
          await goto(corrected, { replace: true });
          return;
        }

        response = result;
        loadState = "loaded";
      })
      .catch(() => {
        if (
          generation !== requestGeneration ||
          attempt !== retryGeneration ||
          controller.signal.aborted
        )
          return;
        response = null;
        loadState = "failed";
      });
    return () => controller.abort();
  });

  onDestroy(() => {
    requestGeneration += 1;
    clearGridPersistence();
  });

  function navigateToPage(targetPage: number, replace = false) {
    const target = new SvelteURL(page.url.href);
    target.search = searchPageParams(
      target.searchParams,
      targetPage,
    ).toString();
    navigationError = false;
    void goto(target, { replace }).catch(() => {
      navigationError = true;
    });
  }

  function changePageSize(event: Event) {
    const size = Number((event.currentTarget as HTMLSelectElement).value);
    try {
      const target = new SvelteURL(page.url.href);
      target.search = searchPageSizeParams(
        target.searchParams,
        size,
      ).toString();
      navigationError = false;
      void goto(target).catch(() => {
        navigationError = true;
      });
    } catch {
      // Ignore values that are not one of the supported page sizes.
    }
  }

  function submitPageJump(event: SubmitEvent) {
    event.preventDefault();
    if (jumpTarget === null || jumpTarget === pageState.page) return;
    navigateToPage(jumpTarget);
  }

  function retry() {
    retryGeneration += 1;
  }

  function editDraft(key: DraftKey) {
    clearAllRequested = false;
    if (!editedDraftKeys.includes(key))
      editedDraftKeys = [...editedDraftKeys, key];
  }

  function clearDrafts() {
    draftValues = draftTextFor(emptySearchFilters());
    editedDraftKeys = [];
    clearAllRequested = true;
  }

  function submitSearch(event: SubmitEvent) {
    event.preventDefault();
    if (!canApplySearch) return;
    const target = new SvelteURL(page.url.href);
    target.search = serializeSearchFilters(
      draftFilters,
      page.url.searchParams,
    ).toString();
    navigationError = false;
    if (target.href === page.url.href) {
      retryGeneration += 1;
      return;
    }
    void goto(target).catch(() => {
      navigationError = true;
    });
  }

  function canClearDrafts() {
    return (
      !searchFiltersEqual(draftFilters, emptySearchFilters()) ||
      filterState.problems.length > 0 ||
      filterFields.some(({ key }) => page.url.searchParams.has(key)) ||
      page.url.searchParams.has("from_date") ||
      page.url.searchParams.has("until_date")
    );
  }
</script>

<section
  class="results-page"
  aria-labelledby="page-title"
  aria-busy={isLoading}
>
  <h1 id="page-title" class="page-title">Search Results (WIP)</h1>

  <form
    class="filter-form"
    aria-label="Test result search filters"
    onsubmit={submitSearch}
  >
    <div class="filter-grid">
      {#each filterFields as field (field.key)}
        <label class="filter-control" for="filter-{field.key}">
          {field.label}
          <textarea
            id="filter-{field.key}"
            name={field.key}
            autocomplete="off"
            rows="2"
            placeholder="Enter exact value(s), one per line"
            bind:value={draftValues[field.key]}
            oninput={() => editDraft(field.key)}></textarea>
          <span
            >Enter one exact value per line; values in this field are ORed. Use
            \n and \r for line breaks within a value, and \\ for a literal
            backslash.</span
          >
        </label>
      {/each}
      <label class="filter-control" for="filter-from-date">
        Created from (UTC)
        <input
          id="filter-from-date"
          name="from_date"
          type="text"
          autocomplete="off"
          placeholder="2026-01-02T03:04:05Z"
          bind:value={draftValues.from_date}
          oninput={() => editDraft("from_date")}
        />
        <span>Inclusive ISO-8601 timestamp lower bound.</span>
      </label>
      <label class="filter-control" for="filter-until-date">
        Created to (UTC)
        <input
          id="filter-until-date"
          name="until_date"
          type="text"
          autocomplete="off"
          placeholder="2026-01-02T03:04:05Z"
          bind:value={draftValues.until_date}
          oninput={() => editDraft("until_date")}
        />
        <span>Inclusive ISO-8601 timestamp upper bound.</span>
      </label>
    </div>
    <div class="filter-actions">
      <button
        class="pager-button search-button"
        type="submit"
        disabled={!canApplySearch}>Search</button
      >
      {#if canClearDrafts()}
        <button class="pager-button" type="button" onclick={clearDrafts}
          >Clear all</button
        >
      {/if}
    </div>
  </form>

  {#if unapplied}
    <p class="draft-notice" role="status">
      Changes not applied. Search to update results.
    </p>
  {/if}
  {#if draftProblems.length > 0}
    <div class="state-message error-message" role="alert">
      <h2>Invalid filter draft</h2>
      <ul>
        {#each draftProblems as problem (problem)}<li>{problem}</li>{/each}
      </ul>
      <p>No request was sent. Correct the filter values before searching.</p>
    </div>
  {/if}

  {#if isInvalid}
    <div
      class="state-message error-message"
      role="alert"
      aria-labelledby="url-error-title"
    >
      <h2 id="url-error-title">Invalid search page URL</h2>
      <ul>
        {#each problems as problem (problem)}
          <li>{problem}</li>
        {/each}
      </ul>
      <p>
        No request was sent. Correct the page, page_size, and filter values in
        the URL, or clear all filters.
      </p>
    </div>
  {:else}
    <div class="grid-region" aria-busy={isLoading}>
      {#if isLoading}
        <p class="state-message" role="status" aria-live="polite">
          Loading test results…
        </p>
      {:else if isFailed}
        <div class="state-message error-message" role="alert">
          <p>Test results could not be loaded.</p>
          <button class="retry-button" type="button" onclick={retry}
            >Retry</button
          >
        </div>
      {:else if currentResponse}
        {#if rows.length === 0}
          <p class="state-message" role="status">No test results found.</p>
        {:else}
          <div
            class="grid-wrapper"
            role="region"
            aria-label="Search results table"
            use:trackColumnWidthActions
            use:cleanupGridPersistence
          >
            <SvGrid
              data={rows}
              {columns}
              containerHeight="100%"
              fitColumns
              getRowId={(row) => String(row.id)}
              sortable={false}
              filterable={false}
              filterMode="none"
              showGlobalFilter={false}
              showColumnFilters={false}
              showFilterRow={false}
              showPagination={false}
              pageable={false}
              selectionMode="none"
              showRowSelection={false}
              contextMenu={false}
              virtualization
              columnVirtualization={false}
              columnResize
              onColumnResize={handleColumnResize}
              onApiReady={handleApiReady}
              enableRowHover
              rowResize={false}
            />
          </div>
        {/if}
      {/if}
    </div>

    {#if currentResponse && range}
      <nav class="pager" aria-label="Test result pages">
        <span class="range" role="status" aria-live="polite">
          {searchPageRangeLabel(range)}
        </span>
        <div class="pager-controls">
          <button
            class="pager-button"
            type="button"
            aria-label="Previous page"
            onclick={() => navigateToPage(pageState.page - 1)}
            disabled={pageState.page <= 1}>Previous</button
          >
          <ul class="pager-pages" aria-label="Page numbers">
            {#each pageItems as item, index (index)}
              {#if item === "gap"}
                <li class="pager-gap" aria-hidden="true">…</li>
              {:else}
                <li>
                  <button
                    class="pager-button"
                    type="button"
                    aria-label="Page {item}"
                    aria-current={item === pageState.page ? "page" : undefined}
                    disabled={item === pageState.page}
                    onclick={() => navigateToPage(item)}>{item}</button
                  >
                </li>
              {/if}
            {/each}
          </ul>
          <button
            class="pager-button"
            type="button"
            aria-label="Next page"
            onclick={() => navigateToPage(pageState.page + 1)}
            disabled={totalPages === 0 || pageState.page >= totalPages}
            >Next</button
          >
        </div>
        {#if totalPages > 0}
          <form class="pager-jump" novalidate onsubmit={submitPageJump}>
            <label for="search-page-jump">Go to page</label>
            <input
              id="search-page-jump"
              class="pager-jump-input"
              type="number"
              min="1"
              max={totalPages}
              step="1"
              inputmode="numeric"
              bind:value={jumpValue}
            />
            <span>of {totalPages}</span>
            <button
              class="pager-button"
              type="submit"
              disabled={jumpTarget === null || jumpTarget === pageState.page}
              >Go</button
            >
          </form>
        {/if}
        <label class="page-size-label" for="search-page-size">
          Results per page
          <select
            id="search-page-size"
            value={pageState.pageSize}
            onchange={changePageSize}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>
      </nav>
    {/if}
  {/if}

  {#if navigationError}
    <p class="state-message error-message" role="alert">
      Could not update the search URL. Please try again.
    </p>
  {/if}
</section>

<style>
  .results-page {
    display: flex;
    flex-direction: column;
    min-width: 0;
    height: calc(100vh - 3rem);
    height: calc(100dvh - 3rem);
    min-height: 0;
  }

  .page-title {
    flex: 0 0 auto;
    font-size: 1.75rem;
    font-weight: 500;
    margin: 0 0 0.75rem;
  }

  .filter-form {
    display: flex;
    flex: 0 0 auto;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .filter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(15rem, 100%), 1fr));
    gap: 0.75rem;
  }

  .filter-control {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.875rem;
  }

  .filter-control input,
  .filter-control textarea {
    box-sizing: border-box;
    width: 100%;
    min-height: 2rem;
    padding: 0.25rem 0.5rem;
    color: var(--lp-color-text-default, #222);
    background: var(--lp-color-background-default, #fff);
    border: 1px solid var(--lp-color-border-default, #ccc);
    border-radius: 0.25rem;
    font: inherit;
  }

  .filter-control span,
  .draft-notice {
    color: var(--lp-color-text-muted, #666);
    font-size: 0.8125rem;
  }

  .filter-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .search-button {
    background: var(--lp-color-brand-default, #06c);
    color: var(--lp-color-text-inverted, #fff);
  }

  .filter-control input:focus-visible,
  .filter-control textarea:focus-visible {
    outline: 2px solid var(--lp-color-brand-default, #06c);
    outline-offset: 1px;
  }

  .draft-notice {
    margin: 0 0 0.5rem;
  }

  .grid-region {
    display: flex;
    flex: 1 1 0;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
  }

  .state-message {
    margin: 1rem 0;
    color: var(--lp-color-text-muted, #666);
  }

  .error-message {
    color: var(--lp-color-text-default, #222);
  }

  .error-message h2 {
    margin: 0 0 0.5rem;
    font-size: 1.125rem;
    font-weight: 500;
  }

  .retry-button,
  .pager-button {
    border: 1px solid currentColor;
    border-radius: 0.25rem;
    background: transparent;
    color: inherit;
    cursor: pointer;
    font: inherit;
    min-height: 2rem;
    padding: 0.25rem 0.625rem;
  }

  .retry-button {
    padding: 0.375rem 0.75rem;
  }

  .pager-button[aria-current="page"] {
    background: var(--lp-color-brand-default, #06c);
    border-color: var(--lp-color-brand-default, #06c);
    color: var(--lp-color-text-inverted, #fff);
  }

  .pager-button:disabled {
    cursor: default;
    opacity: 0.55;
  }

  .grid-wrapper {
    flex: 1 1 auto;
    max-width: 100%;
    min-height: 0;
    overflow: auto;
    width: 100%;
  }

  .pager {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }

  .range {
    display: flex;
    align-items: center;
    margin-right: auto;
    color: var(--lp-color-text-muted, #666);
    font-size: 0.875rem;
  }

  .pager-controls,
  .pager-pages,
  .pager-jump {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    min-width: 0;
    max-width: 100%;
  }

  .pager-pages {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .pager-gap {
    padding: 0 0.125rem;
    color: var(--lp-color-text-muted, #666);
  }

  .pager-jump,
  .page-size-label {
    color: var(--lp-color-text-muted, #666);
    font-size: 0.875rem;
  }

  .pager-jump-input {
    width: 4rem;
    min-height: 2rem;
    padding: 0.25rem 0.5rem;
    font: inherit;
    color: var(--lp-color-text-default, #222);
    background: var(--lp-color-background-default, #fff);
    border: 1px solid var(--lp-color-border-default, #ccc);
    border-radius: 0.25rem;
  }

  .pager-jump-input:focus-visible,
  .pager-button:focus-visible,
  .retry-button:focus-visible {
    outline: 2px solid var(--lp-color-brand-default, #06c);
    outline-offset: 1px;
  }

  .page-size-label {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    min-width: 0;
    max-width: 100%;
    margin-left: 0.5rem;
  }

  .page-size-label select {
    min-height: 2rem;
    font: inherit;
  }

  /* Keep the scrollable grid independently usable in the bounded viewport. */
  .grid-wrapper :global(.sv-grid-container) {
    overscroll-behavior-y: auto;
  }

  @media (max-width: 50rem) {
    .range {
      flex-basis: 100%;
    }

    .pager-controls {
      gap: 0.25rem;
    }
  }
</style>
