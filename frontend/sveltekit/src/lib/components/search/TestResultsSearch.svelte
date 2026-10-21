<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, tick, untrack } from "svelte";
  import { Button, Spinner, Link } from "@canonical/svelte-ds-app-launchpad";
  import { SearchIcon } from "@canonical/svelte-icons";
  import type { Family } from "$lib/types";
  import { getApiRoot } from "$lib/config";
  import { TestResultsSearchStore } from "$lib/stores/test-results-search.svelte";
  import {
    emptyFilters,
    cloneFilters,
    filtersEqual,
    hasFilters,
    editedSearchParams,
    parseSearch,
    searchParams,
    searchQueryString,
    SEARCH_FILTERS,
    type SearchFilter,
    type SearchResult,
  } from "$lib/testResultsSearch";
  import SearchResultsGrid from "./SearchResultsGrid.svelte";
  import SearchConditions from "./SearchConditions.svelte";
  import SearchResultDetails from "./SearchResultDetails.svelte";
  import BulkIssueActions from "./BulkIssueActions.svelte";
  import CreateAttachmentRule from "./CreateAttachmentRule.svelte";
  import {
    attachmentRuleFilters,
    freezeBulkTarget,
  } from "$lib/testResultsBulk";
  import { VIEW_PARAM } from "$lib/gridViewUrl";
  import {
    selectionQuery,
    TestResultsSelection,
  } from "$lib/testResultsSelection.svelte";

  let {
    url,
    families,
    base,
    navigate,
    replaceView,
    onBusyChange,
  }: {
    url: URL;
    families: Family[];
    base: string;
    navigate: (url: URL) => Promise<unknown>;
    replaceView: (
      encoded: string | null,
      sourceHref: string,
    ) => Promise<unknown>;
    onBusyChange?: (busy: boolean) => void;
  } = $props();
  const store = new TestResultsSearchStore();
  const selection = new TestResultsSelection();
  let live = true;
  onDestroy(() => {
    live = false;
    selection.clear();
  });
  let grid = $state<ReturnType<typeof SearchResultsGrid> | null>(null);
  let conditions = $state<ReturnType<typeof SearchConditions> | null>(null);
  let selectedDetails = $state<{
    result: SearchResult;
    key: string;
    trigger: HTMLButtonElement;
  } | null>(null);
  let pageElement: HTMLElement;
  const queryString = $derived(searchQueryString(url.searchParams));
  const routeKey = $derived(`${url.origin}${url.pathname}`);
  const applied = $derived(
    parseSearch(new URLSearchParams(queryString), families),
  );
  const encodedView = $derived(url.searchParams.get(VIEW_PARAM));
  let reapply = $state(0);
  let editorRevision = $state(0);
  let drafts = $state(emptyFilters());
  let editedFields = $state<SearchFilter[]>([]);
  let moving = $state(false);
  let navigationError = $state(false);
  let selectedBusy = $state(false);
  let selectedReviewOpen = $state(false);
  let ruleBusy = $state(false);
  let ruleReviewOpen = $state(false);
  // Imperative callbacks also run during child teardown. Svelte teardown reads
  // reactive values from the outgoing snapshot, even after a no-op false write.
  // Keep the latest callback values outside that snapshot so route guards agree
  // with the rendered state, without letting one child clear another action.
  const actionBusy = { selection: false, rule: false };
  const bulkBusy = $derived(selectedBusy || ruleBusy);
  const bulkReviewOpen = $derived(selectedReviewOpen || ruleReviewOpen);
  let bulkMessage = $state("");
  let refreshView = $state<{ source: string; encoded: string | null } | null>(
    null,
  );
  const gridView = $derived(
    refreshView?.source === url.href ? refreshView.encoded : encodedView,
  );
  function actionReadiness(mutating: boolean) {
    return {
      available:
        store.response !== null &&
        store.responseQuery === applied &&
        !store.error,
      loading: store.loading,
      moving,
      accessError: store.accessError !== null,
      unapplied,
      // This dialog owns the in-flight operation; its pre-POST recheck must
      // exclude only itself, never another operation or loading/access guard.
      mutating,
    };
  }
  function bulkScope(ownSubmission = false) {
    return freezeBulkTarget(
      selection.snapshot(),
      applied,
      actionReadiness(ruleBusy || (selectedBusy && !ownSubmission)),
    );
  }
  function ruleScope(ownSubmission = false) {
    return attachmentRuleFilters(
      applied,
      actionReadiness(selectedBusy || (ruleBusy && !ownSubmission)),
    );
  }
  function prepareBulk() {
    conditions?.preserveEditor();
    selectedDetails = null;
  }
  function setActionBusy(action: "selection" | "rule", value: boolean) {
    actionBusy[action] = value;
    if (action === "selection") selectedBusy = value;
    else ruleBusy = value;
    onBusyChange?.(actionBusy.selection || actionBusy.rule);
  }
  async function refreshResults() {
    const view = grid?.getSharedView();
    if (view !== undefined) {
      refreshView = { source: url.href, encoded: view };
      await updateView(view);
      if (!live) return;
    }
    if (!live) return;
    // Read CURRENT applied state after any view write; the store's generation
    // guard rejects this response if a newer query subsequently starts.
    await store.search(applied);
  }
  async function bulkComplete(key: string, message: string) {
    if (!live) return;
    if (key === bulkReviewKey) selection.clear();
    bulkMessage = message;
    await refreshResults();
    await tick();
    if (live)
      (
        pageElement.querySelector<HTMLElement>(".results-grid") ??
        pageElement.querySelector<HTMLElement>(".results")
      )?.focus({ preventScroll: true });
  }
  const unapplied = $derived(
    !filtersEqual(drafts, applied.filters) ||
      editedFields.some((key) => invalidAppliedFields.includes(key)),
  );
  const hasDrafts = $derived(hasFilters(drafts));
  const invalidAppliedFields = $derived(
    SEARCH_FILTERS.filter((key) =>
      applied.problems.some((problem) => problem.startsWith(`Invalid ${key}:`)),
    ),
  );
  const invalidFields = $derived(
    invalidAppliedFields.filter((key) => !editedFields.includes(key)),
  );
  const selectionSnapshot = $derived(selectionQuery(applied));
  const datasetKey = $derived(
    `${url.origin}${url.pathname}?${queryString}:${reapply}`,
  );
  const bulkReviewKey = $derived(
    `${datasetKey}:${JSON.stringify(selection.snapshot())}`,
  );
  const selectionReady = $derived(
    !moving &&
      !store.loading &&
      !store.error &&
      !store.accessError &&
      store.responseQuery === applied &&
      selectionSnapshot !== null,
  );
  const selectionPage = $derived.by(() => {
    const owner = store.response;
    const key = datasetKey;
    if (!owner || !selectionReady) return null;
    return selection.page(
      owner.test_results.map((result) => result.test_result.id),
      () =>
        live &&
        selectionReady &&
        store.response === owner &&
        datasetKey === key,
      owner.test_results.map((result) => ({
        resultId: result.test_result.id,
        executionId: result.test_execution.id,
      })),
    );
  });

  // Presentation-only history never changes datasetKey/selectionReady. Query,
  // reapply, pagination, session/loading and route invalidation do.
  $effect.pre(() => {
    if (
      selectedDetails &&
      (!selectionReady || selectedDetails.key !== datasetKey)
    )
      selectedDetails = null;
  });

  function showDetails(result: SearchResult, trigger: HTMLButtonElement) {
    if (
      !live ||
      bulkReviewOpen ||
      !selectionReady ||
      !store.response?.test_results.includes(result)
    )
      return;
    trigger.focus({ preventScroll: true });
    selectedDetails = { result, key: datasetKey, trigger };
  }

  function closeDetails() {
    const previous = selectedDetails;
    selectedDetails = null;
    if (!previous || !live || !selectionReady || previous.key !== datasetKey)
      return;
    // Native dialog restores its invoker. A locally hidden/virtualized-away
    // trigger needs a meaningful fallback, without focusing an outgoing route.
    const target =
      previous.trigger.isConnected &&
      previous.trigger.dataset.testResultId ===
        String(previous.result.test_result.id)
        ? previous.trigger
        : pageElement.querySelector<HTMLElement>(".results-grid");
    target?.focus({ preventScroll: true });
  }

  $effect.pre(() => {
    const snapshot = selectionSnapshot;
    const count = selectionReady ? store.response?.count : undefined;
    untrack(() => {
      selection.setQuery(snapshot);
      if (count !== undefined) selection.updateCount(count);
    });
  });

  // Pages retain selected execution IDs; route changes and explicit reapply do
  // not. View-only history neither clears context nor causes an API request.
  $effect.pre(() => {
    void routeKey;
    void reapply;
    untrack(() => selection.clear());
  });

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
      void store.search(query);
    });
    return () => store.cancel();
  });

  async function go(params: URLSearchParams, clearView = false) {
    if (moving || bulkBusy) return;
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
    if (moving || bulkBusy) return;
    selection.clear();
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

<svelte:window
  onbeforeunload={(event) => {
    if (bulkBusy) {
      event.preventDefault();
      event.returnValue = "";
    }
  }}
/>

<section
  class="search-page"
  aria-labelledby="search-heading"
  bind:this={pageElement}
>
  <h1 id="search-heading">Search test results</h1>
  <p>
    Add exact-match conditions, then Search. Values within a filter match any;
    different filters must all match.
  </p>
  <div class="filter-bar" role="group" aria-label="Test result filters">
    {#key `${queryString}:${reapply}:${editorRevision}`}
      <SearchConditions
        bind:this={conditions}
        bind:filters={drafts}
        {families}
        {invalidFields}
        onedit={(key) => {
          if (!editedFields.includes(key))
            editedFields = [...editedFields, key];
        }}
        disabled={moving || bulkBusy}
      />
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
        disabled={moving || bulkBusy}
      >
        {#snippet iconLeft()}<SearchIcon />{/snippet}
        Search
      </Button>
      {#if hasDrafts || url.search}
        <Button
          type="button"
          density="dense"
          onclick={() => {
            selection.clear();
            drafts = emptyFilters();
            editorRevision++;
            void go(new URLSearchParams(), true);
          }}
          disabled={moving || bulkBusy}>Clear all</Button
        >
      {/if}
      <Button
        type="button"
        density="dense"
        disabled={moving || bulkBusy || !encodedView}
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
  {#if bulkMessage}<p role="status">{bulkMessage}</p>{/if}
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
      <CreateAttachmentRule
        scope={ruleScope}
        reviewKey={`${datasetKey}:${getApiRoot()}`}
        origin={url.origin}
        {base}
        {loginUrl}
        blocked={selectedReviewOpen || selectedBusy}
        beforeOpen={prepareBulk}
        onbusy={(value) => setActionBusy("rule", value)}
        onreview={(value) => (ruleReviewOpen = value)}
        oncomplete={(message) => (bulkMessage = message)}
      />
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
      {#if selectionPage && (selection.selectedCount > 0 || selection.allMatches)}
        <div
          class="selection-summary"
          role="group"
          aria-label="Result selection"
        >
          <p role="status">
            {selection.selectedCount} selected{selection.allMatches
              ? ` across the applied query (${selection.exclusions.size} excluded)`
              : " by result ID"}.
          </p>
          {#if selection.allMatches || (selection.matchCount > 0 && selectionPage.allLoadedSelected())}
            <label class="all-matches">
              <input
                type="checkbox"
                checked={selection.allMatches}
                disabled={!selectionPage.enabled()}
                onchange={selectionPage.toggleAllMatches}
                aria-describedby="selection-scope"
              />
              Apply bulk options to all {selection.matchCount} matches
            </label>
          {/if}
          <Button
            type="button"
            density="dense"
            disabled={!selectionPage.enabled()}
            onclick={selectionPage.clear}>Clear selection</Button
          >
          <BulkIssueActions
            scope={bulkScope}
            reviewKey={bulkReviewKey}
            origin={url.origin}
            {base}
            {loginUrl}
            blocked={ruleReviewOpen || ruleBusy}
            beforeOpen={prepareBulk}
            onbusy={(value) => setActionBusy("selection", value)}
            onreview={(open) => (selectedReviewOpen = open)}
            oncomplete={bulkComplete}
            onrefresh={refreshResults}
          />
          <p id="selection-scope" class="muted">
            Selection uses the applied backend query, not local grid filters or
            unapplied drafts. All-matches counts use the last server total, not
            a frozen snapshot; results may change. Turning all matches off keeps
            selected rows on this loaded backend page only. The header changes
            only displayed rows; Clear selection clears every page.
          </p>
        </div>
      {/if}
      {#if response.test_results.length && selectionPage}
        <SearchResultsGrid
          bind:this={grid}
          results={response.test_results}
          {families}
          {base}
          encodedView={gridView}
          sourceHref={url.href}
          queryKey={datasetKey}
          selection={selectionPage}
          selectedCount={selection.selectedCount}
          onViewChange={updateView}
          beforeDetails={() => conditions?.preserveEditor()}
          onDetails={showDetails}
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
          disabled={moving || bulkBusy || unapplied || applied.offset === 0}
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
          disabled={moving || bulkBusy || unapplied || !hasNext}
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

<SearchResultDetails
  result={selectedDetails?.result ?? null}
  {families}
  {base}
  onclose={closeDetails}
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
  .muted {
    color: var(--lp-color-text-muted);
  }
  .selection-summary {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    margin-bottom: 0.75rem;
  }
  .selection-summary p {
    margin: 0;
  }
  .selection-summary .muted {
    flex-basis: 100%;
    font-size: 0.875rem;
  }
  .all-matches {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .pagination {
    margin-top: 1rem;
  }
</style>
