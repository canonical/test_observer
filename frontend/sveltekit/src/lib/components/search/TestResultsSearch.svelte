<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import { Button, Spinner, Link } from "@canonical/svelte-ds-app-launchpad";
  import { SearchIcon } from "@canonical/svelte-icons";
  import type { Family } from "$lib/types";
  import { getApiRoot } from "$lib/config";
  import { TestResultsSearchStore } from "$lib/stores/test-results-search.svelte";
  import {
    emptyFilters,
    parseSearch,
    searchParams,
    searchQueryString,
    SEARCH_FILTERS,
  } from "$lib/testResultsSearch";
  import SearchResultsGrid from "./SearchResultsGrid.svelte";
  import SearchConditions from "./SearchConditions.svelte";
  import { VIEW_PARAM } from "$lib/gridViewUrl";

  let {
    url,
    families,
    base,
    navigate,
    replaceView,
  }: {
    url: URL;
    families: Family[];
    base: string;
    navigate: (url: URL) => Promise<unknown>;
    replaceView: (
      encoded: string | null,
      sourceHref: string,
    ) => Promise<unknown>;
  } = $props();
  const store = new TestResultsSearchStore();
  let grid = $state<ReturnType<typeof SearchResultsGrid> | null>(null);
  const queryString = $derived(searchQueryString(url.searchParams));
  const applied = $derived(
    parseSearch(new URLSearchParams(queryString), families),
  );
  const encodedView = $derived(url.searchParams.get(VIEW_PARAM));
  let reapply = $state(0);
  let editorRevision = $state(0);
  let drafts = $state(emptyFilters());
  let moving = $state(false);
  let navigationError = $state(false);
  const unapplied = $derived(
    SEARCH_FILTERS.some(
      (key) =>
        drafts[key].length !== applied.filters[key].length ||
        drafts[key].some((value) => !applied.filters[key].includes(value)),
    ),
  );
  const hasDrafts = $derived(
    SEARCH_FILTERS.some((key) => drafts[key].length > 0),
  );

  $effect(() => {
    const query = applied;
    void reapply;
    drafts = structuredClone(query.filters);
    untrack(() => {
      void store.search(query);
    });
    return () => store.cancel();
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
    void go(hasDrafts ? searchParams(drafts) : new URLSearchParams());
  }

  async function updateView(encoded: string | null, sourceHref = url.href) {
    if (moving || sourceHref !== url.href) return;
    try {
      await replaceView(encoded, sourceHref);
    } catch {
      navigationError = true;
    }
  }

  const response = $derived(store.response);
  const hasNext = $derived(
    Boolean(
      response &&
      response.test_results.length >= applied.limit &&
      applied.offset + response.test_results.length < response.count,
    ),
  );
  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(url.href)}`,
  );
</script>

<section class="search-page" aria-labelledby="search-heading">
  <h1 id="search-heading">Search test results</h1>
  <p>
    Add exact-match conditions, then Search. Values within a filter match any;
    different filters must all match.
  </p>
  <div class="filter-bar" role="group" aria-label="Test result filters">
    {#key `${queryString}:${reapply}:${editorRevision}`}
      <SearchConditions bind:filters={drafts} {families} disabled={moving} />
    {/key}
    <form
      class="actions"
      aria-label="Apply confirmed search filters"
      onsubmit={(event) => {
        event.preventDefault();
        apply();
      }}
    >
      <Button
        type="submit"
        severity="brand"
        density="dense"
        disabled={moving}
      >
        {#snippet iconLeft()}<SearchIcon />{/snippet}
        Search
      </Button>
      {#if hasDrafts || url.search}
        <Button
          type="button"
          density="dense"
          onclick={() => {
            drafts = emptyFilters();
            editorRevision++;
            void go(new URLSearchParams(), true);
          }}
          disabled={moving}>Clear all</Button
        >
      {/if}
      <Button
        type="button"
        density="dense"
        disabled={moving || !encodedView}
        onclick={() => updateView(null)}>Reset table view</Button
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
  <section
    class="results"
    aria-label="Search results"
    aria-busy={store.loading}
  >
    {#if applied.hasFilters && !applied.problems.length}
      <h2>
        {unapplied ? "Results for previous query" : "Results for applied query"}
      </h2>
    {/if}
    {#if applied.problems.length}
      <div role="alert">
        <h2>Search not applied</h2>
        <ul>
          {#each applied.problems as problem (problem)}<li>{problem}</li>{/each}
        </ul>
        <p>
          No request was sent. Correct the URL, Search with supported filters to
          replace it, or clear all filters.
        </p>
      </div>
    {:else if !applied.hasFilters}
      <p role="status">
        Choose at least one filter and select Search to find test results.
      </p>
    {:else if store.loading}
      <div class="loading" role="status"><Spinner /> Loading test results…</div>
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
        <Button onclick={() => store.search(applied)}>Retry</Button>
      </div>
    {:else if store.accessError === "sessionCheckFailed"}
      <div role="alert">
        <p>
          We couldn't verify your session. Check your connection and try again.
        </p>
        <Button onclick={() => store.search(applied)}>Retry</Button>
      </div>
    {:else if store.error}
      <div role="alert">
        <p>{store.error}</p>
        <Button onclick={() => store.search(applied)}>Retry</Button>
      </div>
    {:else if response}
      <p role="status">
        {response.count} matching test results on the server. {response
          .test_results.length} loaded on this page (offset {applied.offset}).
      </p>
      <p class="muted">
        Grid filtering and sorting affect only this loaded page, not the server
        total or other pages. Server pages are ordered newest first.
      </p>
      {#if response.test_results.length}
        <SearchResultsGrid
          bind:this={grid}
          results={response.test_results}
          {families}
          {base}
          {encodedView}
          sourceHref={url.href}
          queryKey={`${url.origin}${url.pathname}?${queryString}`}
          onViewChange={updateView}
        />
      {:else if response.count === 0}
        <p>No test results match the applied filters.</p>
      {:else}
        <p>
          No results on this page. Go to the previous page or apply filters
          again to start from the beginning.
        </p>
      {/if}
      <nav aria-label="Search result pages" class="actions pagination">
        <Button
          disabled={moving || unapplied || applied.offset === 0}
          onclick={() =>
            go(
              searchParams(
                applied.filters,
                applied.limit,
                Math.max(0, applied.offset - applied.limit),
              ),
            )}>Previous page</Button
        >
        <Button
          disabled={moving || unapplied || !hasNext}
          onclick={() =>
            go(
              searchParams(
                applied.filters,
                applied.limit,
                applied.offset + applied.limit,
              ),
            )}>Next page</Button
        >
      </nav>
    {/if}
  </section>
</section>

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
  .loading {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .muted {
    color: var(--lp-color-text-muted);
  }
  .pagination {
    margin-top: 1rem;
  }
</style>
