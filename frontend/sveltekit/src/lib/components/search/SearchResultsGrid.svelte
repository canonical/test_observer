<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, onMount, untrack } from "svelte";
  import {
    SvGrid,
    renderComponent,
    ALL_FILTER_OPERATORS,
    type GridColumns,
    type SvGridApi,
  } from "@svgrid/grid";
  import type { Family } from "$lib/types";
  import { familyDisplayName } from "$lib/types";
  import { viewRunPath, type SearchResult } from "$lib/testResultsSearch";
  import ViewRunLink from "./ViewRunLink.svelte";
  import type { SearchSelectionPage } from "$lib/testResultsSelection.svelte";
  import {
    EMPTY_VIEW,
    decodeView,
    encodeView,
    type SharedGridView,
  } from "$lib/gridViewUrl";

  let {
    results,
    families,
    base,
    encodedView,
    sourceHref,
    queryKey,
    selection,
    selectedCount,
    onViewChange,
  }: {
    results: SearchResult[];
    families: Family[];
    base: string;
    encodedView: string | null;
    sourceHref: string;
    queryKey: string;
    selection: SearchSelectionPage;
    selectedCount: number;
    onViewChange: (
      encoded: string | null,
      sourceHref: string,
    ) => Promise<unknown>;
  } = $props();
  // The outgoing instance can receive new route props before its loading
  // branch unmounts. Tag it with the backend query it actually rendered, not
  // the latest href (which legitimately changes for presentation writes).
  const ownerQuery = untrack(() => queryKey);
  let live = true;
  onDestroy(() => {
    live = false;
  });
  const selectionEnabled = () =>
    live && ownerQuery === queryKey && selection.enabled();
  const rows = $derived(
    results.map((result) => {
      const family = families.find(
        (f) => f.api_name === result.artefact.family,
      );
      return {
        id: result.test_result.id,
        artefact: result.artefact.name,
        family: family ? familyDisplayName(family) : result.artefact.family,
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
      };
    }),
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

  let api = $state<SvGridApi<never, Row> | null>(null);
  // getDisplayedRows is the grid's complete post-filter/sort list, not its
  // virtual DOM window. Header intent never opts in to all server matches.
  const displayedIds = () => api?.getDisplayedRows().map((row) => row.id) ?? [];
  const rowSelectionModel = {
    isSelected: (_id: string, row: Row) =>
      selectionEnabled() && selection.isSelected(row.id),
    headerState: () =>
      selectionEnabled() ? selection.headerState(displayedIds()) : "none",
    toggle: (_id: string, row: Row, next: boolean) => {
      if (selectionEnabled()) selection.toggle([row.id], next);
    },
    toggleAll: (next: boolean) => {
      if (selectionEnabled()) selection.toggle(displayedIds(), next);
    },
    selectedCount: () => (selectionEnabled() ? selectedCount : 0),
  };
  let restored = false;
  let restoredParam: string | null = null;
  let lastSnapshot: string | null = null;

  // A dashboard's columns are not necessarily applicable to search results.
  // Ignore unknown refs and the Run link's non-sortable/non-filterable column.
  function applicableView(view: SharedGridView): SharedGridView {
    const ids = new Set(columns.map((column) => column.id));
    const sortable = new Set(
      columns.filter((c) => c.sortable !== false).map((c) => c.id),
    );
    const filterable = new Set(
      columns.filter((c) => c.filterable !== false).map((c) => c.id),
    );
    return {
      ...EMPTY_VIEW,
      ...view,
      sorting: view.sorting?.filter((sort) => sortable.has(sort.id)) ?? [],
      columnFilters: Object.fromEntries(
        Object.entries(view.columnFilters ?? {}).filter(
          ([id, filter]) =>
            filterable.has(id) &&
            ALL_FILTER_OPERATORS.includes(filter.operator),
        ),
      ),
      facetFilters: Object.fromEntries(
        Object.entries(view.facetFilters ?? {}).filter(([id]) =>
          filterable.has(id),
        ),
      ),
      hiddenColumns: view.hiddenColumns?.filter((id) => ids.has(id)) ?? [],
      // All search columns are visible by default: there are no default-hidden
      // columns to reveal. Widths, order and pinning never enter shared state.
      shownColumns: [],
    };
  }

  function sharedState(handle: SvGridApi<never, Row>): SharedGridView {
    const {
      sorting,
      globalFilter,
      columnFilters,
      facetFilters,
      hiddenColumns,
    } = handle.getState();
    return {
      sorting,
      globalFilter,
      columnFilters,
      facetFilters,
      hiddenColumns,
    };
  }

  $effect(() => {
    const handle = api;
    const param = encodedView;
    if (!handle) return;
    untrack(() => {
      const view = applicableView(decodeView(param) ?? {});
      lastSnapshot = encodeView(view);
      // Missing/invalid params restore ALL shared defaults, not just the keys
      // present in the link. Do not reset session-only widths/order/pinning.
      if (encodeView(sharedState(handle)) !== lastSnapshot)
        handle.setState(view);
      restoredParam = param;
      restored = true;
    });
  });

  function syncView() {
    // Grid callbacks run in effects. Do not subscribe those effects to our URL
    // props, and never echo restoration (including a removed/invalid view).
    untrack(() => {
      if (
        !api ||
        !restored ||
        ownerQuery !== queryKey ||
        restoredParam !== encodedView
      )
        return;
      const snapshot = encodeView(sharedState(api));
      if (snapshot === lastSnapshot) return;
      lastSnapshot = snapshot;
      void onViewChange(snapshot, sourceHref);
    });
  }

  // Search/pagination must capture even a visibility toggle made just before
  // the next polling tick, rather than copying a slightly stale URL snapshot.
  export function getSharedView(): string | null {
    return api && ownerQuery === queryKey
      ? encodeView(sharedState(api))
      : encodedView;
  }

  onMount(() => {
    // Installed SvGrid 3 has sorting/filter callbacks but no visibility-change
    // callback. Poll only the shareable snapshot, as its autosave manager does;
    // no storage or named views are enabled for search.
    const timer = setInterval(syncView, 250);
    return () => clearInterval(timer);
  });
</script>

<div class="results-grid">
  <SvGrid
    data={rows}
    {columns}
    getRowId={(row) => String(row.id)}
    containerHeight="100%"
    virtualization
    columnVirtualization={false}
    sortable
    filterable
    filterMode="menu"
    showGlobalFilter
    columnResize
    enableRowHover
    selectionMode="row"
    showRowSelection={selectionEnabled()}
    {rowSelectionModel}
    selectionBar={false}
    contextMenu={false}
    emptyMessage="No loaded results match the local grid filters."
    onApiReady={(handle) => {
      api = handle;
    }}
    onSortingChange={syncView}
    onFiltersChange={syncView}
  />
</div>

<style>
  .results-grid {
    flex: 1;
    min-height: 0;
    min-width: 0;
    width: 100%;
  }
</style>
