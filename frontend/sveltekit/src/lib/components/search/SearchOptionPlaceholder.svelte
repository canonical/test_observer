<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { FetchError } from "$lib/api/client";
  import { getApiRoot } from "$lib/config";
  import { userStore } from "$lib/stores/user.svelte";
  import type { Family } from "$lib/types";
  import {
    loadSearchOptionsPage,
    parseSearchOptions,
    searchOptionsAccessErrorFor,
    searchOptionsPageParams,
    searchOptionsPageRange,
    searchOptionsPageSizeParams,
  } from "$lib/searchOptionsPagination";
  import type { SearchOptionsAccessError } from "$lib/searchOptionsPagination";
  import type { SearchTableResponse } from "$lib/testResultsSearch";

  let {
    option,
    url,
    routePath,
    families,
    navigate,
  }: {
    option: 2 | 3 | 4;
    url: URL;
    routePath: string;
    families: Family[];
    navigate: (url: string | URL) => Promise<unknown>;
  } = $props();

  const search = $derived(parseSearchOptions(url.searchParams, families));
  let selectedPageSize = $derived(search.pageSize);
  let response = $state.raw<SearchTableResponse | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let accessError = $state<SearchOptionsAccessError | null>(null);
  let retryGeneration = $state(0);
  let requestGeneration = 0;
  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(url.href)}`,
  );
  const range = $derived(response ? searchOptionsPageRange(response) : null);

  $effect(() => {
    const requestUrl = url.href;
    const query = parseSearchOptions(url.searchParams, families);
    const attempt = retryGeneration;
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

  function navigateWith(params: URLSearchParams) {
    const query = params.toString();
    return navigate(query ? `${routePath}?${query}` : routePath);
  }

  function goToPage(page: number) {
    return navigateWith(searchOptionsPageParams(url.searchParams, page));
  }

  function changePageSize(event: Event) {
    const select = event.currentTarget as HTMLSelectElement;
    const pageSize = Number(select.value);
    if (pageSize !== 25 && pageSize !== 50 && pageSize !== 100)
      return Promise.resolve();
    selectedPageSize = pageSize;
    return navigateWith(
      searchOptionsPageSizeParams(url.searchParams, pageSize),
    );
  }

  function retry() {
    error = null;
    accessError = null;
    retryGeneration += 1;
  }
</script>

<svelte:head>
  <title>Search (Option {option}) — Test Observer</title>
</svelte:head>

<section class="placeholder" aria-labelledby="search-option-title">
  <h1 id="search-option-title">Search (Option {option})</h1>
  <p>
    Search controls and result presentation are not implemented yet. This
    scaffold uses the shared server-backed pagination path.
  </p>
  {#if search.problems.length}
    <p class="message" role="alert">
      Search not applied: {search.problems.join(" ")}
    </p>
  {:else if accessError === "requiresLogin"}
    <div role="status">
      <p>You need to be logged in to search test results.</p>
      <a href={loginUrl}>Log in</a>
    </div>
  {:else if accessError === "forbidden"}
    <div class="message" role="alert">
      <p>
        You don't have permission to view these test results. Contact an
        administrator if this is a mistake.
      </p>
      <button type="button" onclick={retry}>Retry</button>
    </div>
  {:else if accessError === "sessionCheckFailed"}
    <div class="message" role="alert">
      <p>
        We couldn't verify your session. Check your connection and try again.
      </p>
      <button type="button" onclick={retry}>Retry</button>
    </div>
  {:else if error}
    <div class="message" role="alert">
      <p>{error}</p>
      <button type="button" onclick={retry}>Retry</button>
    </div>
  {:else if loading}
    <p class="count" role="status" aria-live="polite">Loading test results…</p>
  {:else if response && range}
    <p class="count" role="status" aria-live="polite">
      {#if range.start}
        Showing {range.start}–{range.end} of {range.count} results
      {:else if range.count === 0}
        No test results (0 total)
      {:else}
        No results on this page ({range.count} total)
      {/if}
    </p>
    <nav class="pager" aria-label="Test result pages">
      <button
        type="button"
        onclick={() => void goToPage(search.page - 1)}
        disabled={search.page <= 1}>Previous</button
      >
      <span>Page {search.page}</span>
      <button
        type="button"
        onclick={() => void goToPage(search.page + 1)}
        disabled={search.page * search.pageSize >= range.count}>Next</button
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

<style>
  .placeholder {
    padding: 2rem 0;
  }

  h1 {
    margin: 0 0 1rem;
    font-size: 1.75rem;
    font-weight: 500;
  }

  p {
    margin: 0;
    color: var(--lp-color-text-muted);
  }

  .count,
  .message {
    margin-top: 1.5rem;
  }

  .message {
    color: var(--lp-color-negative);
  }

  .pager {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }

  .pager button,
  .pager select {
    font: inherit;
  }

  .pager label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-left: 0.5rem;
  }
</style>
