<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { SvGrid, renderComponent, type GridColumns } from "@svgrid/grid";
  import type { Family } from "$lib/types";
  import { viewRunPath, type SearchResult } from "$lib/testResultsSearch";
  import ViewRunLink from "./ViewRunLink.svelte";

  let {
    results,
    families,
    base,
  }: { results: SearchResult[]; families: Family[]; base: string } = $props();
  const rows = $derived(
    results.map((result) => ({
      id: result.test_result.id,
      artefact: result.artefact.name,
      family:
        families.find((f) => f.api_name === result.artefact.family)
          ?.friendly_name ?? result.artefact.family,
      testCase: result.test_result.name,
      status: result.test_result.status,
      execution: result.test_execution.id,
      executionStatus: result.test_execution.status,
      version: result.artefact.version,
      track: result.artefact.track,
      environment: result.test_execution.environment.name,
      testPlan: result.test_execution.test_plan,
      architecture: result.artefact_build.architecture,
      href: viewRunPath(result, families, base),
    })),
  );
  type Row = (typeof rows)[number];
  const columns: GridColumns<Row> = [
    {
      id: "run",
      header: "Run",
      sortable: false,
      filterable: false,
      cell: ({ row }) =>
        renderComponent(ViewRunLink, {
          href: row.original.href,
          name: row.original.testCase,
        }),
    },
    { id: "artefact", header: "Artefact", field: "artefact" },
    { id: "testCase", header: "Test case", field: "testCase" },
    { id: "status", header: "Result status", field: "status" },
    {
      id: "execution",
      header: "Execution ID",
      field: "execution",
      cellDataType: "number",
    },
    {
      id: "executionStatus",
      header: "Execution status",
      field: "executionStatus",
    },
    { id: "version", header: "Version", field: "version" },
    { id: "track", header: "Track", field: "track" },
    { id: "environment", header: "Environment", field: "environment" },
    { id: "testPlan", header: "Test plan", field: "testPlan" },
    { id: "family", header: "Family", field: "family" },
    { id: "architecture", header: "Architecture", field: "architecture" },
  ];
</script>

<div class="results-grid">
  <SvGrid
    data={rows}
    {columns}
    getRowId={(row) => String(row.id)}
    containerHeight="32rem"
    virtualization={false}
    columnVirtualization={false}
    sortable
    filterable
    filterMode="menu"
    showGlobalFilter
    columnResize
    enableRowHover
    selectionMode="none"
    emptyMessage="No loaded results match the local grid filters."
  />
</div>

<style>
  .results-grid {
    min-width: 0;
    width: 100%;
  }
</style>
