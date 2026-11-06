<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { onDestroy, tick, untrack } from "svelte";
  import { SvelteURLSearchParams } from "svelte/reactivity";
  import {
    Button,
    Link,
    Spinner,
    SidePanel,
    Table,
  } from "@canonical/svelte-ds-app-launchpad";
  import { SearchIcon } from "@canonical/svelte-icons";
  import { FetchError, silentApi } from "$lib/api/client";
  import { getApiRoot } from "$lib/config";
  import { userStore } from "$lib/stores/user.svelte";
  import type { Family } from "$lib/types";
  import { familyDisplayName } from "$lib/types";
  import { formatUtcDateTime } from "$lib/formatUtcDateTime.js";
  import {
    cloneFilters,
    editedSearchParams,
    emptyFilters,
    filtersEqual,
    hasFilters,
    parseSearchPage,
    SEARCH_PAGE_FILTERS,
    searchQueryString,
    toSearchGridRow,
    type SearchFilter,
    type SearchGridRow,
    type SearchResultDetails as SearchResultDetailsData,
    type SearchTableResponse,
  } from "$lib/testResultsSearch";
  import {
    loadSearchOptionsPage,
    parseSearchOptions,
    resetSearchOptionsPage,
    searchOptionsAccessErrorFor,
    searchOptionsPageParams,
    searchOptionsPageRange,
    searchOptionsPageSizeParams,
  } from "$lib/searchOptionsPagination";
  import type { SearchOptionsAccessError } from "$lib/searchOptionsPagination";
  import SearchGridFilterHeader from "./SearchGridFilterHeader.svelte";
  import SearchGridFilterMenu from "./SearchGridFilterMenu.svelte";
  import SearchConditions from "./SearchConditions.svelte";
  import SearchGridValueCell from "./SearchGridValueCell.svelte";
  import SearchGridValueDialog from "./SearchGridValueDialog.svelte";
  import ViewRunLink from "./ViewRunLink.svelte";
  import DetailsButton from "./DetailsButton.svelte";
  import SearchResultDetails from "./SearchResultDetails.svelte";

  let {
    url,
    routePath,
    families,
    base,
    navigate,
    variant = 2,
  }: {
    url: URL;
    routePath: string;
    families: Family[];
    base: string;
    navigate: (url: string | URL) => Promise<unknown>;
    variant?: 2 | 3 | 4;
  } = $props();

  interface SearchGridValueItem {
    key: string;
    label: string;
    detail?: string;
    href?: string;
    ariaLabel?: string;
  }

  let drafts = $state(emptyFilters());
  let editedFields = $state<SearchFilter[]>([]);
  let moving = $state(false);
  let navigationError = $state(false);
  let response = $state.raw<SearchTableResponse | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let accessError = $state<SearchOptionsAccessError | null>(null);
  let retryGeneration = $state(0);
  let reapply = $state(0);
  let requestGeneration = 0;
  let detailsGeneration = 0;
  let detailsRequest: AbortController | null = null;
  let detailsResult = $state<SearchResultDetailsData | null>(null);
  let detailsLoading = $state(false);
  let detailsError = $state<string | null>(null);
  interface DetailsSelection {
    resultId: number;
    key: string;
    trigger: HTMLButtonElement;
  }
  interface ValueDialogSelection {
    heading: string;
    itemLabel: string;
    items: SearchGridValueItem[];
    itemLayout?: "metadata-table";
    ownerKey: string;
    trigger: HTMLButtonElement;
  }
  let selectedDetails = $state<DetailsSelection | null>(null);
  let invalidatedDetails = $state<DetailsSelection | null>(null);
  let activeValueDialog = $state<ValueDialogSelection | null>(null);
  let invalidatedValueDialog = $state<ValueDialogSelection | null>(null);
  let tableRegion = $state<HTMLElement>();
  let filterPanelOpen = $state(false);
  let filterPanelTrigger = $state<HTMLButtonElement>();
  let filterPanelBody = $state<HTMLElement>();
  let live = true;

  const filterGroups: { label: string; key: SearchFilter }[] = [
    { label: "Created", key: "from_date" },
    { label: "Family", key: "families" },
    { label: "Artefact", key: "artefacts" },
    { label: "Stage", key: "artefact_stages" },
    { label: "Archived", key: "artefact_is_archived" },
    { label: "Test Case", key: "test_cases" },
    { label: "Execution Status", key: "test_execution_statuses" },
    { label: "Rerun Requested", key: "rerun_is_requested" },
    { label: "Latest Execution", key: "execution_is_latest" },
    { label: "Result status", key: "test_result_statuses" },
    { label: "Track", key: "artefact_tracks" },
    { label: "Version", key: "artefact_versions" },
    { label: "Environment", key: "environments" },
    { label: "Test Plan", key: "test_plans" },
    { label: "Template ID", key: "template_ids" },
    { label: "Issues", key: "issues" },
    { label: "Reviewers", key: "reviewer_ids" },
    { label: "Execution Metadata", key: "execution_metadata" },
  ];

  const search = $derived(parseSearchOptions(url.searchParams, families));
  let selectedPageSize = $derived(search.pageSize);
  const queryString = $derived(searchQueryString(url.searchParams));
  const filterParams = $derived.by(() => {
    const params = new SvelteURLSearchParams(url.searchParams);
    params.delete("page");
    params.delete("page_size");
    return params;
  });
  const appliedFilterKey = $derived(searchQueryString(filterParams));
  const applied = $derived(parseSearchPage(filterParams, families));
  const invalidFields = $derived(
    SEARCH_PAGE_FILTERS.filter(
      (key) =>
        applied.problems.some((problem) =>
          problem.startsWith(`Invalid ${key}:`),
        ) ||
        ((key === "from_date" || key === "until_date") &&
          applied.problems.some((problem) =>
            problem.startsWith("Invalid date range:"),
          )),
    ),
  );
  const chipInvalidFields = $derived(
    invalidFields.filter((key) => !editedFields.includes(key)),
  );
  const datasetKey = $derived(
    `${url.origin}${url.pathname}?${queryString}:${reapply}`,
  );
  const unapplied = $derived(
    !filtersEqual(drafts, applied.filters) ||
      editedFields.some((key) => invalidFields.includes(key)),
  );
  const hasDrafts = $derived(hasFilters(drafts));
  const range = $derived(response ? searchOptionsPageRange(response) : null);
  const rows = $derived(
    response?.rows.map((row) => toSearchGridRow(row, families, base)) ?? [],
  );
  let draftResetFilterKey: string | null = null;
  let draftResetGeneration = -1;

  onDestroy(() => {
    live = false;
    detailsRequest?.abort();
  });

  $effect.pre(() => {
    const filterKey = appliedFilterKey;
    const generation = reapply;
    if (
      filterKey === draftResetFilterKey &&
      generation === draftResetGeneration
    )
      return;
    draftResetFilterKey = filterKey;
    draftResetGeneration = generation;
    untrack(() => {
      drafts = cloneFilters(applied.filters);
      editedFields = [];
    });
  });

  $effect.pre(() => {
    if (selectedDetails && selectedDetails.key !== datasetKey) {
      invalidatedDetails = selectedDetails;
      discardDetails();
    }
    if (
      activeValueDialog &&
      !activeValueDialog.ownerKey.startsWith(`${datasetKey}:`)
    ) {
      invalidatedValueDialog = activeValueDialog;
      activeValueDialog = null;
    }
  });

  $effect(() => {
    const requestUrl = url.href;
    const query = parseSearchOptions(url.searchParams, families);
    const attempt = retryGeneration;
    void reapply;
    const generation = ++requestGeneration;
    response = null;
    error = null;
    accessError = null;
    if (query.problems.length) {
      loading = false;
      return;
    }

    const controller = new AbortController();
    loading = true;
    void loadSearchOptionsPage(query.filters, query.page, query.pageSize, {
      signal: controller.signal,
    })
      .then((result) => {
        if (
          generation === requestGeneration &&
          attempt === retryGeneration &&
          requestUrl === url.href
        )
          response = result;
      })
      .catch(async (requestError: unknown) => {
        if (
          controller.signal.aborted ||
          generation !== requestGeneration ||
          attempt !== retryGeneration
        )
          return;
        if (
          requestError instanceof FetchError &&
          (requestError.status === 401 || requestError.status === 403)
        ) {
          const auth = await userStore.refresh(
            globalThis.fetch,
            controller.signal,
          );
          if (
            controller.signal.aborted ||
            generation !== requestGeneration ||
            attempt !== retryGeneration
          )
            return;
          accessError = searchOptionsAccessErrorFor(requestError.status, auth);
        } else {
          error =
            "Could not load test results. Check your connection and try again.";
        }
      })
      .finally(() => {
        if (generation === requestGeneration && attempt === retryGeneration)
          loading = false;
      });
    return () => controller.abort();
  });

  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(url.href)}`,
  );

  function navigateWith(params: URLSearchParams) {
    const query = params.toString();
    return navigate(query ? `${routePath}?${query}` : routePath);
  }

  async function go(params: URLSearchParams) {
    if (moving) return;
    moving = true;
    navigationError = false;
    const query = params.toString();
    const target = query ? `${routePath}?${query}` : routePath;
    try {
      if (new URL(target, url.origin).href === url.href) reapply += 1;
      else await navigate(target);
    } catch {
      navigationError = true;
    } finally {
      moving = false;
    }
  }

  function apply() {
    if (moving) return;
    filterPanelOpen = false;
    const params = resetSearchOptionsPage(
      editedSearchParams(drafts, url.searchParams, editedFields),
    );
    void go(params);
  }

  function clearAll() {
    if (moving) return;
    filterPanelOpen = false;
    drafts = emptyFilters();
    editedFields = [];
    const params = new SvelteURLSearchParams();
    const currentSize = url.searchParams.getAll("page_size");
    if (
      currentSize.length === 1 &&
      (currentSize[0] === "25" ||
        currentSize[0] === "50" ||
        currentSize[0] === "100")
    )
      params.set("page_size", currentSize[0]);
    void go(params);
  }

  function onFilterEdit(key: SearchFilter, next: typeof drafts) {
    drafts = next;
    if (!editedFields.includes(key)) editedFields = [...editedFields, key];
  }

  function goToPage(page: number) {
    return navigateWith(searchOptionsPageParams(url.searchParams, page));
  }

  function changePageSize(event: Event) {
    const pageSize = Number((event.currentTarget as HTMLSelectElement).value);
    if (pageSize !== 25 && pageSize !== 50 && pageSize !== 100)
      return Promise.resolve();
    selectedPageSize = pageSize;
    return navigateWith(
      searchOptionsPageSizeParams(url.searchParams, pageSize),
    );
  }

  async function openFilterPanel(event: MouseEvent) {
    filterPanelTrigger = event.currentTarget as HTMLButtonElement;
    filterPanelOpen = true;
    await tick();
    filterPanelBody
      ?.querySelector<HTMLElement>("input, select, button")
      ?.focus({ preventScroll: true });
  }

  function restoreFilterTriggerFocus() {
    filterPanelOpen = false;
    void tick().then(() => filterPanelTrigger?.focus({ preventScroll: true }));
  }

  function retry() {
    error = null;
    accessError = null;
    retryGeneration += 1;
  }

  function discardDetails() {
    ++detailsGeneration;
    detailsRequest?.abort();
    detailsRequest = null;
    selectedDetails = null;
    detailsResult = null;
    detailsLoading = false;
    detailsError = null;
  }

  async function loadDetails(resultId: number, trigger: HTMLButtonElement) {
    detailsRequest?.abort();
    const generation = ++detailsGeneration;
    const key = datasetKey;
    const request = new AbortController();
    detailsRequest = request;
    selectedDetails = { resultId, key, trigger };
    detailsResult = null;
    detailsError = null;
    detailsLoading = true;
    try {
      const details = await silentApi<SearchResultDetailsData>(
        `test-results/search-page/${resultId}`,
        { signal: request.signal },
      );
      if (!details) throw new Error("The details endpoint returned no result.");
      if (details.test_result.id !== resultId)
        throw new Error("The details endpoint returned a different result.");
      if (
        !live ||
        generation !== detailsGeneration ||
        selectedDetails?.resultId !== resultId ||
        selectedDetails.key !== datasetKey ||
        !response?.rows.some((row) => row.test_result.id === resultId)
      )
        return;
      detailsResult = details;
    } catch {
      if (!live || request.signal.aborted || generation !== detailsGeneration)
        return;
      detailsError =
        "Could not load result details. Check your connection and try again.";
    } finally {
      if (generation === detailsGeneration) {
        detailsLoading = false;
        detailsRequest = null;
      }
    }
  }

  function showDetails(resultId: number, trigger: HTMLButtonElement) {
    if (
      !live ||
      loading ||
      !response?.rows.some((row) => row.test_result.id === resultId)
    )
      return;
    trigger.focus({ preventScroll: true });
    invalidatedDetails = null;
    void loadDetails(resultId, trigger);
  }

  function closeDetails() {
    const previous = selectedDetails ?? invalidatedDetails;
    invalidatedDetails = null;
    if (selectedDetails) discardDetails();
    if (!previous || !live) return;
    const sameDataset = previous.key === datasetKey;
    const target =
      sameDataset &&
      previous.trigger.isConnected &&
      previous.trigger.dataset.testResultId === String(previous.resultId)
        ? previous.trigger
        : tableRegion;
    if (target?.isConnected) target.focus({ preventScroll: true });
  }

  function showValueDialog(
    heading: string,
    itemLabel: string,
    items: SearchGridValueItem[],
    ownerKey: string,
    trigger: HTMLButtonElement,
    itemLayout?: "metadata-table",
  ) {
    trigger.focus({ preventScroll: true });
    invalidatedValueDialog = null;
    activeValueDialog = {
      heading,
      itemLabel,
      items: items.map((item) => ({ ...item })),
      itemLayout,
      ownerKey: `${datasetKey}:${ownerKey}`,
      trigger,
    };
  }

  function closeValueDialog() {
    const previous = activeValueDialog ?? invalidatedValueDialog;
    invalidatedValueDialog = null;
    if (!previous) return;
    activeValueDialog = null;
    if (!live) return;
    const sameDataset = previous.ownerKey.startsWith(`${datasetKey}:`);
    const target =
      sameDataset &&
      previous.trigger.isConnected &&
      previous.trigger.dataset.searchGridValueOwner ===
        previous.ownerKey.slice(datasetKey.length + 1)
        ? previous.trigger
        : tableRegion;
    if (target?.isConnected) target.focus({ preventScroll: true });
  }

  function issueItems(row: SearchGridRow): SearchGridValueItem[] {
    return row.issues.map((issue) => ({
      key: String(issue.id),
      label: `#${issue.id}${issue.key ? ` · ${issue.key}` : ""}`,
      detail: issue.title,
      href: `${base}/issues/${issue.id}`,
      ariaLabel: `View issue ${issue.key || issue.id}`,
    }));
  }

  function reviewerItems(row: SearchGridRow): SearchGridValueItem[] {
    return row.reviewers.map((reviewer) => ({
      key: String(reviewer.id),
      label: reviewer.name || `#${reviewer.id}`,
      detail: reviewer.launchpad_handle
        ? `@${reviewer.launchpad_handle}`
        : undefined,
    }));
  }

  function metadataItems(row: SearchGridRow): SearchGridValueItem[] {
    return row.executionMetadata.map((pair, index) => ({
      key: `${index}:${pair.category}`,
      label: pair.category,
      detail: pair.value,
    }));
  }
