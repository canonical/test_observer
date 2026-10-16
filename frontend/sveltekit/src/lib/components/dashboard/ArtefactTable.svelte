<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { resolve } from '$app/paths';
  import { browser } from '$app/env';
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import {
    SvGrid,
    attachAutoSavedView,
    createNamedViews,
    renderComponent,
    type GridColumns,
    type SvGridApi
  } from '@svgrid/grid';
  import type { Artefact, ColumnSpec, Family } from '$lib/types';
  import { columnValue, columnColor, columnSortValue } from '$lib/artefactMetadata';
  import { downloadCsv, toCsv } from '$lib/utils/csv';
  import ColouredCell from './ColouredCell.svelte';
  import {
    AUTOSAVE_SLOT,
    EMPTY_VIEW,
    VIEW_PARAM,
    decodeView,
    encodeView,
    familyViewStorage,
    type SharedGridView
  } from '$lib/gridViewUrl';

  let {
    artefacts,
    family,
    // The component only ever writes this prop, so the lint rule cannot see
    // that the default reaches the parent through the binding.
    // eslint-disable-next-line no-useless-assignment
    filtered = $bindable(false),
    // The grid is unavailable while this component is mounting or between
    // family changes, and the current view may have no exportable content.
    // eslint-disable-next-line no-useless-assignment
    exportAvailable = $bindable(false),
  }: {
    artefacts: Artefact[];
    family: Family;
    /** Whether the grid is filtered or sorted away from its defaults. */
    filtered?: boolean;
    /** Whether the current view can be exported. */
    exportAvailable?: boolean;
  } = $props();

  // Tagged with the family it belongs to: switching dashboards remounts the
  // grid, and the outgoing instance must not write its state into the incoming
  // family's URL.
  let api = $state<{ family: string; handle: SvGridApi<never, Artefact> } | null>(null);
  // Null while the incoming family's grid is still mounting, so the header's
  // actions cannot reach the dashboard the user has just navigated away from.
  const currentApi = $derived(api?.family === family.name ? api.handle : null);
  // Shallow goto throws before the router has initialised, and restoring a
  // shared view fires the grid's change callbacks while still mounting.
  let routerReady = $state(false);

  onMount(() => {
    routerReady = true;
  });

  // The route component is reused across /snaps, /debs and friends, so without
  // this the header would keep offering to clear the previous family's filters
  // until the incoming grid reports its own state.
  $effect.pre(() => {
    if (api && api.family !== family.name) {
      filtered = false;
      exportAvailable = false;
    }
  });

  // Formats whose displayed text would sort and filter wrongly as a string
  // ("10" before "9", "9/18/2026" before "10/1/2026"), so the grid gets the
  // raw comparable value instead. Keyed on ColumnSpec.format, so this stays
  // generic across artefact families.
  const GRID_TYPE_BY_FORMAT: Record<string, 'number' | 'dateString'> = {
    reviewsRemaining: 'number',
    date: 'dateString',
  };

  const columns: GridColumns<Artefact> = $derived(
    family.columns.map((col) => {
      const cellDataType = GRID_TYPE_BY_FORMAT[col.format ?? ''];
      return {
        id: col.key,
        header: col.label,
        cellDataType,
        // Hidden columns stay listed in the grid's "Choose columns" menu, so
        // rarely-wanted artefact fields are available without crowding the
        // default view.
        visible: !col.hidden,
        // Everything else filters and sorts on the text the user can actually
        // see, so the filter menu lists "Approved" rather than "APPROVED".
        fieldFn: (a: Artefact) =>
          cellDataType ? columnSortValue(a, col) : columnValue(a, col),
        cell: (ctx) => {
          const artefact = ctx.row.original;
          const text = columnValue(artefact, col);
          const color = columnColor(artefact, col);
          return color ? renderComponent(ColouredCell, { text, color }) : text;
        }
      };
    })
  );

  const hiddenByDefault = $derived(
    family.columns.filter((col) => col.hidden).map((col) => col.key)
  );

  // The grid reports its declared-hidden columns as part of its state from the
  // moment it mounts, so visibility is shared as a delta against the family's
  // defaults: an untouched dashboard encodes to nothing, while hiding an extra
  // column or revealing a default-hidden one both survive a shared link.
  function sharedState(handle: SvGridApi<never, Artefact>): SharedGridView {
    const state = handle.getState();
    return {
      sorting: state.sorting,
      globalFilter: state.globalFilter,
      columnFilters: state.columnFilters,
      facetFilters: state.facetFilters,
      hiddenColumns: state.hiddenColumns.filter((id) => !hiddenByDefault.includes(id)),
      shownColumns: hiddenByDefault.filter((id) => !state.hiddenColumns.includes(id))
    };
  }

  /** Applies a decoded view, resolving its visibility delta back to a full set. */
  function applySharedState(handle: SvGridApi<never, Artefact>, view: SharedGridView) {
    const { hiddenColumns = [], shownColumns = [], ...filters } = view;
    const hidden = [...hiddenByDefault, ...hiddenColumns].filter(
      (id) => !shownColumns.includes(id)
    );
    handle.setState({ ...filters, hiddenColumns: [...new Set(hidden)] });
  }

  let detachAutosave: (() => void) | null = null;
  let exportAvailabilityTimer: ReturnType<typeof setInterval> | null = null;

  // If the grid later loads data incrementally (pagination or infinite
  // scrolling), keep export disabled until the displayed dataset is complete.
  function updateExportAvailability() {
    if (!currentApi) {
      exportAvailable = false;
      return;
    }

    const specByKey = new Set(family.columns.map((col) => col.key));
    const hasVisibleColumn = currentApi
      .getColumns()
      .some((col) => col.visible && specByKey.has(col.id));
    exportAvailable = hasVisibleColumn && currentApi.getDisplayedRows().length > 0;
  }

  function handleApiReady(ready: SvGridApi<never, Artefact>) {
    api = { family: family.name, handle: ready };
    if (!browser) return;

    // Switching families remounts only the keyed SvGrid, not this component, so
    // the previous grid's autosave would otherwise keep polling a dead grid.
    detachAutosave?.();
    detachAutosave = null;

    const views = createNamedViews(ready, { storage: familyViewStorage(family.name) });
    // Layout first, then the link: a shared view's filters should land on top of
    // the column widths and ordering this tab was already using.
    views.load(AUTOSAVE_SLOT);
    const shared = decodeView(new URL(location.href).searchParams.get(VIEW_PARAM));
    if (shared) applySharedState(ready, shared);
    filtered = encodeView(sharedState(ready)) !== null;
    updateExportAvailability();
    if (exportAvailabilityTimer) clearInterval(exportAvailabilityTimer);
    exportAvailabilityTimer = setInterval(updateExportAvailability, 250);

    // SvGrid has no column visibility or resize equivalent of onSortingChange,
    // so the manager polls getState() and saves when the snapshot changes.
    detachAutosave = attachAutoSavedView(ready, views, { skipRestore: true });
  }

  onDestroy(() => {
    exportAvailable = false;
    if (exportAvailabilityTimer) clearInterval(exportAvailabilityTimer);
    detachAutosave?.();
  });

  // Mirror the grid's state into the URL so the current view is always the
  // thing the Share button hands out, and so a reload keeps it. location is the
  // source of truth here rather than page.url, which does not react to the
  // shallow goto below and would go stale after the first write.
  function syncUrl() {
    if (!currentApi) return;
    const encoded = encodeView(sharedState(currentApi));
    filtered = encoded !== null;
    if (!routerReady || !browser) return;
    const url = new URL(location.href);
    if (encoded === null) {
      url.searchParams.delete(VIEW_PARAM);
    } else {
      url.searchParams.set(VIEW_PARAM, encoded);
    }
    if (url.href !== location.href) {
      // Built from location.href, so the base path is already applied.
      void goto(url, {
        state: page.state,
        shallow: true,
        replace: true,
        reset: false,
      });
    }
  }

  /** Drops every filter and returns to the grid's default ordering. */
  export function clearView() {
    if (!currentApi) return;
    // Column visibility is restored to the family's defaults rather than
    // emptied, so clearing filters does not reveal its hidden columns.
    currentApi.setState({ ...EMPTY_VIEW, hiddenColumns: [...hiddenByDefault] });
    syncUrl();
  }

  /** Absolute link reproducing the current filtering and sorting. */
  export function shareUrl(): string {
    syncUrl();
    return browser ? location.href : '';
  }

  type ExportResult =
    | 'exported'
    | 'unavailable'
    | 'no-visible-columns'
    | 'no-displayed-rows';

  /**
   * Downloads the rows the grid is currently showing as CSV, in the order and
   * with the columns on screen.
   */
  export function exportCsv(): ExportResult {
    if (!currentApi || !browser) return 'unavailable';
    // getColumns() reports visible columns first, in their visual order, so the
    // file matches the table even after the user reorders or hides columns.
    const specByKey = new Map(family.columns.map((col) => [col.key, col]));
    const columns = currentApi
      .getColumns()
      .filter((col) => col.visible)
      .map((col) => ({ header: col.header, spec: specByKey.get(col.id) }))
      .filter((col): col is { header: string; spec: ColumnSpec } => col.spec !== undefined);
    const rows = currentApi.getDisplayedRows();
    if (columns.length === 0) return 'no-visible-columns';
    if (rows.length === 0) return 'no-displayed-rows';

    const text = toCsv(
      columns.map((col) => col.header),
      rows.map((artefact) => columns.map((col) => columnValue(artefact, col.spec)))
    );
    const date = new Date().toISOString().slice(0, 10);
    downloadCsv(`${family.name}-${date}.csv`, text);
    return 'exported';
  }

  function openArtefact(id: string | number) {
    void goto(resolve(`${family.name}/${id}`));
  }
</script>

<!-- Keyed on the family so switching dashboards mounts a fresh grid: SvGrid
     keeps filter state internally, and the route component is reused across
     /snaps, /debs and friends, so without this the filters would follow you. -->
{#key family.name}
  <!-- selectionMode="none" because clicking a row opens the artefact, so cell
       and row selection would only fight with navigation. -->
  <div class="grid-wrapper">
    <SvGrid
      data={artefacts}
      {columns}
      getRowId={(a) => String(a.id)}
      containerHeight="100%"
      sortable
      filterable
      filterMode="menu"
      showGlobalFilter
      virtualization
      fitColumns
      columnResize
      enableRowHover
      selectionMode="none"
      emptyMessage="No artefacts match the current filters."
      onApiReady={handleApiReady}
      onSortingChange={syncUrl}
      onFiltersChange={syncUrl}
      onRowClick={({ row }) => openArtefact(row.id)}
    />
  </div>
{/key}

<style>
  .grid-wrapper {
    height: 100%;
    min-height: 0;
    width: 100%;
  }

  .grid-wrapper :global(.sg-row) {
    cursor: pointer;
  }
</style>
