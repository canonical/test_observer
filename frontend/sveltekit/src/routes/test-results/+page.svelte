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
  import { SvGrid, type GridColumns } from "@svgrid/grid";
  import { silentApi } from "$lib/api/client";
  import type {
    TestResultSearchPageResponse,
    TestResultSearchPageRow,
  } from "$lib/types/test-results-search-page";

  const FIRST_PAGE_REQUEST = "test-results/search-page?limit=50&offset=0";

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

  let rows = $state<TestResultGridRow[]>([]);
  let loadState = $state<"loading" | "loaded" | "failed">("loading");
  let activeRequest: AbortController | undefined;
  let requestGeneration = 0;

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
        if (generation !== requestGeneration || controller.signal.aborted)
          return;
        if (!response) throw new Error("The search page response was empty.");
        rows = toGridRows(response.test_results);
        loadState = "loaded";
      })
      .catch(() => {
        if (generation !== requestGeneration || controller.signal.aborted)
          return;
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

<section
  class="results-page"
  aria-labelledby="page-title"
  aria-busy={loadState === "loading"}
>
  <h1 id="page-title" class="page-title">Search Results (WIP)</h1>

  {#if loadState === "loading"}
    <p class="state-message" role="status" aria-live="polite">
      Loading test results…
    </p>
  {:else if loadState === "failed"}
    <div class="state-message error-message" role="alert">
      <p>Test results could not be loaded.</p>
      <button class="retry-button" type="button" onclick={loadFirstPage}
        >Retry</button
      >
    </div>
  {:else if rows.length === 0}
    <p class="state-message" role="status">No test results found.</p>
  {:else}
    <div class="grid-wrapper">
      <SvGrid
        data={rows}
        {columns}
        containerHeight="auto"
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
        virtualization={false}
        columnVirtualization={false}
        columnResize={false}
        rowResize={false}
      />
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

  .grid-wrapper {
    max-width: 100%;
    overflow: auto;
    width: 100%;
  }

  /* Let vertical wheel scrolling chain to the containing pane. This unpaginated
     grid grows to its content, so it should not trap scroll at its own edge. */
  .grid-wrapper :global(.sv-grid-container) {
    overscroll-behavior-y: auto;
  }
</style>