</script>

<svelte:head>
  <title>Search (Option {variant}) — Test Observer</title>
</svelte:head>

<section class="search-page" aria-labelledby="search-option-title">
  <h1 id="search-option-title">Search (Option {variant})</h1>
  {#if variant === 2}
    <p>
      Set exact server-side filters from the result columns, then Search. Values
      within a field match any; different fields must all match.
    </p>
  {:else if variant === 3}
    <p>
      Set exact server-side filters in the filter panel, then Search. Values
      within a field match any; different fields must all match.
    </p>
  {:else}
    <p>
      Add or edit exact server-side filter chips, then Search. Values within a
      field match any; different fields must all match.
    </p>
  {/if}
  <div class="filter-actions" role="group" aria-label="Test result filters">
    {#if variant === 3}
      <Button
        type="button"
        density="dense"
        aria-haspopup="dialog"
        aria-controls="search-option-3-filter-panel"
        aria-expanded={filterPanelOpen}
        onclick={openFilterPanel}>Filters</Button
      >
    {/if}
    {#if variant === 4}
      <SearchConditions
        bind:filters={drafts}
        {families}
        invalidFields={chipInvalidFields}
        disabled={moving}
        onedit={onFilterEdit}
      />
    {/if}
    <form
      aria-label="Apply confirmed search filters"
      onsubmit={(event) => {
        event.preventDefault();
        apply();
      }}
    >
      <Button type="submit" severity="brand" density="dense" disabled={moving}>
        {#snippet iconLeft()}<SearchIcon />{/snippet}
        Search
      </Button>
      {#if hasDrafts || url.search}
        <Button
          type="button"
          density="dense"
          onclick={clearAll}
          disabled={moving}>Clear all</Button
        >
      {/if}
    </form>
  </div>
  {#if variant === 3}
    <SidePanel
      id="search-option-3-filter-panel"
      class="search-option-filter-panel"
      aria-labelledby="search-option-3-filter-title"
      bind:open={filterPanelOpen}
      onclose={restoreFilterTriggerFocus}
    >
      {#snippet children(commandfor, close)}
        <SidePanel.Content>
          <SidePanel.Content.Header>
            <h2 id="search-option-3-filter-title">Test result filters</h2>
            <SidePanel.Content.Header.CloseButton
              {commandfor}
              command="close"
              aria-label="Close filters"
              onclick={() => {
                close();
                restoreFilterTriggerFocus();
              }}
            />
          </SidePanel.Content.Header>
          <SidePanel.Content.Body>
            <div class="filter-panel-body" bind:this={filterPanelBody}>
              {#each filterGroups as group (group.key)}
                <section
                  class="filter-group"
                  aria-labelledby={`search-option-3-filter-${group.key}`}
                >
                  <h3 id={`search-option-3-filter-${group.key}`}>
                    {group.label}
                  </h3>
                  <SearchGridFilterMenu
                    filterKey={group.key}
                    filters={drafts}
                    {families}
                    {invalidFields}
                    disabled={moving}
                    open={filterPanelOpen}
                    deferIdLabelHydration
                    onedit={onFilterEdit}
                  />
                </section>
              {/each}
            </div>
          </SidePanel.Content.Body>
          <SidePanel.Content.Footer>
            <Button
              type="button"
              density="dense"
              onclick={() => {
                close();
                restoreFilterTriggerFocus();
              }}>Close</Button
            >
            <Button
              type="button"
              density="dense"
              disabled={moving}
              onclick={clearAll}>Clear all</Button
            >
            <Button
              type="button"
              severity="brand"
              density="dense"
              disabled={moving}
              onclick={() => {
                apply();
                close();
              }}>Search</Button
            >
          </SidePanel.Content.Footer>
        </SidePanel.Content>
      {/snippet}
    </SidePanel>
  {/if}
  {#if unapplied}
    <p class="draft-notice" role="status">
      Changes not applied. Search to update results{!hasDrafts
        ? " and clear the previous query"
        : ""}.
    </p>
  {/if}
  {#if navigationError}
    <p role="alert">Could not update the search URL. Please try again.</p>
  {/if}

  <section class="results" aria-label="Search results" aria-busy={loading}>
    {#if applied.hasFilters && !search.problems.length}
      <div class="applied-query-actions">
        <h2>
          {unapplied
            ? "Results for previous query"
            : "Results for applied query"}
        </h2>
      </div>
    {/if}
    {#if search.problems.length}
      <div role="alert">
        <h2>Search not applied</h2>
        <ul>
          {#each search.problems as problem (problem)}<li>{problem}</li>{/each}
        </ul>
        <p>
          No request was sent. Correct the invalid filters or URL, or clear all
          filters. Untouched invalid or unknown URL conditions are preserved
          when searching.
        </p>
      </div>
    {/if}
    {#if !search.problems.length}
      {#if accessError === "requiresLogin"}
        <div role="status">
          <p>You need to be logged in to search test results.</p>
          <Link href={loginUrl}>Log in</Link>
        </div>
      {:else if accessError === "forbidden"}
        <div role="alert">
          <p>
            You don't have permission to view these test results. Contact an
            administrator if this is a mistake.
          </p>
          <Button onclick={retry}>Retry</Button>
        </div>
      {:else if accessError === "sessionCheckFailed"}
        <div role="alert">
          <p>
            We couldn't verify your session. Check your connection and try
            again.
          </p>
          <Button onclick={retry}>Retry</Button>
        </div>
      {:else if error}
        <div role="alert">
          <p>{error}</p>
          <Button onclick={retry}>Retry</Button>
        </div>
      {:else}
        {#if loading || !response}
          <div class="loading" role="status">
            <Spinner /> Loading test results…
          </div>
        {:else if range}
          <p class="count" role="status" aria-live="polite">
            {#if range.start}
              Showing {range.start}–{range.end} of {range.count} results
            {:else if range.count === 0}
              No test results (0 total)
            {:else}
              No results on this page ({range.count} total)
            {/if}
          </p>
        {/if}
      {/if}
    {/if}

    <div
      class="table-scroll"
      bind:this={tableRegion}
      role="region"
      aria-label="Search results table"
      tabindex="-1"
    >
      {#if variant === 3 || variant === 4}
        <Table
          class="search-option-table search-option-table-compact"
          aria-label="Test results"
        >
          <thead>
            <tr>
              <th scope="col">Created</th>
              <th scope="col">Artefact</th>
              <th scope="col">Test Case</th>
              <th scope="col">Test Execution ID</th>
              <th scope="col">Status</th>
              <th scope="col">Track</th>
              <th scope="col">Version</th>
              <th scope="col">Environment</th>
              <th scope="col">Test Plan</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each rows as row (row.id)}
              <tr>
                <td>{formatUtcDateTime(row.createdAt)}</td>
                <td>{row.artefact}</td>
                <td>
                  <div class="compact-test-case">
                    <span>{row.testCase}</span>
                    {#if row.category}<span class="compact-category"
                        >{row.category}</span
                      >{/if}
                  </div>
                </td>
                <td>{row.execution}</td>
                <td class="compact-status">{row.status}</td>
                <td>{row.track}</td>
                <td>{row.version}</td>
                <td title="{row.architecture}/{row.environment}">
                  {row.architecture}/{row.environment}
                </td>
                <td>{row.testPlan || "Unknown"}</td>
                <td>
                  <div class="compact-actions">
                    <DetailsButton
                      name={row.testCase}
                      resultId={row.id}
                      prepare={() =>
                        document.dispatchEvent(
                          new Event("search-grid-close-menus"),
                        )}
                      show={(trigger) => showDetails(row.id, trigger)}
                    />
                    <ViewRunLink href={row.href} name={row.testCase} />
                  </div>
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="10">
                  {#if search.problems.length}
                    Correct or clear the blocked search to load results.
                  {:else if loading || !response}
                    Loading test results…
                  {:else}
                    No test results match the applied conditions.
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </Table>
      {:else}
        <Table class="search-option-table" aria-label="Test results">
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Details</th>
              <th scope="col">{@render filterHeader("Created", "from_date")}</th
              >
              <th scope="col">{@render filterHeader("Family", "families")}</th>
              <th scope="col"
                >{@render filterHeader("Artefact", "artefacts")}</th
              >
              <th scope="col"
                >{@render filterHeader("Stage", "artefact_stages")}</th
              >
              <th scope="col"
                >{@render filterHeader("Archived", "artefact_is_archived")}</th
              >
              <th scope="col"
                >{@render filterHeader("Test Case", "test_cases")}</th
              >
              <th scope="col">Category</th>
              <th scope="col">Execution ID</th>
              <th scope="col"
                >{@render filterHeader(
                  "Execution Status",
                  "test_execution_statuses",
                )}</th
              >
              <th scope="col"
                >{@render filterHeader(
                  "Rerun Requested",
                  "rerun_is_requested",
                )}</th
              >
              <th scope="col"
                >{@render filterHeader(
                  "Latest Execution",
                  "execution_is_latest",
                )}</th
              >
              <th scope="col"
                >{@render filterHeader(
                  "Result status",
                  "test_result_statuses",
                )}</th
              >
              <th scope="col"
                >{@render filterHeader("Track", "artefact_tracks")}</th
              >
              <th scope="col"
                >{@render filterHeader("Version", "artefact_versions")}</th
              >
              <th scope="col">Architecture</th>
              <th scope="col"
                >{@render filterHeader("Environment", "environments")}</th
              >
              <th scope="col"
                >{@render filterHeader("Test Plan", "test_plans")}</th
              >
              <th scope="col"
                >{@render filterHeader("Template ID", "template_ids")}</th
              >
              <th scope="col">{@render filterHeader("Issues", "issues")}</th>
              <th scope="col"
                >{@render filterHeader("Reviewers", "reviewer_ids")}</th
              >
              <th scope="col"
                >{@render filterHeader(
                  "Execution Metadata",
                  "execution_metadata",
                )}</th
              >
            </tr>
          </thead>
          <tbody>
            {#each rows as row (row.id)}
              {@const configuredFamily = families.find(
                (family) => family.api_name === row.family,
              )}
              <tr>
                <td><ViewRunLink href={row.href} name={row.testCase} /></td>
                <td>
                  <DetailsButton
                    name={row.testCase}
                    resultId={row.id}
                    prepare={() =>
                      document.dispatchEvent(
                        new Event("search-grid-close-menus"),
                      )}
                    show={(trigger) => showDetails(row.id, trigger)}
                  />
                </td>
                <td>{formatUtcDateTime(row.createdAt)}</td>
                <td>
                  {configuredFamily
                    ? familyDisplayName(configuredFamily)
                    : row.family}
                </td>
                <td>{row.artefact}</td>
                <td>{row.stage === "" ? "(none)" : (row.stage ?? "—")}</td>
                <td>{row.archived ? "Yes" : "No"}</td>
                <td>{row.testCase}</td>
                <td>{row.category}</td>
                <td>{row.execution}</td>
                <td>{row.executionStatus}</td>
                <td>{row.rerunRequested ? "Yes" : "No"}</td>
                <td>{row.latestExecution ? "Yes" : "No"}</td>
                <td>{row.status}</td>
                <td>{row.track}</td>
                <td>{row.version}</td>
                <td>{row.architecture}</td>
                <td>{row.environment}</td>
                <td>{row.testPlan}</td>
                <td>{row.templateId}</td>
                <td>
                  <SearchGridValueCell
                    heading="Issues"
                    itemLabel="issue"
                    items={issueItems(row)}
                    ownerKey={`${row.id}:issues`}
                    onshow={showValueDialog}
                  />
                </td>
                <td>
                  <SearchGridValueCell
                    heading="Reviewers"
                    itemLabel="reviewer"
                    items={reviewerItems(row)}
                    ownerKey={`${row.id}:reviewers`}
                    onshow={showValueDialog}
                  />
                </td>
                <td>
                  <SearchGridValueCell
                    heading="Execution Metadata"
                    itemLabel="metadata pair"
                    itemLayout="metadata-table"
                    items={metadataItems(row)}
                    ownerKey={`${row.id}:executionMetadata`}
                    onshow={showValueDialog}
                  />
                </td>
              </tr>
            {:else}
              <tr>
                <td colspan="23">
                  {#if search.problems.length}
                    Correct or clear the blocked search to load results.
                  {:else if loading || !response}
                    Loading test results…
                  {:else}
                    No test results match the applied conditions.
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </Table>
      {/if}
    </div>

    {#if !search.problems.length && response && range}
      <nav class="pager" aria-label="Test result pages">
        <Button
          type="button"
          density="dense"
          onclick={() => void goToPage(search.page - 1)}
          disabled={moving || search.page <= 1}>Previous</Button
        >
        <span>Page {search.page}</span>
        <Button
          type="button"
          density="dense"
          onclick={() => void goToPage(search.page + 1)}
          disabled={moving || search.page * search.pageSize >= range.count}
          >Next</Button
        >
        <label>
          Results per page
          <select bind:value={selectedPageSize} onchange={changePageSize}>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>
      </nav>
    {/if}
  </section>
</section>

<SearchResultDetails
  result={detailsResult}
  active={selectedDetails !== null}
  loading={detailsLoading}
  error={detailsError}
  {families}
  {base}
  onclose={closeDetails}
  onretry={() => {
    if (selectedDetails)
      void loadDetails(selectedDetails.resultId, selectedDetails.trigger);
  }}
/>
<SearchGridValueDialog
  selection={activeValueDialog}
  onclose={closeValueDialog}
/>

{#snippet filterHeader(label: string, filterKey: SearchFilter)}
  <SearchGridFilterHeader
    {label}
    {filterKey}
    filters={drafts}
    {families}
    disabled={moving}
    {invalidFields}
    onedit={onFilterEdit}
  />
{/snippet}

<style>
  .search-page {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: calc(100vh - 3rem);
    color: var(--lp-color-text-default);
  }
  h1 {
    margin: 0 0 0.75rem;
    font-size: 1.75rem;
    font-weight: 500;
  }
  .search-page > p {
    margin: 0;
    color: var(--lp-color-text-muted);
  }
  .filter-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }
  .filter-actions form {
    display: flex;
    gap: 0.5rem;
  }
  .draft-notice {
    margin: 0.75rem 0 0;
    color: var(--lp-color-text-muted);
  }
  .results {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
    margin-top: 0.75rem;
  }
  .applied-query-actions h2 {
    margin: 0 0 0.5rem;
    font-size: 1.125rem;
    font-weight: 500;
  }
  .loading,
  .count {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0 0 0.5rem;
  }
  .table-scroll {
    max-width: 100%;
    overflow: auto;
    overscroll-behavior: contain;
  }
  :global(.search-option-table) {
    width: max-content;
    min-width: 100%;
    white-space: nowrap;
  }
  :global(.search-option-table td) {
    max-width: 18rem;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  :global(.search-option-table td:nth-child(21)),
  :global(.search-option-table td:nth-child(22)),
  :global(.search-option-table td:nth-child(23)) {
    white-space: normal;
  }
  .pager {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }
  .pager label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-left: 0.5rem;
  }
  .pager select {
    min-height: 2rem;
    font: inherit;
  }
  :global(.search-option-filter-panel) {
    max-width: min(33.5rem, 100vw);
  }
  .filter-panel-body {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: calc(100vh - 11rem);
    overflow: auto;
    overscroll-behavior: contain;
  }
  .filter-group {
    min-width: 0;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--lp-color-border-default);
  }
  .filter-group h3 {
    margin: 0 0 0.25rem;
    font-size: 0.95rem;
    font-weight: 500;
  }
  .filter-group :global(.grid-filter-menu) {
    width: 100%;
    padding: 0;
    border: 0;
    border-radius: 0;
    box-shadow: none;
    background: transparent;
  }
  .filter-group :global(.grid-filter-menu > .hint) {
    margin-bottom: 0.4rem;
  }
  :global(.search-option-table-compact) {
    min-width: 1000px;
  }
  :global(.search-option-table-compact td) {
    max-width: 16rem;
    white-space: normal;
  }
  .compact-test-case {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    min-width: 8rem;
  }
  .compact-category {
    color: var(--lp-color-text-muted);
    font-size: 0.75rem;
  }
  .compact-status {
    font-size: 0.75rem;
    font-weight: 500;
  }
  .compact-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }
</style>
