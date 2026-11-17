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
  import { onMount } from "svelte";
  import { silentApi } from "$lib/api/client";
  import type {
    TestResultSearchPageResponse,
    TestResultSearchPageRow,
  } from "$lib/types/test-results-search-page";

  const FIRST_PAGE_REQUEST = "test-results/search-page?limit=50&offset=0";

  let rows = $state<TestResultSearchPageRow[]>([]);
  let loadState = $state<"loading" | "loaded" | "failed">("loading");
  let activeRequest: AbortController | undefined;
  let requestGeneration = 0;

  function loadFirstPage() {
    activeRequest?.abort();
    const controller = new AbortController();
    activeRequest = controller;
    const generation = ++requestGeneration;
    loadState = "loading";

    void silentApi<TestResultSearchPageResponse>(FIRST_PAGE_REQUEST, {
      signal: controller.signal,
    })
      .then((response) => {
        if (generation !== requestGeneration || controller.signal.aborted) return;
        if (!response) throw new Error("The search page response was empty.");
        rows = response.test_results;
        loadState = "loaded";
      })
      .catch(() => {
        if (generation !== requestGeneration || controller.signal.aborted) return;
        loadState = "failed";
      });
  }

  onMount(() => {
    loadFirstPage();
    return () => {
      requestGeneration += 1;
      activeRequest?.abort();
    };
  });
</script>

<section class="results-page" aria-labelledby="page-title" aria-busy={loadState === "loading"}>
  <h1 id="page-title" class="page-title">Search Results</h1>

  {#if loadState === "loading"}
    <p class="state-message" role="status" aria-live="polite">Loading test results…</p>
  {:else if loadState === "failed"}
    <div class="state-message error-message" role="alert">
      <p>Test results could not be loaded.</p>
      <button class="retry-button" type="button" onclick={loadFirstPage}>Retry</button>
    </div>
  {:else if rows.length === 0}
    <p class="state-message" role="status">No test results found.</p>
  {:else}
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th scope="col">Created</th>
            <th scope="col">Artefact</th>
            <th scope="col">Test Case</th>
            <th scope="col">Category</th>
            <th scope="col">Test Execution ID</th>
            <th scope="col">Status</th>
            <th scope="col">Track</th>
            <th scope="col">Version</th>
            <th scope="col">Environment / Architecture</th>
            <th scope="col">Test Plan</th>
          </tr>
        </thead>
        <tbody>
          {#each rows as row (row.test_result.id)}
            <tr>
              <td><time datetime={row.test_result.created_at}>{new Date(row.test_result.created_at).toLocaleString()}</time></td>
              <td>{row.artefact.name}</td>
              <td>{row.test_result.name}</td>
              <td>{row.test_result.category}</td>
              <td>{row.test_execution.id}</td>
              <td>{row.test_result.status}</td>
              <td>{row.artefact.track || "—"}</td>
              <td>{row.artefact.version}</td>
              <td>{row.test_execution.environment.name} / {row.artefact_build.architecture}</td>
              <td>{row.test_execution.test_plan}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>

<style>
  .results-page {
    padding: 1rem 0 2rem;
  }

  .page-title {
    font-size: 1.75rem;
    font-weight: 500;
    margin: 0 0 1.5rem;
  }

  .state-message {
    margin: 1rem 0;
    color: var(--lp-color-text-muted, #666);
  }

  .error-message {
    color: var(--lp-color-text-default, #222);
  }

  .retry-button {
    border: 1px solid currentColor;
    border-radius: 0.25rem;
    background: transparent;
    color: inherit;
    cursor: pointer;
    font: inherit;
    padding: 0.375rem 0.75rem;
  }

  .table-scroll {
    max-width: 100%;
    overflow: auto;
  }

  table {
    border-collapse: collapse;
    min-width: 70rem;
    text-align: left;
    width: 100%;
  }

  th,
  td {
    border-bottom: 1px solid var(--lp-color-border-default, #d9d9d9);
    padding: 0.75rem;
    vertical-align: top;
  }

  th {
    font-weight: 500;
  }
</style>
