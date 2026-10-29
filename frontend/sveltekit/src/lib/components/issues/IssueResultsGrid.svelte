<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import {
    SvGrid,
    renderComponent,
    type GridColumns,
    type GridRowModel,
    type RowData,
  } from "@svgrid/grid";
  import type { SearchGridRow } from "$lib/testResultsSearch";
  import DetailsButton from "$lib/components/search/DetailsButton.svelte";
  import ViewRunLink from "$lib/components/search/ViewRunLink.svelte";

  let {
    rowModel,
    onDetails,
  }: {
    rowModel: GridRowModel<SearchGridRow>;
    onDetails: (id: number, trigger: HTMLButtonElement) => void;
  } = $props();
  const ownerModel = untrack(() => rowModel);
  let live = true;
  onDestroy(() => (live = false));
  const columns: GridColumns<SearchGridRow> = [
    {
      id: "run",
      header: "Run",
      cell: ({ row }) =>
        renderComponent(ViewRunLink, {
          href: row.original.href,
          name: row.original.testCase,
        }),
    },
    {
      id: "details",
      header: "Details",
      width: 100,
      cell: ({ row }) =>
        renderComponent(DetailsButton, {
          name: row.original.testCase,
          resultId: row.original.id,
          prepare: () => undefined,
          show: (trigger: HTMLButtonElement) => {
            if (live && ownerModel === rowModel)
              onDetails(row.original.id, trigger);
          },
        }),
    },
    { id: "artefact", header: "Artefact", field: "artefact" },
    { id: "testCase", header: "Test case", field: "testCase" },
    { id: "category", header: "Category", field: "category" },
    { id: "execution", header: "Execution ID", field: "execution" },
    {
      id: "executionStatus",
      header: "Execution status",
      field: "executionStatus",
    },
    { id: "status", header: "Result status", field: "status" },
    { id: "track", header: "Track", field: "track" },
    { id: "version", header: "Version", field: "version" },
    { id: "architecture", header: "Architecture", field: "architecture" },
    { id: "environment", header: "Environment", field: "environment" },
    { id: "testPlan", header: "Test plan", field: "testPlan" },
  ];
</script>

<div
  class="issue-results-grid"
  role="region"
  aria-label="Issue test results grid"
  tabindex="-1"
>
  <SvGrid
    rowModel={rowModel as unknown as GridRowModel<RowData>}
    columns={columns as unknown as GridColumns}
    containerHeight="100%"
    virtualization
    columnVirtualization={false}
    sortable={false}
    filterable={false}
    showGlobalFilter={false}
    columnResize
    enableRowHover
    selectionMode="none"
    showRowSelection={false}
    contextMenu={false}
    emptyMessage="No test results are attached to this issue."
  />
</div>

<style>
  .issue-results-grid {
    height: clamp(20rem, 65vh, 48rem);
    min-width: 0;
    width: 100%;
  }
</style>
