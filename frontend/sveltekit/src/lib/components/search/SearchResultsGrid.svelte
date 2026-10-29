<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, onMount, untrack } from "svelte";
  import {
    SvGrid,
    renderComponent,
    type GridColumns,
    type GridRowModel,
    type GridFilterState,
    type RowData,
    type SvGridApi,
  } from "@svgrid/grid";
  import type { ServerController } from "@svgrid/grid";
  import type { SearchGridRow } from "$lib/testResultsSearch";
  import { filterValues, type SearchFilter } from "$lib/testResultsFilters";
  import {
    searchFiltersFromGridState,
    type SearchFilters,
  } from "$lib/testResultsSearch";
  import type { Family } from "$lib/types";
  import { familyDisplayName } from "$lib/types";
  import { formatUtcDateTime } from "$lib/formatUtcDateTime.js";
  import ViewRunLink from "./ViewRunLink.svelte";
  import DetailsButton from "./DetailsButton.svelte";
  import SearchGridValueCell from "./SearchGridValueCell.svelte";
  import SearchGridValueDialog from "./SearchGridValueDialog.svelte";
  import SearchGridFilterHeader from "./SearchGridFilterHeader.svelte";
  import {
    EMPTY_VIEW,
    decodeView,
    encodeView,
    type SharedGridView,
  } from "$lib/gridViewUrl";

  let {
    controller,
    rowModel,
    base,
    encodedView,
    sourceHref,
    queryKey,
    disabled = false,
    blocked = false,
    onViewChange,
    beforeDetails,
    onDetails,
    filters,
    families,
    onFilterEdit,
    onFilterState,
    onFilterStateError,
    invalidFields = [],
  }: {
    controller: ServerController<SearchGridRow> | null;
    rowModel: GridRowModel<SearchGridRow>;
    base: string;
    encodedView: string | null;
    sourceHref: string;
    queryKey: string;
    disabled?: boolean;
    blocked?: boolean;
    beforeDetails: () => void;
    onDetails: (resultId: number, trigger: HTMLButtonElement) => void;
    filters: SearchFilters;
    families: Family[];
    onFilterEdit: (key: SearchFilter, next: SearchFilters) => void;
    onFilterState: (next: SearchFilters) => void;
    onFilterStateError: (message: string) => void;
    invalidFields?: SearchFilter[];
    onViewChange: (
      encoded: string | null,
      sourceHref: string,
    ) => Promise<unknown>;
  } = $props();
  // The outgoing instance can receive new route props before it unmounts.
  // Tag callbacks with the query and model it actually rendered, not the latest
  // URL (which legitimately changes for column-visibility writes).
  const ownerQuery = untrack(() => queryKey);
  const ownerController = untrack(() => controller);
  const ownerRowModel = untrack(() => rowModel);
  let live = true;
  let gridRegion: HTMLDivElement | undefined = $state();
  let activeValueDialog = $state<{
    heading: string;
    itemLabel: string;
    items: SearchGridValueItem[];
    itemLayout?: "metadata-table";
    ownerKey: string;
    trigger: HTMLButtonElement;
  } | null>(null);
  onDestroy(() => {
    live = false;
  });
  const isCurrent = () =>
    live &&
    ownerQuery === queryKey &&
    controller === ownerController &&
    rowModel === ownerRowModel;
  function showValueDialog(
    heading: string,
    itemLabel: string,
    items: SearchGridValueItem[],
    ownerKey: string,
    trigger: HTMLButtonElement,
    itemLayout?: "metadata-table",
  ) {
    if (!isCurrent()) return;
    // Keep a complete snapshot in the shared dialog so a virtualized/recycled
    // row cannot change the values while the modal is open.
    trigger.focus({ preventScroll: true });
    activeValueDialog = {
      heading,
      itemLabel,
      items: items.map((item) => ({ ...item })),
      itemLayout,
      ownerKey,
      trigger,
    };
  }

  function closeValueDialog() {
    const previous = activeValueDialog;
    if (!previous) return;
    activeValueDialog = null;
    // Don't return focus to an outgoing grid after a query replacement. The
    // trigger can remain connected but be recycled for a different row.
    if (!isCurrent()) return;
    const target =
      previous.trigger.isConnected &&
      previous.trigger.dataset.searchGridValueOwner === previous.ownerKey
        ? previous.trigger
        : gridRegion;
    target?.focus({ preventScroll: true });
  }

  type Row = SearchGridRow;
  type MenuFilter = SearchFilter;
  interface SearchGridValueItem {
    key: string;
    label: string;
    detail?: string;
    href?: string;
    ariaLabel?: string;
  }
  const filterHeader = (label: string, filterKey: MenuFilter) => () =>
    renderComponent(SearchGridFilterHeader, {
      label,
      filterKey,
      filters,
      families,
      disabled,
      invalidFields,
      onedit: onFilterEdit,
    });
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
    {
      id: "details",
      header: "Details",
      sortable: false,
      filterable: false,
      width: 100,
      cell: ({ row }) =>
        renderComponent(DetailsButton, {
          name: row.original.testCase,
          resultId: row.original.id,
          prepare: () => {
            if (isCurrent()) beforeDetails();
          },
          show: (trigger: HTMLButtonElement) => {
            if (!isCurrent()) return;
            onDetails(row.original.id, trigger);
          },
        }),
    },
    {
      id: "createdAt",
      header: filterHeader("Created", "from_date"),
      field: "createdAt",
      cell: ({ row }) => formatUtcDateTime(row.original.createdAt),
    },
    {
      id: "family",
      header: filterHeader("Family", "families"),
      field: "family",
      cell: ({ row }) => {
        const configured = families.find(
          (family) => family.api_name === row.original.family,
        );
        return configured ? familyDisplayName(configured) : row.original.family;
      },
    },
    {
      id: "artefact",
      header: filterHeader("Artefact", "artefacts"),
      field: "artefact",
    },
    {
      id: "stage",
      header: filterHeader("Stage", "artefact_stages"),
      field: "stage",
      cell: ({ row }) =>
        row.original.stage === "" ? "(none)" : (row.original.stage ?? "—"),
    },
    {
      id: "archived",
      header: filterHeader("Archived", "artefact_is_archived"),
      field: "archived",
      cell: ({ row }) => (row.original.archived ? "Yes" : "No"),
    },
    {
      id: "testCase",
      header: filterHeader("Test case", "test_cases"),
      field: "testCase",
    },
    {
      id: "category",
      header: "Category",
      field: "category",
      filterable: false,
    },
    {
      id: "execution",
      header: "Execution ID",
      field: "execution",
      cellDataType: "number",
      filterable: false,
    },
    {
      id: "executionStatus",
      header: filterHeader("Execution Status", "test_execution_statuses"),
      field: "executionStatus",
    },
    {
      id: "rerunRequested",
      header: filterHeader("Rerun Requested", "rerun_is_requested"),
      field: "rerunRequested",
      cell: ({ row }) => (row.original.rerunRequested ? "Yes" : "No"),
    },
    {
      id: "latestExecution",
      header: filterHeader("Latest Execution", "execution_is_latest"),
      field: "latestExecution",
      cell: ({ row }) => (row.original.latestExecution ? "Yes" : "No"),
    },
    {
      id: "status",
      header: filterHeader("Result status", "test_result_statuses"),
      field: "status",
    },
    {
      id: "track",
      header: filterHeader("Track", "artefact_tracks"),
      field: "track",
    },
    {
      id: "version",
      header: filterHeader("Version", "artefact_versions"),
      field: "version",
    },
    {
      id: "architecture",
      header: "Architecture",
      field: "architecture",
      filterable: false,
    },
    {
      id: "environment",
      header: filterHeader("Environment", "environments"),
      field: "environment",
    },
    {
      id: "testPlan",
      header: filterHeader("Test plan", "test_plans"),
      field: "testPlan",
    },
    {
      id: "templateId",
      header: filterHeader("Template ID", "template_ids"),
      field: "templateId",
    },
    {
      id: "issues",
      header: filterHeader("Issues", "issues"),
      field: "issues",
      width: 210,
      cell: ({ row }) =>
        renderComponent(SearchGridValueCell, {
          heading: "Issues",
          itemLabel: "issue",
          ownerKey: `${row.original.id}:issues`,
          onshow: showValueDialog,
          items: row.original.issues.map((issue) => ({
            key: String(issue.id),
            label: `#${issue.id}${issue.key ? ` · ${issue.key}` : ""}`,
            detail: issue.title,
            href: `${base}/issues/${issue.id}`,
            ariaLabel: `View issue ${issue.key || issue.id}`,
          })),
        }),
    },
    {
      id: "reviewers",
      header: filterHeader("Reviewers", "reviewer_ids"),
      field: "reviewers",
      width: 180,
      cell: ({ row }) =>
        renderComponent(SearchGridValueCell, {
          heading: "Reviewers",
          itemLabel: "reviewer",
          ownerKey: `${row.original.id}:reviewers`,
          onshow: showValueDialog,
          items: row.original.reviewers.map((reviewer) => ({
            key: String(reviewer.id),
            label: reviewer.name || `#${reviewer.id}`,
            detail: reviewer.launchpad_handle
              ? `@${reviewer.launchpad_handle}`
              : undefined,
          })),
        }),
    },
    {
      id: "executionMetadata",
      header: filterHeader("Execution Metadata", "execution_metadata"),
      field: "executionMetadata",
      width: 220,
      cell: ({ row }) =>
        renderComponent(SearchGridValueCell, {
          heading: "Execution Metadata",
          itemLabel: "metadata pair",
          ownerKey: `${row.original.id}:executionMetadata`,
          onshow: showValueDialog,
          itemLayout: "metadata-table",
          items: row.original.executionMetadata.map((pair, index) => ({
            key: `${index}:${pair.category}`,
            label: pair.category,
            detail: pair.value,
          })),
        }),
    },
  ];

  let api = $state<SvGridApi<never, Row> | null>(null);
  let restored = false;
  let restoredParam: string | null = null;
  let lastSnapshot: string | null = null;
  let filterStateHydrated = false;
  let lastFilterSnapshot = "";

  function gridFilterSnapshot(searchFilters: SearchFilters): string {
    return JSON.stringify([
      searchFilters.test_result_statuses,
      searchFilters.artefacts,
      searchFilters.artefact_versions,
      searchFilters.artefact_tracks,
      searchFilters.environments,
      searchFilters.test_cases,
      searchFilters.test_plans,
      searchFilters.families,
      searchFilters.artefact_stages,
      searchFilters.artefact_is_archived,
      searchFilters.test_execution_statuses,
      searchFilters.rerun_is_requested,
      searchFilters.execution_is_latest,
      searchFilters.template_ids,
      searchFilters.from_date,
      searchFilters.until_date,
      searchFilters.issues,
      searchFilters.reviewer_ids,
      searchFilters.execution_metadata,
    ]);
  }

  function syncGridFilters(
    handle: SvGridApi<never, Row>,
    searchFilters: SearchFilters,
  ) {
    const snapshot = gridFilterSnapshot(searchFilters);
    if (snapshot === lastFilterSnapshot) return;
    lastFilterSnapshot = snapshot;

    const sets = [
      ["status", searchFilters.test_result_statuses],
      ["artefact", searchFilters.artefacts],
      ["version", searchFilters.artefact_versions],
      ["track", searchFilters.artefact_tracks],
      ["environment", searchFilters.environments],
      ["testCase", searchFilters.test_cases],
      ["testPlan", searchFilters.test_plans],
      ["family", searchFilters.families],
      ["stage", searchFilters.artefact_stages],
      ["executionStatus", searchFilters.test_execution_statuses],
      ["templateId", searchFilters.template_ids],
      [
        "issues",
        Array.isArray(searchFilters.issues)
          ? searchFilters.issues.map(String)
          : [searchFilters.issues],
      ],
      [
        "reviewers",
        Array.isArray(searchFilters.reviewer_ids)
          ? searchFilters.reviewer_ids.map(String)
          : [searchFilters.reviewer_ids],
      ],
      ["executionMetadata", filterValues("execution_metadata", searchFilters)],
    ] as const;
    for (const [id, values] of sets)
      handle.setFacetFilter(id, values.length ? [...values] : null);

    for (const [id, value] of [
      ["archived", searchFilters.artefact_is_archived],
      ["rerunRequested", searchFilters.rerun_is_requested],
      ["latestExecution", searchFilters.execution_is_latest],
    ] as const)
      handle.setFilter(
        id,
        value === null ? null : { operator: "equals", value: String(value) },
      );

    const { from_date: from, until_date: until } = searchFilters;
    handle.setFilter(
      "createdAt",
      from && until
        ? { operator: "between", value: from, valueTo: until }
        : from
          ? { operator: "greaterThan", value: from }
          : until
            ? { operator: "lessThan", value: until }
            : null,
    );
    filterStateHydrated = true;
  }

  function onGridFiltersChange(state: GridFilterState) {
    if (!filterStateHydrated) return;
    try {
      const adapted = searchFiltersFromGridState(state, filters);
      // SvGrid sorts selectedValues in its callback. Don't let that reorder a
      // typed list while the user is mid-edit, and ignore its initial empty
      // callback before URL state hydration has settled. The custom controls
      // write synchronously to the canonical draft; the external callback is
      // accepted once its exact snapshot agrees with that draft.
      if (gridFilterSnapshot(adapted) === gridFilterSnapshot(filters))
        onFilterState(adapted);
    } catch (error) {
      onFilterStateError(
        error instanceof Error
          ? error.message
          : "Unsupported SvGrid filter state.",
      );
    }
  }

  $effect(() => {
    const handle = api;
    const searchFilters = filters;
    if (!handle) return;
    untrack(() => syncGridFilters(handle, searchFilters));
  });

  // A dashboard's columns are not necessarily applicable to search results.
  // Preserve only applicable column visibility from older shared views.
  function applicableView(view: SharedGridView): SharedGridView {
    const ids = new Set(columns.map((column) => column.id));
    return {
      ...EMPTY_VIEW,
      ...view,
      // Server-backed infinite results retain newest-first API ordering. Local
      // sorting and filters would describe only the blocks currently cached.
      sorting: [],
      globalFilter: "",
      columnFilters: {},
      facetFilters: {},
      hiddenColumns: view.hiddenColumns?.filter((id) => ids.has(id)) ?? [],
      // All search columns are visible by default: there are no default-hidden
      // columns to reveal. Widths, order and pinning never enter shared state.
      shownColumns: [],
    };
  }

  function sharedState(handle: SvGridApi<never, Row>): SharedGridView {
    const { hiddenColumns } = handle.getState();
    return {
      sorting: [],
      globalFilter: "",
      columnFilters: {},
      facetFilters: {},
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

  // Search/reapply must capture even a visibility toggle made just before
  // the next polling tick, rather than copying a slightly stale URL snapshot.
  export function getSharedView(): string | null {
    return api && ownerQuery === queryKey
      ? encodeView(sharedState(api))
      : encodedView;
  }

  onMount(() => {
    // Installed SvGrid 3 has no visibility-change callback. Poll only the
    // shareable snapshot; no storage or named views are enabled for search.
    const timer = setInterval(syncView, 250);
    return () => clearInterval(timer);
  });
</script>

<div
  bind:this={gridRegion}
  class="results-grid"
  data-testid="search-grid-filters"
  role="region"
  aria-label="Search results grid"
  tabindex="-1"
>
  <SvGrid
    rowModel={rowModel as unknown as GridRowModel<RowData>}
    columns={columns as unknown as GridColumns}
    containerHeight="100%"
    virtualization
    columnVirtualization={false}
    sortable={false}
    filterable
    filterMode="none"
    externalFilter
    onFiltersChange={onGridFiltersChange}
    showGlobalFilter={false}
    columnResize
    enableRowHover
    selectionMode="none"
    showRowSelection={false}
    contextMenu={false}
    emptyMessage={blocked
      ? "Correct or clear the blocked search to load results."
      : "No test results match the applied conditions."}
    onApiReady={(handle) => {
      const gridApi = handle as unknown as SvGridApi<never, Row>;
      api = gridApi;
      untrack(() => syncGridFilters(gridApi, filters));
    }}
  />
</div>
<SearchGridValueDialog
  selection={activeValueDialog}
  onclose={closeValueDialog}
/>

<style>
  .results-grid {
    flex: 1;
    min-height: 0;
    min-width: 0;
    width: 100%;
  }
  /* Search keeps SvGrid's external filter state for its server-backed adapter,
     but its generic operator menu is not part of this exact-filter UI. In
     particular, an active built-in funnel can overlap our custom header
     trigger at narrow widths. */
  .results-grid :global(.sv-grid-column .sv-grid-col-filter-btn) {
    display: none;
  }
</style>
