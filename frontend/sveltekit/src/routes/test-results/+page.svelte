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
  import type { PageProps } from "./$types";
  import { onDestroy, tick, untrack } from "svelte";
  import { page } from "$app/state";
  import { SvelteSet, SvelteURL } from "svelte/reactivity";
  import { goto, invalidate } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { SidePanel } from "@canonical/svelte-ds-app-launchpad";
  import {
    SvGrid,
    renderComponent,
    attachAutoSavedView,
    createNamedViews,
    type GridColumns,
    type SvGridApi,
  } from "@svgrid/grid";
  import { silentApi } from "$lib/api/client";
  import SearchSuggestionPicker from "$lib/components/SearchSuggestionPicker.svelte";
  import SearchMetadataEditor from "$lib/components/SearchMetadataEditor.svelte";
  import SearchRunLink from "$lib/components/search/SearchRunLink.svelte";
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
  import { searchRunPath } from "$lib/searchRunPath";
  import { FAMILIES_DEPENDENCY } from "$lib/familiesApi";

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
    runHref: string | null;
  };

  let { data }: PageProps = $props();
  const searchBasePath = resolve("").replace(/\/$/, "");

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
      runHref: searchRunPath(row, data.artefactFamilies, searchBasePath),
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

  type DraftKey =
    | "families"
    | "test_result_statuses"
    | "artefacts"
    | "artefact_versions"
    | "artefact_tracks"
    | "environments"
    | "test_cases"
    | "test_plans"
    | "template_ids"
    | "from_date"
    | "until_date";
  type TextListKey = Extract<DraftKey, SearchFilterListKey>;

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
      template_ids: formatSearchFilterText(filters.template_ids),
      from_date: filters.from_date ?? "",
      until_date: filters.until_date ?? "",
    };
  }

  const filterFields: { key: TextListKey; label: string }[] = [
    { key: "families", label: "Family" },
    { key: "test_result_statuses", label: "Result status" },
    { key: "artefacts", label: "Artefact" },
    { key: "artefact_versions", label: "Version" },
    { key: "artefact_tracks", label: "Track" },
    { key: "environments", label: "Environment" },
    { key: "test_cases", label: "Test case" },
    { key: "test_plans", label: "Test plan" },
    { key: "template_ids", label: "Template ID" },
  ];
  const commonFilterFields = filterFields.filter(
    ({ key }) => key !== "template_ids",
  );
  const advancedTextFields = filterFields.filter(
    ({ key }) => key === "template_ids",
  );
  let draftAdvanced = $state<SearchFilters>(emptySearchFilters());
  let stageEntryText = $state("");
  let draftValues = $state<Record<DraftKey, string>>(
    draftTextFor(emptySearchFilters()),
  );
  let draftFilterKey = $state<string | null>(null);
  let editedDraftKeys = $state<string[]>([]);
  let clearAllRequested = $state(false);
  let filterDrawerOpen = $state(false);
  let filterDrawerTrigger: HTMLButtonElement | null = null;
  let filterDrawerBody: HTMLDivElement | null = null;
  let filterDrawerFocusGeneration = 0;
  const filterDrawerId = "test-result-filter-drawer";
  const filterDrawerTitleId = "test-result-filter-title";

  // Refreshing families hands the page new data objects even when the list is
  // unchanged; derive by value so that doesn't rerun the results request.
  const familyNamesKey = $derived(
    data.familyNamesError ? null : JSON.stringify([...data.apiFamilyNames].sort()),
  );
  const validatedFamilyNames = $derived<string[] | undefined>(
    familyNamesKey === null ? undefined : JSON.parse(familyNamesKey),
  );

  // Invalidation also replaces page.url with an equal URL, so derive URL state
  // from its value to avoid resetting state or rerunning the request.
  const pageHref = $derived(page.url.href);
  const pageSearchParams = $derived(new URL(pageHref).searchParams);
  const pageState = $derived(parseSearchPageState(pageSearchParams));
  const filterState = $derived(
    parseSearchFilters(
      pageSearchParams,
      data.familyNamesError ? undefined : data.apiFamilyNames,
    ),
  );
  const appliedFilters = $derived(filterState.filters);
  const draftFilters = $derived.by(() => {
    const filters = { ...draftAdvanced };
    for (const { key } of filterFields) {
      filters[key] = splitSearchFilterText(
        draftValues[key],
      ) as SearchFilters[typeof key];
    }
    filters.from_date = draftValues.from_date.trim() || null;
    filters.until_date = draftValues.until_date.trim() || null;
    return filters;
  });
  const stageOptions = $derived(
    [
      ...new Set(["", ...draftAdvanced.artefact_stages]),
    ].sort((left, right) => left.localeCompare(right)),
  );
  const executionStatuses = [
    "NOT_STARTED",
    "NOT_TESTED",
    "IN_PROGRESS",
    "ENDED_PREMATURELY",
    "FAILED",
    "PASSED",
  ] as const;
  const issueIds = $derived(
    Array.isArray(draftAdvanced.issues) ? draftAdvanced.issues : [],
  );
  const reviewerIds = $derived(
    Array.isArray(draftAdvanced.reviewer_ids) ? draftAdvanced.reviewer_ids : [],
  );
  const draftFamilyValidationFailed = $derived(
    !clearAllRequested &&
      data.familyNamesError &&
      draftFilters.families.some((value) => value.trim() !== ""),
  );
  const draftProblems = $derived.by(() => {
    const problems = validateSearchFilters(
      draftFilters,
      data.familyNamesError ? undefined : data.apiFamilyNames,
    );
    if (draftFamilyValidationFailed) {
      problems.push(
        "Could not validate family values against the API family list. No request was sent.",
      );
    }
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
  const familyValidationProblem = $derived(
    data.familyNamesError &&
      page.url.searchParams
        .getAll("families")
        .some((value) => value.trim() !== "")
      ? [
          "Could not validate family values against the API family list. No request was sent.",
        ]
      : [],
  );
  const problems = $derived([
    ...pageState.problems,
    ...filterState.problems,
    ...familyValidationProblem,
  ]);
  const isInvalid = $derived(problems.length > 0);

  // The family list is loaded once per app start, so a family created since
  // then looks unknown. Refresh it once per set of unknown URL values before
  // reporting them as invalid; a repeat of the same set is reported directly.
  let familyRefreshCount = $state(0);
  const familyRefreshPending = $derived(familyRefreshCount > 0);
  const refreshedUnknownFamilies = new SvelteSet<string>();
  const unknownUrlFamilies = $derived(
    data.familyNamesError
      ? []
      : [
          ...new Set(
            appliedFilters.families.filter(
              (family) => !data.apiFamilyNames.includes(family),
            ),
          ),
        ].sort(),
  );

  async function refreshFamilies() {
    familyRefreshCount += 1;
    try {
      await invalidate(FAMILIES_DEPENDENCY);
    } finally {
      familyRefreshCount -= 1;
    }
  }

  $effect(() => {
    if (unknownUrlFamilies.length === 0) return;
    const key = JSON.stringify(unknownUrlFamilies);
    if (refreshedUnknownFamilies.has(key)) return;
    refreshedUnknownFamilies.add(key);
    void untrack(refreshFamilies);
  });
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
    {
      id: "run",
      header: "Run",
      sortable: false,
      filterable: false,
      cell: ({ row }) =>
        renderComponent(SearchRunLink, {
          href: row.original.runHref,
          name: row.original.testCase,
        }),
    },
  ];

  $effect.pre(() => {
    const key = searchFilterQueryKey(page.url.searchParams);
    if (key === draftFilterKey) return;
    const parsed = parseSearchFilters(page.url.searchParams);
    untrack(() => {
      draftFilterKey = key;
      draftValues = draftTextFor(parsed.filters);
      draftAdvanced = parsed.filters;
      stageEntryText = "";
      editedDraftKeys = [];
      clearAllRequested = false;
    });
  });

  $effect(() => {
    const requestUrl = pageHref;
    const parsed = parseSearchPageState(pageSearchParams);
    const parsedFilters = parseSearchFilters(
      pageSearchParams,
      validatedFamilyNames,
    );
    const familyValidationUnavailable =
      validatedFamilyNames === undefined &&
      parsedFilters.filters.families.some((value) => value.trim() !== "");
    const attempt = retryGeneration;
    const generation = ++requestGeneration;
    response = null;
    requestUrlState = requestUrl;
    navigationError = false;

    if (
      parsed.problems.length > 0 ||
      parsedFilters.problems.length > 0 ||
      familyValidationUnavailable
    ) {
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
    // Without a family list the page stays fail-closed, so reload the list too.
    if (data.familyNamesError) void refreshFamilies();
    retryGeneration += 1;
  }

  function editDraft(
    key:
      | DraftKey
      | "artefact_stages"
      | "test_execution_statuses"
      | "artefact_is_archived"
      | "rerun_is_requested"
      | "execution_is_latest"
      | "issues"
      | "reviewer_ids"
      | "execution_metadata",
  ) {
    if (!editedDraftKeys.includes(key))
      editedDraftKeys = [...editedDraftKeys, key];
  }

  function clearDrafts() {
    const empty = emptySearchFilters();
    draftValues = draftTextFor(empty);
    draftAdvanced = empty;
    stageEntryText = "";
    editedDraftKeys = [];
    clearAllRequested = true;
  }

  function addExactStage() {
    if (stageEntryText.trim() === "") return;
    toggleStage(stageEntryText, true);
    stageEntryText = "";
  }

  function toggleStage(stage: string, checked: boolean) {
    const values = draftAdvanced.artefact_stages;
    draftAdvanced.artefact_stages = checked
      ? [...new Set([...values, stage])]
      : values.filter((value) => value !== stage);
    editDraft("artefact_stages");
  }

  function toggleExecutionStatus(
    status: (typeof executionStatuses)[number],
    checked: boolean,
  ) {
    const values = draftAdvanced.test_execution_statuses;
    draftAdvanced.test_execution_statuses = checked
      ? [...new Set([...values, status])]
      : values.filter((value) => value !== status);
    editDraft("test_execution_statuses");
  }

  function setBooleanFilter(
    key: "artefact_is_archived" | "rerun_is_requested" | "execution_is_latest",
    value: string,
  ) {
    draftAdvanced[key] = value === "" ? null : value === "true";
    editDraft(key);
  }

  function setIdMode(
    key: "issues" | "reviewer_ids",
    mode: "ids" | "any" | "none",
  ) {
    if (mode === "ids") draftAdvanced[key] = [];
    else draftAdvanced[key] = mode;
    editDraft(key);
  }

  function addIds(key: "issues" | "reviewer_ids", values: string[]) {
    const existing = Array.isArray(draftAdvanced[key])
      ? draftAdvanced[key]
      : [];
    draftAdvanced[key] = [...new Set([...existing, ...values.map(Number)])];
    editDraft(key);
  }

  function removeId(key: "issues" | "reviewer_ids", id: number) {
    const existing = Array.isArray(draftAdvanced[key])
      ? draftAdvanced[key]
      : [];
    draftAdvanced[key] = existing.filter((value) => value !== id);
    editDraft(key);
  }

  function addSuggestedValues(key: TextListKey, values: string[]) {
    const current = splitSearchFilterText(draftValues[key]);
    draftValues[key] = formatSearchFilterText([
      ...new Set([...current, ...values]),
    ]);
    editDraft(key);
  }

  async function openFilterDrawer(event: MouseEvent) {
    filterDrawerTrigger = event.currentTarget as HTMLButtonElement;
    ++filterDrawerFocusGeneration;
    filterDrawerOpen = true;
    // Draft families are validated against the cached list, so refresh it
    // once per opening to accept families created since it was loaded.
    void refreshFamilies();
    await tick();
    if (!filterDrawerOpen) return;
    filterDrawerBody
      ?.querySelector<HTMLElement>("input, textarea, select, button")
      ?.focus({ preventScroll: true });
  }

  function restoreFilterDrawerFocus() {
    filterDrawerOpen = false;
    const generation = ++filterDrawerFocusGeneration;
    void tick().then(() => {
      if (generation !== filterDrawerFocusGeneration || filterDrawerOpen)
        return;
      const trigger = filterDrawerTrigger?.isConnected
        ? filterDrawerTrigger
        : document.querySelector<HTMLButtonElement>(
            `button[aria-controls="${filterDrawerId}"]`,
          );
      trigger?.focus({ preventScroll: true });
    });
  }

  function handleFilterDrawerKeydown(event: KeyboardEvent) {
    if (event.key !== "Escape" || !filterDrawerOpen) return;
    event.preventDefault();
    restoreFilterDrawerFocus();
  }

  async function submitSearch(event: SubmitEvent) {
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
      restoreFilterDrawerFocus();
      return;
    }
    try {
      await goto(target);
    } catch {
      navigationError = true;
    }
    restoreFilterDrawerFocus();
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
  class:filters-open={filterDrawerOpen}
  aria-labelledby="page-title"
  aria-busy={isLoading}
>
  <h1 id="page-title" class="page-title">Search Results (WIP)</h1>

  <div class="filter-toolbar" role="group" aria-label="Test result filters">
    <button
      class="pager-button filters-toggle"
      type="button"
      aria-haspopup="dialog"
      aria-controls={filterDrawerId}
      aria-expanded={filterDrawerOpen}
      onclick={openFilterDrawer}>Filters</button
    >
  </div>

  <SidePanel
    id={filterDrawerId}
    class="search-filter-panel"
    aria-labelledby={filterDrawerTitleId}
    bind:open={filterDrawerOpen}
    onclose={restoreFilterDrawerFocus}
    onkeydown={handleFilterDrawerKeydown}
  >
    {#snippet children(commandfor, close)}
      <SidePanel.Content>
        <form
          class="filter-form"
          aria-label="Test result search filters"
          onsubmit={submitSearch}
        >
          <SidePanel.Content.Header>
            <h2 id={filterDrawerTitleId}>Test result filters</h2>
            <SidePanel.Content.Header.CloseButton
              {commandfor}
              command="close"
              aria-label="Close filters"
              onclick={restoreFilterDrawerFocus}
            />
          </SidePanel.Content.Header>
          <div class="filter-panel-body" bind:this={filterDrawerBody}>
            <p class="filter-guidance">
              Draft changes apply only when you choose Search. Values within a
              field are ORed; separate fields are combined. For multiline
              values, use <code>\n</code> and <code>\r</code> for line breaks
              and
              <code>\\</code> for a literal backslash.
            </p>
            {#if draftProblems.length > 0}
              <div
                class="state-message error-message filter-draft-errors"
                role="alert"
              >
                <h2>Invalid filter draft</h2>
                <ul>
                  {#each draftProblems as problem (problem)}<li>
                      {problem}
                    </li>{/each}
                </ul>
                <p>
                  No request was sent. Correct the filter values before
                  searching.
                </p>
                {#if draftFamilyValidationFailed}
                  <button
                    class="retry-button"
                    type="button"
                    disabled={familyRefreshPending}
                    onclick={refreshFamilies}>Retry</button
                  >
                {/if}
              </div>
            {/if}
            <section
              class="filter-section"
              aria-labelledby="common-filters-title"
            >
              <h3 id="common-filters-title">Common filters</h3>
              <div class="filter-grid">
                {#each commonFilterFields as field (field.key)}
                  <div class="filter-control">
                    <label for="filter-{field.key}">{field.label}</label>
                    <textarea
                      id="filter-{field.key}"
                      name={field.key}
                      autocomplete="off"
                      rows="2"
                      placeholder="Exact value(s), one per line"
                      bind:value={draftValues[field.key]}
                      oninput={() => editDraft(field.key)}></textarea>
                    {#if field.key === "artefacts" || field.key === "environments" || field.key === "test_cases" || field.key === "test_plans"}
                      <SearchSuggestionPicker
                        field={field.key}
                        families={draftFilters.families}
                        onselect={(values) =>
                          addSuggestedValues(field.key, values)}
                      />
                    {/if}
                  </div>
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
                </label>
              </div>
              <p class="section-note">
                Created date bounds are inclusive ISO-8601 timestamps.
              </p>
            </section>

            <section
              class="filter-section"
              aria-labelledby="advanced-filters-title"
            >
              <h3 id="advanced-filters-title">Advanced filters</h3>
              <div class="filter-grid">
                {#each advancedTextFields as field (field.key)}
                  <div class="filter-control">
                    <label for="filter-{field.key}">{field.label}</label>
                    <textarea
                      id="filter-{field.key}"
                      name={field.key}
                      autocomplete="off"
                      rows="2"
                      placeholder="Exact value(s), one per line"
                      bind:value={draftValues[field.key]}
                      oninput={() => editDraft(field.key)}></textarea>
                  </div>
                {/each}
                <fieldset class="filter-control advanced-control wide-control">
                  <legend>Artefact stage</legend>
                  <div class="choice-list">
                    {#each stageOptions as stage (stage)}
                      <label>
                        <input
                          type="checkbox"
                          name="artefact_stages"
                          value={stage}
                          checked={draftAdvanced.artefact_stages.includes(
                            stage,
                          )}
                          onchange={(event) =>
                            toggleStage(stage, event.currentTarget.checked)}
                        />
                        {stage === "" ? "(none)" : stage}
                      </label>
                    {/each}
                  </div>
                  <p class="section-note">
                    (none) matches an explicitly empty stage. Add exact stages
                    to filter by their values.
                  </p>
                  <label for="filter-stage-entry">Exact stage</label>
                  <div class="inline-entry">
                    <input
                      id="filter-stage-entry"
                      autocomplete="off"
                      bind:value={stageEntryText}
                    />
                    <button
                      type="button"
                      class="pager-button"
                      onclick={addExactStage}
                      disabled={!stageEntryText.trim()}>Add</button
                    >
                  </div>
                </fieldset>
                <fieldset class="filter-control advanced-control">
                  <legend>Execution status</legend>
                  <div class="choice-list">
                    {#each executionStatuses as status (status)}
                      <label>
                        <input
                          type="checkbox"
                          name="test_execution_statuses"
                          value={status}
                          checked={draftAdvanced.test_execution_statuses.includes(
                            status,
                          )}
                          onchange={(event) =>
                            toggleExecutionStatus(
                              status,
                              event.currentTarget.checked,
                            )}
                        />
                        {status.replaceAll("_", " ")}
                      </label>
                    {/each}
                    {#each draftAdvanced.test_execution_statuses.filter((status) => !executionStatuses.includes(status as (typeof executionStatuses)[number])) as status (status)}
                      <label>
                        <input
                          type="checkbox"
                          checked
                          onchange={(event) =>
                            toggleExecutionStatus(
                              status as (typeof executionStatuses)[number],
                              event.currentTarget.checked,
                            )}
                        />
                        Unsupported: {status}
                      </label>
                    {/each}
                  </div>
                </fieldset>
                <label class="filter-control" for="filter-artefact-is-archived">
                  Artefact archived
                  <select
                    id="filter-artefact-is-archived"
                    name="artefact_is_archived"
                    value={draftAdvanced.artefact_is_archived === null
                      ? ""
                      : String(draftAdvanced.artefact_is_archived)}
                    onchange={(event) =>
                      setBooleanFilter(
                        "artefact_is_archived",
                        event.currentTarget.value,
                      )}
                  >
                    <option value="">Any</option><option value="true"
                      >Yes</option
                    ><option value="false">No</option>
                  </select>
                </label>
                <label class="filter-control" for="filter-rerun-is-requested">
                  Rerun requested
                  <select
                    id="filter-rerun-is-requested"
                    name="rerun_is_requested"
                    value={draftAdvanced.rerun_is_requested === null
                      ? ""
                      : String(draftAdvanced.rerun_is_requested)}
                    onchange={(event) =>
                      setBooleanFilter(
                        "rerun_is_requested",
                        event.currentTarget.value,
                      )}
                  >
                    <option value="">Any</option><option value="true"
                      >Yes</option
                    ><option value="false">No</option>
                  </select>
                </label>
                <label class="filter-control" for="filter-execution-is-latest">
                  Execution version
                  <select
                    id="filter-execution-is-latest"
                    name="execution_is_latest"
                    value={draftAdvanced.execution_is_latest === null
                      ? ""
                      : String(draftAdvanced.execution_is_latest)}
                    onchange={(event) =>
                      setBooleanFilter(
                        "execution_is_latest",
                        event.currentTarget.value,
                      )}
                  >
                    <option value="">Any</option><option value="true"
                      >Latest only</option
                    ><option value="false">Older only</option>
                  </select>
                </label>
                <fieldset class="filter-control advanced-control">
                  <legend>Issues</legend>
                  <div class="choice-list">
                    <label
                      ><input
                        type="radio"
                        name="issues-mode"
                        value="ids"
                        checked={Array.isArray(draftAdvanced.issues)}
                        onchange={() => setIdMode("issues", "ids")}
                      /> Specific IDs</label
                    >
                    <label
                      ><input
                        type="radio"
                        name="issues-mode"
                        value="any"
                        checked={draftAdvanced.issues === "any"}
                        onchange={() => setIdMode("issues", "any")}
                      /> Has any issue</label
                    >
                    <label
                      ><input
                        type="radio"
                        name="issues-mode"
                        value="none"
                        checked={draftAdvanced.issues === "none"}
                        onchange={() => setIdMode("issues", "none")}
                      /> Has no issue</label
                    >
                  </div>
                  {#if Array.isArray(draftAdvanced.issues)}
                    <SearchSuggestionPicker
                      field="issues"
                      onselect={(values) => addIds("issues", values)}
                    />
                    <ul class="selected-ids" aria-label="Selected issue IDs">
                      {#each issueIds as id (id)}<li>
                          Issue #{id}
                          <button
                            type="button"
                            aria-label="Remove issue {id}"
                            onclick={() => removeId("issues", id)}
                            >Remove</button
                          >
                        </li>{/each}
                    </ul>
                  {/if}
                </fieldset>
                <fieldset class="filter-control advanced-control">
                  <legend>Reviewers</legend>
                  <div class="choice-list">
                    <label
                      ><input
                        type="radio"
                        name="reviewer_ids-mode"
                        value="ids"
                        checked={Array.isArray(draftAdvanced.reviewer_ids)}
                        onchange={() => setIdMode("reviewer_ids", "ids")}
                      /> Specific IDs</label
                    >
                    <label
                      ><input
                        type="radio"
                        name="reviewer_ids-mode"
                        value="any"
                        checked={draftAdvanced.reviewer_ids === "any"}
                        onchange={() => setIdMode("reviewer_ids", "any")}
                      /> Has any reviewer</label
                    >
                    <label
                      ><input
                        type="radio"
                        name="reviewer_ids-mode"
                        value="none"
                        checked={draftAdvanced.reviewer_ids === "none"}
                        onchange={() => setIdMode("reviewer_ids", "none")}
                      /> Has no reviewer</label
                    >
                  </div>
                  {#if Array.isArray(draftAdvanced.reviewer_ids)}
                    <SearchSuggestionPicker
                      field="reviewer_ids"
                      onselect={(values) => addIds("reviewer_ids", values)}
                    />
                    <ul class="selected-ids" aria-label="Selected reviewer IDs">
                      {#each reviewerIds as id (id)}<li>
                          Reviewer #{id}
                          <button
                            type="button"
                            aria-label="Remove reviewer {id}"
                            onclick={() => removeId("reviewer_ids", id)}
                            >Remove</button
                          >
                        </li>{/each}
                    </ul>
                  {/if}
                </fieldset>
                <div class="filter-control metadata-control wide-control">
                  <span class="control-label">Execution metadata</span>
                  <SearchMetadataEditor
                    bind:value={draftAdvanced.execution_metadata}
                    onedit={() => editDraft("execution_metadata")}
                  />
                </div>
              </div>
              <p class="section-note">
                Specific Issue and Reviewer IDs are ORed; use any/none instead
                when filtering for presence or absence.
              </p>
            </section>
          </div>
          <SidePanel.Content.Footer>
            <button
              class="pager-button drawer-close-button"
              type="button"
              onclick={() => {
                close();
                restoreFilterDrawerFocus();
              }}>Close</button
            >
            {#if canClearDrafts()}
              <button
                class="pager-button clear-all-button"
                type="button"
                onclick={clearDrafts}>Clear all</button
              >
            {/if}
            <button
              class="pager-button search-button"
              type="submit"
              disabled={!canApplySearch}>Search</button
            >
          </SidePanel.Content.Footer>
        </form>
      </SidePanel.Content>
    {/snippet}
  </SidePanel>

  {#if unapplied}
    <p class="draft-notice" role="status">
      Changes not applied. Search to update results.
    </p>
  {/if}
  {#if draftProblems.length > 0 && !filterDrawerOpen}
    <div class="state-message error-message" role="alert">
      <h2>Invalid filter draft</h2>
      <ul>
        {#each draftProblems as problem (problem)}<li>{problem}</li>{/each}
      </ul>
      <p>No request was sent. Correct the filter values before searching.</p>
    </div>
  {/if}

  {#if familyRefreshPending && unknownUrlFamilies.length > 0}
    <p class="state-message" role="status" aria-live="polite">
      Refreshing the family list…
    </p>
  {:else if isInvalid}
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
      {#if familyValidationProblem.length > 0}
        <button
          class="retry-button"
          type="button"
          disabled={familyRefreshPending}
          onclick={retry}>Retry</button
        >
      {/if}
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
    --search-filter-drawer-width: min(34rem, 44vw);
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

  .filter-toolbar {
    display: flex;
    flex: 0 0 auto;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .filters-toggle {
    color: var(--lp-color-text-default, #222);
  }

  :global(.search-filter-panel) {
    --dimension-width-modal: var(--search-filter-drawer-width);
    width: min(100vw, var(--dimension-width-modal));
    max-width: min(34rem, 100vw);
    height: 100vh;
    height: 100dvh;
    max-height: none;
    border: 0;
    background: var(--lp-color-background-default, #fff);
  }

  :global(.search-filter-panel .ds.dialog-content) {
    height: 100%;
    min-height: 0;
    gap: 0;
    padding: 0;
  }

  .filter-form {
    display: flex;
    flex: 1 1 auto;
    flex-direction: column;
    min-height: 0;
  }

  :global(.search-filter-panel .ds.dialog-content-header) {
    flex: 0 0 auto;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--lp-color-border-default, #ccc);
  }

  :global(.search-filter-panel .ds.dialog-content-header h2) {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 500;
  }

  .filter-panel-body {
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    padding: 0.75rem 1.25rem 1rem;
  }

  .filter-guidance,
  .section-note {
    margin: 0.25rem 0 0.75rem;
    color: var(--lp-color-text-muted, #666);
    font-size: 0.8125rem;
    line-height: 1.4;
  }

  .filter-guidance code {
    color: var(--lp-color-text-default, #222);
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  }

  .filter-section {
    min-width: 0;
    margin: 0 0 1rem;
    padding: 0 0 0.875rem;
    border-bottom: 1px solid var(--lp-color-border-default, #ccc);
  }

  .filter-section h3 {
    margin: 0 0 0.5rem;
    font-size: 1rem;
    font-weight: 500;
  }

  .filter-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
  }

  .filter-control {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.875rem;
  }

  .filter-control input:not([type="checkbox"]):not([type="radio"]),
  .filter-control textarea,
  .filter-control select {
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

  .filter-control textarea {
    resize: vertical;
  }

  .advanced-control {
    box-sizing: border-box;
    min-width: 0;
    margin: 0;
    padding: 0.625rem;
    border: 1px solid var(--lp-color-border-default, #ccc);
    border-radius: 0.25rem;
  }

  .wide-control {
    grid-column: 1 / -1;
  }

  .choice-list label,
  .selected-ids li {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin: 0.3rem 0;
  }

  .choice-list input[type="checkbox"],
  .choice-list input[type="radio"] {
    width: auto;
    min-height: auto;
    accent-color: var(--lp-color-brand-default, #06c);
  }

  .inline-entry {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .inline-entry input {
    flex: 1 1 auto;
    min-width: 0;
  }

  .metadata-control .control-label {
    font-weight: 500;
  }

  :global(.search-filter-panel .ds.dialog-content-footer) {
    flex: 0 0 auto;
    padding: 0.75rem 1.25rem;
    border-top: 1px solid var(--lp-color-border-default, #ccc);
    background: var(--lp-color-background-default, #fff);
  }

  .search-button {
    border-color: var(--lp-color-brand-default, #06c);
    background: var(--lp-color-brand-default, #06c);
    color: var(--lp-color-text-inverted, #fff);
  }

  .filter-control input:focus-visible,
  .filter-control textarea:focus-visible,
  .filter-control select:focus-visible,
  .filter-form button:focus-visible {
    outline: 2px solid var(--lp-color-brand-default, #06c);
    outline-offset: 1px;
  }

  .draft-notice {
    margin: 0 0 0.5rem;
    color: var(--lp-color-text-muted, #666);
    font-size: 0.8125rem;
  }

  .results-page.filters-open .grid-region,
  .results-page.filters-open .pager {
    margin-right: var(--search-filter-drawer-width);
  }

  .filter-draft-errors {
    margin: 0 0 1rem;
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
    box-sizing: border-box;
    border: 1px solid var(--lp-color-border-default, #ccc);
    border-radius: 0.25rem;
    background: var(--lp-color-background-default, #fff);
    color: var(--lp-color-text-default, #222);
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

    .results-page {
      --search-filter-drawer-width: 100vw;
    }

    .results-page.filters-open .grid-region,
    .results-page.filters-open .pager {
      margin-right: 0;
    }

    :global(.search-filter-panel) {
      --dimension-width-modal: 100vw;
      width: 100vw;
      max-width: 100vw;
    }

    .filter-grid {
      grid-template-columns: minmax(0, 1fr);
    }

    .wide-control {
      grid-column: auto;
    }
  }
</style>
