<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import {
    Button,
    Checkbox,
    TextInput,
    Spinner,
    Link,
  } from "@canonical/svelte-ds-app-launchpad";
  import { SearchIcon } from "@canonical/svelte-icons";
  import type { Family } from "$lib/types";
  import { getApiRoot } from "$lib/config";
  import { TestResultsSearchStore } from "$lib/stores/test-results-search.svelte";
  import {
    emptyFilters,
    listValues,
    parseSearch,
    searchParams,
    RESULT_STATUSES,
    type SearchFilters,
    type SearchFilter,
  } from "$lib/testResultsSearch";
  import SearchResultsGrid from "./SearchResultsGrid.svelte";

  let {
    url,
    families,
    base,
    navigate,
  }: {
    url: URL;
    families: Family[];
    base: string;
    navigate: (url: URL) => Promise<unknown>;
  } = $props();
  const store = new TestResultsSearchStore();
  const applied = $derived(parseSearch(url.searchParams, families));
  let drafts = $state(emptyFilters());
  let textDrafts = $state<Record<string, string>>({});
  let moving = $state(false);
  let navigationError = $state(false);
  const textFilters: { key: SearchFilter; label: string }[] = [
    { key: "artefacts", label: "Artefact names" },
    { key: "artefact_versions", label: "Versions" },
    { key: "artefact_tracks", label: "Tracks" },
    { key: "environments", label: "Environments" },
    { key: "test_plans", label: "Test plans" },
    { key: "test_cases", label: "Test cases" },
  ];

  $effect(() => {
    const query = applied;
    drafts = structuredClone(query.filters);
    textDrafts = Object.fromEntries(
      textFilters.map(({ key }) => [key, query.filters[key].join(", ")]),
    );
    untrack(() => {
      void store.search(query);
    });
    return () => store.cancel();
  });

  async function go(params: URLSearchParams) {
    if (moving) return;
    moving = true;
    navigationError = false;
    // One-off navigation target, not mutable reactive component state.
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    const next = new URL(url);
    next.search = params.toString();
    try {
      if (next.href === url.href) await store.search(applied);
      else await navigate(next);
    } catch {
      navigationError = true;
    } finally {
      moving = false;
    }
  }

  function apply(event: SubmitEvent) {
    event.preventDefault();
    const filters: SearchFilters = { ...drafts };
    for (const { key } of textFilters)
      filters[key] = listValues([textDrafts[key] ?? ""]);
    void go(searchParams(filters));
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
    Search exact names, not partial text. Comma-separated values match any value
    within a filter; different filters must all match.
  </p>
  <form onsubmit={apply} aria-label="Test result filters">
    <div class="choices">
      <fieldset>
        <legend>Families</legend>
        {#each families as family (family.api_name)}
          <label
            ><Checkbox bind:group={drafts.families} value={family.api_name} />
            {family.friendly_name}</label
          >
        {/each}
        {#if families.length === 0}<p>
            Family configuration unavailable. Other filters can still be used.
          </p>{/if}
      </fieldset>
      <fieldset>
        <legend>Test result statuses</legend>
        {#each RESULT_STATUSES as status (status)}
          <label
            ><Checkbox
              bind:group={drafts.test_result_statuses}
              value={status}
            />
            {status}</label
          >
        {/each}
      </fieldset>
    </div>
    <div class="text-filters">
      {#each textFilters as filter (filter.key)}
        <div class="text-filter">
          <label for={`search-${filter.key}`}>{filter.label}</label>
          <TextInput
            id={`search-${filter.key}`}
            name={filter.key}
            bind:value={textDrafts[filter.key]}
            aria-describedby="search-hint"
          />
        </div>
      {/each}
    </div>
    <p id="search-hint" class="muted">
      Enter one or more exact values, separated by commas. Apply to update the
      URL and start a new search.
    </p>
    <div class="actions">
      <Button type="submit" severity="brand" disabled={moving}
        ><SearchIcon /> Apply filters</Button
      >
      <Button
        type="button"
        onclick={() => go(new URLSearchParams())}
        disabled={moving}>Clear all</Button
      >
    </div>
  </form>
  <details>
    <summary>About this basic search</summary>
    <p>
      Only the eight filters above are supported. Archived/latest/rerun
      selectors, dates, stages, templates, execution statuses/metadata, issues
      and reviewers are deferred. No details modal, saved views, export, bulk
      actions or mutations.
    </p>
  </details>

  {#if navigationError}<p role="alert">
      Could not update the search URL. Please try again.
    </p>{/if}
  <section
    class="results"
    aria-label="Search results"
    aria-busy={store.loading}
  >
    {#if applied.problems.length}
      <div role="alert">
        <h2>Search not applied</h2>
        <ul>
          {#each applied.problems as problem (problem)}<li>{problem}</li>{/each}
        </ul>
        <p>
          No request was sent. Correct the URL, apply the supported controls to
          replace it, or clear all filters.
        </p>
      </div>
    {:else if !applied.hasFilters}
      <p role="status">
        Choose at least one filter and apply it to search test results.
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
        {#key url.search}
          <SearchResultsGrid
            results={response.test_results}
            {families}
            {base}
          />
        {/key}
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
          disabled={moving || applied.offset === 0}
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
          disabled={moving || !hasNext}
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
    padding-bottom: 2rem;
  }
  h1 {
    font-size: 1.75rem;
    font-weight: 500;
  }
  form,
  details,
  .results {
    margin-top: 1.5rem;
  }
  fieldset {
    border: 1px solid var(--lp-color-border-default);
    padding: 1rem;
    min-width: 0;
  }
  legend {
    font-weight: 500;
  }
  fieldset label {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin: 0.25rem 1rem 0.25rem 0;
  }
  .choices,
  .text-filters {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }
  .text-filter {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
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
  summary {
    cursor: pointer;
  }
</style>
