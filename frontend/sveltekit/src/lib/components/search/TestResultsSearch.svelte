<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import { Button, Spinner, Link } from "@canonical/svelte-ds-app-launchpad";
  import { SearchIcon } from "@canonical/svelte-icons";
  import type { GridRowModel } from "@svgrid/grid";
  import { silentApi } from "$lib/api/client";
  import type { Family } from "$lib/types";
  import { getApiRoot } from "$lib/config";
  import { TestResultsSearchStore } from "$lib/stores/test-results-search.svelte";
  import {
    emptyFilters,
    cloneFilters,
    filtersEqual,
    hasFilters,
    editedSearchParams,
    parseSearchPage,
    searchQueryString,
    SEARCH_PAGE_FILTERS,
    type SearchFilter,
    type SearchGridRow,
    type SearchResultDetails as SearchResultDetailsData,
  } from "$lib/testResultsSearch";
  import SearchResultsGrid from "./SearchResultsGrid.svelte";
  import SearchResultDetails from "./SearchResultDetails.svelte";
  import { VIEW_PARAM } from "$lib/gridViewUrl";

  let {
    url,
    families,
    base,
    navigate,
    replaceView,
    normalizeUrl,
  }: {
    url: URL;
    families: Family[];
    base: string;
    navigate: (url: URL) => Promise<unknown>;
    replaceView: (
      encoded: string | null,
      sourceHref: string,
    ) => Promise<unknown>;
    normalizeUrl: (next: URL, sourceHref: string) => Promise<unknown>;
  } = $props();
  const store = new TestResultsSearchStore();
  let detailsGeneration = 0;
  let detailsRequest: AbortController | null = null;
  let detailsResult = $state<SearchResultDetailsData | null>(null);
  let detailsLoading = $state(false);
  let detailsError = $state<string | null>(null);
  const invalidSearchRowModel: GridRowModel<SearchGridRow> = {
    subscribe: () => () => 0,
    getRows: () => [],
    isLoading: () => false,
  };
  let live = true;
  onDestroy(() => {
    live = false;
    detailsRequest?.abort();
  });
  let grid = $state<ReturnType<typeof SearchResultsGrid> | null>(null);
  let selectedDetails = $state<{
    resultId: number;
    key: string;
    trigger: HTMLButtonElement;
  } | null>(null);
  let pageElement: HTMLElement;
  const queryString = $derived(searchQueryString(url.searchParams));
  const applied = $derived(
    parseSearchPage(new URLSearchParams(queryString), families),
  );
  const encodedView = $derived(url.searchParams.get(VIEW_PARAM));
  let reapply = $state(0);
  let drafts = $state(emptyFilters());
  let editedFields = $state<SearchFilter[]>([]);
  let moving = $state(false);
  let navigationError = $state(false);
  let gridFilterError = $state<string | null>(null);
  let refreshView = $state<{ source: string; encoded: string | null } | null>(
    null,
  );
  const gridView = $derived(
    refreshView?.source === url.href ? refreshView.encoded : encodedView,
  );
  const unapplied = $derived(
    !filtersEqual(drafts, applied.filters) ||
      editedFields.some((key) => invalidAppliedFields.includes(key)),
  );
  const hasDrafts = $derived(hasFilters(drafts));
  const invalidAppliedFields = $derived(
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
  const invalidColumnFields = $derived(invalidAppliedFields);
  const datasetKey = $derived(
    `${url.origin}${url.pathname}?${queryString}:${reapply}`,
  );
  const resultsReady = $derived(
    !moving &&
      !store.error &&
      !store.accessError &&
      store.controller !== null &&
      store.responseQuery === applied,
  );

  $effect.pre(() => {
    if (
      selectedDetails &&
      (!store.controller || selectedDetails.key !== datasetKey)
    )
      discardDetails();
  });

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
        !store.controller?.getRows().some((row) => row.id === resultId)
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
      !resultsReady ||
      !store.controller?.getRows().some((row) => row.id === resultId)
    )
      return;
    trigger.focus({ preventScroll: true });
    void loadDetails(resultId, trigger);
  }

  function retryDetails() {
    const selected = selectedDetails;
    if (selected) void loadDetails(selected.resultId, selected.trigger);
  }

  function closeDetails() {
    const previous = selectedDetails;
    discardDetails();
    if (!previous || !live || !resultsReady || previous.key !== datasetKey)
      return;
    // Native dialog restores its invoker. A locally hidden/virtualized-away
    // trigger needs a meaningful fallback, without focusing an outgoing route.
    const target =
      previous.trigger.isConnected &&
      previous.trigger.dataset.testResultId === String(previous.resultId)
        ? previous.trigger
        : pageElement.querySelector<HTMLElement>(".results-grid");
    target?.focus({ preventScroll: true });
  }

  // Synchronize before the keyed editors mount on navigation. Otherwise a new
  // editor can briefly hydrate the outgoing draft's IDs before this reset runs.
  $effect.pre(() => {
    const query = applied;
    void reapply;
    drafts = cloneFilters(query.filters);
    editedFields = [];
  });
  $effect(() => {
    const query = applied;
    void reapply;
    untrack(() => {
      void store.search(query, families, base);
    });
    return () => store.cancel();
  });

  // Older share links may carry page pagination. It is not a search condition
  // in the infinite grid: remove it with a replace-only URL update so it can
  // never be added on top of a block's own offset.
  $effect(() => {
    const current = url;
    if (
      !current.searchParams.has("limit") &&
      !current.searchParams.has("offset")
    )
      return;
    const next = new URL(current);
    next.searchParams.delete("limit");
    next.searchParams.delete("offset");
    void normalizeUrl(next, current.href).catch(() => {
      navigationError = true;
    });
  });

  async function go(params: URLSearchParams, clearView = false) {
    if (moving) return;
    moving = true;
    navigationError = false;
    // One-off navigation target, not mutable reactive component state.
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    const next = new URL(url);
    if (!clearView) {
      if (grid) {
        const view = grid.getSharedView();
        if (view !== null) params.set(VIEW_PARAM, view);
      } else {
        for (const value of url.searchParams.getAll(VIEW_PARAM))
          params.append(VIEW_PARAM, value);
      }
    }
    next.search = params.toString();
    const sameQuery = searchQueryString(next.searchParams) === queryString;
    try {
      // Explicit Search still reapplies/retries an identical query, including
      // clearing transient editors. View-only URL changes never do this.
      if (next.href === url.href) reapply++;
      else {
        await navigate(next);
        // URLSearchParams can canonicalize encoding without changing backend
        // identity (e.g. %20 to +). That explicit Search must still retry.
        if (sameQuery && url.href === next.href) reapply++;
      }
    } catch {
      navigationError = true;
    } finally {
      moving = false;
    }
  }

  function apply() {
    if (moving) return;
    void go(editedSearchParams(drafts, url.searchParams, editedFields));
  }

  async function updateView(encoded: string | null, sourceHref = url.href) {
    if (moving || sourceHref !== url.href) return;
    try {
      await replaceView(encoded, sourceHref);
    } catch {
      navigationError = true;
    }
  }

  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(url.href)}`,
  );

  function currentRowModel() {
    const model = store.rowModel;
    if (!model) throw new Error("The search row model is not ready.");
    return model;
  }
</script>

<section
  class="search-page"
  aria-labelledby="search-heading"
  bind:this={pageElement}
>
  <h1 id="search-heading">Search test results</h1>
  <p>
    Set filters from the result columns' headers, then Search. Conditions are
    exact server filters: values within a field match any; different fields must
    all match.
  </p>
  <div class="filter-bar" role="group" aria-label="Test result filters">
    <form
      class="actions"
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
          onclick={() => {
            drafts = emptyFilters();
            void go(new URLSearchParams(), true);
          }}
          disabled={moving}>Clear all</Button
        >
      {/if}
      <Button
        type="button"
        density="dense"
        disabled={moving || !encodedView}
        onclick={() => {
          refreshView = null;
          void updateView(null);
        }}>Reset table view</Button
      >
    </form>
  </div>
  {#if unapplied}
    <p class="draft-notice" role="status">
      Changes not applied. Search to update results{!hasDrafts
        ? " and clear the previous query"
        : ""}.
    </p>
  {/if}

  {#if navigationError}<p role="alert">
      Could not update the search URL. Please try again.
    </p>{/if}
  {#if gridFilterError}<p role="alert">
      {gridFilterError} Clear the unsupported grid filter and use Search to apply
      a supported exact condition.
    </p>{/if}
  <section
    class="results"
    aria-label="Search results"
    aria-busy={store.loading}
    tabindex="-1"
  >
    <div class="applied-query-actions">
      {#if applied.hasFilters && !applied.problems.length}
        <h2>
          {unapplied
            ? "Results for previous query"
            : "Results for applied query"}
        </h2>
      {/if}
    </div>
    {#if applied.problems.length}
      <div role="alert">
        <h2>Search not applied</h2>
        <ul>
          {#each applied.problems as problem (problem)}<li>{problem}</li>{/each}
        </ul>
        <p>
          No request was sent. Correct the invalid filters or URL, or clear all
          filters. Untouched invalid or unknown URL conditions are preserved
          when searching.
        </p>
      </div>
      <SearchResultsGrid
        controller={null}
        rowModel={invalidSearchRowModel}
        {base}
        encodedView={gridView}
        sourceHref={url.href}
        queryKey={datasetKey}
        disabled={moving}
        blocked
        onViewChange={updateView}
        filters={drafts}
        {families}
        onFilterEdit={(key, next) => {
          drafts = next;
          gridFilterError = null;
          if (!editedFields.includes(key))
            editedFields = [...editedFields, key];
        }}
        onFilterState={(next) => {
          drafts = next;
          gridFilterError = null;
        }}
        onFilterStateError={(message) => {
          gridFilterError = message;
        }}
        invalidFields={invalidColumnFields}
        beforeDetails={() =>
          document.dispatchEvent(new Event("search-grid-close-menus"))}
        onDetails={showDetails}
      />
    {:else if store.accessError === "requiresLogin"}
      <div role="status">
        <p>You need to be logged in to search test results.</p>
        <Link href={loginUrl}>Log in</Link>
      </div>
    {:else if store.accessError === "forbidden"}
      <div role="alert">
        <p>
          You don't have permission to view these test results. Contact an
          administrator if this is a mistake.
        </p>
        <Button onclick={() => store.retry()}>Retry</Button>
      </div>
    {:else if store.accessError === "sessionCheckFailed"}
      <div role="alert">
        <p>
          We couldn't verify your session. Check your connection and try again.
        </p>
        <Button onclick={() => store.retry()}>Retry</Button>
      </div>
    {:else if store.error}
      <div role="alert">
        <p>{store.error}</p>
        <Button onclick={() => store.retry()}>Retry</Button>
      </div>
    {:else if store.modelQuery === applied && store.controller && store.rowModel}
      {#if store.state?.rowCount !== null && store.state?.rowCount !== undefined}
        <p role="status">
          {store.state.rowCount} matching test results on the server. Scroll to load
          more; results are ordered newest first.
        </p>
      {/if}
      {#if store.loading}
        <div class="loading" role="status">
          <Spinner /> Loading test results…
        </div>
      {/if}
      {#if store.state?.rowCount === 0}
        <p>No test results match the applied conditions.</p>
      {/if}
      {#key store.controller}
        <SearchResultsGrid
          bind:this={grid}
          controller={store.controller}
          rowModel={currentRowModel()}
          {base}
          encodedView={gridView}
          sourceHref={url.href}
          queryKey={datasetKey}
          disabled={moving}
          onViewChange={updateView}
          filters={drafts}
          {families}
          onFilterEdit={(key, next) => {
            drafts = next;
            gridFilterError = null;
            if (!editedFields.includes(key))
              editedFields = [...editedFields, key];
          }}
          onFilterState={(next) => {
            drafts = next;
            gridFilterError = null;
          }}
          onFilterStateError={(message) => {
            gridFilterError = message;
          }}
          invalidFields={invalidColumnFields}
          beforeDetails={() =>
            document.dispatchEvent(new Event("search-grid-close-menus"))}
          onDetails={showDetails}
        />
      {/key}
    {:else if store.loading || store.modelQuery !== applied}
      <div class="loading" role="status"><Spinner /> Loading test results…</div>
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
  onretry={retryDetails}
/>

<style>
  .search-page {
    color: var(--lp-color-text-default);
    min-width: 0;
    height: calc(100vh - 3rem);
    display: flex;
    flex-direction: column;
  }
  .search-page > :not(.results),
  .results > :not(:global(.results-grid)) {
    flex-shrink: 0;
  }
  .results {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    min-width: 0;
  }
  h1 {
    font-size: 1.75rem;
    font-weight: 500;
  }
  .filter-bar,
  .results {
    margin-top: 1.5rem;
  }
  .filter-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.75rem;
  }
  h2 {
    font-size: 1.125rem;
    font-weight: 500;
  }
  .draft-notice {
    color: var(--lp-color-text-muted);
    margin-bottom: 0;
  }
  .actions,
  .applied-query-actions,
  .loading {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .applied-query-actions h2 {
    margin: 0;
  }
</style>
