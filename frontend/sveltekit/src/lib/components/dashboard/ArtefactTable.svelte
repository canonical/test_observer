<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import { browser } from '$app/env';
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { Button, Checkbox, Popover, SearchBox, Select, Table } from '@canonical/svelte-ds-app-launchpad';
  import type { Artefact, ColumnSpec, Family } from '$lib/types';
  import { columnValue, columnColor } from '$lib/artefactMetadata';
  import { downloadCsv, toCsv } from '$lib/utils/csv';
  import {
    EMPTY_VIEW,
    filterArtefacts,
    nextSorting,
    PAGE_SIZES,
    pageCount,
    paginate,
    sortArtefacts,
    type TableView
  } from '$lib/tableView';
  import {
    VIEW_PARAM,
    decodeView,
    encodeView,
    loadLayout,
    saveLayout,
    type SharedTableView
  } from '$lib/tableViewUrl';

  let {
    artefacts,
    family,
    // The component only ever writes this prop, so the lint rule cannot see
    // that the default reaches the parent through the binding.
    // eslint-disable-next-line no-useless-assignment
    filtered = $bindable(false),
    // The current view may have no exportable content.
    // eslint-disable-next-line no-useless-assignment
    exportAvailable = $bindable(false)
  }: {
    artefacts: Artefact[];
    family: Family;
    /** Whether the table is filtered or sorted away from its defaults. */
    filtered?: boolean;
    /** Whether the current view can be exported. */
    exportAvailable?: boolean;
  } = $props();

  const hiddenByDefault = $derived(
    family.columns.filter((col) => col.hidden).map((col) => col.key)
  );

  let view = $state<TableView>({ ...EMPTY_VIEW, columnFilters: {} });
  let hiddenColumns = $state<string[]>([]);
  // The family whose state is currently held, so that switching dashboards
  // (the route component is reused across /snaps, /debs and friends) starts
  // from a clean table rather than carrying filters over.
  let initialisedFor: string | null = null;
  // Shallow goto throws before the router has initialised.
  let routerReady = $state(false);

  function applySharedState(shared: SharedTableView) {
    const { hiddenColumns: hide = [], shownColumns: show = [], ...rest } = shared;
    view = {
      sorting: rest.sorting ?? null,
      globalFilter: rest.globalFilter ?? '',
      columnFilters: rest.columnFilters ?? {}
    };
    hiddenColumns = [...new Set([...hiddenByDefault, ...hide])].filter(
      (id) => !show.includes(id)
    );
  }

  function initialise() {
    initialisedFor = family.name;
    view = { ...EMPTY_VIEW, columnFilters: {} };
    hiddenColumns = [...hiddenByDefault];
    if (!browser) return;
    // Layout first, then the link: a shared view's visibility should land on
    // top of the layout this tab was already using.
    const layout = loadLayout(family.name);
    if (layout) hiddenColumns = layout.hiddenColumns;
    const shared = decodeView(new URL(location.href).searchParams.get(VIEW_PARAM));
    if (shared) applySharedState(shared);
  }

  initialise();

  $effect.pre(() => {
    if (family.name !== initialisedFor) untrack(initialise);
  });

  onMount(() => {
    routerReady = true;
  });

  const visibleColumns = $derived(family.columns.filter((c) => !hiddenColumns.includes(c.key)));
  const visibleIds = $derived(new Set(visibleColumns.map((c) => c.key)));

  const rows = $derived(
    sortArtefacts(
      filterArtefacts(artefacts, family.columns, visibleIds, view),
      family.columns,
      view.sorting
    )
  );

  let pageSize = $state<number>(PAGE_SIZES[0]);
  let requestedPage = $state(0);
  const paged = $derived(paginate(rows, requestedPage, pageSize));
  const totalPages = $derived(pageCount(rows.length, pageSize));

  // Any change to what is shown starts again from the first page.
  $effect.pre(() => {
    void [view.sorting, view.globalFilter, view.columnFilters, hiddenColumns, family.name];
    untrack(() => (requestedPage = 0));
  });

  // Visibility is shared as a delta against the family's defaults: an untouched
  // dashboard encodes to nothing, while hiding an extra column or revealing a
  // default-hidden one both survive a shared link.
  const encodedView = $derived(
    encodeView({
      ...view,
      hiddenColumns: hiddenColumns.filter((id) => !hiddenByDefault.includes(id)),
      shownColumns: hiddenByDefault.filter((id) => !hiddenColumns.includes(id))
    })
  );

  $effect(() => {
    filtered = encodedView !== null;
    exportAvailable = visibleColumns.length > 0 && rows.length > 0;
  });

  $effect(() => {
    const hidden = $state.snapshot(hiddenColumns);
    if (initialisedFor === family.name) saveLayout(family.name, { hiddenColumns: hidden });
  });

  // Mirror the view into the URL so the current view is always the thing the
  // Share button hands out, and so a reload keeps it. location is the source
  // of truth rather than page.url, which does not react to shallow goto.
  function syncUrl() {
    if (!routerReady || !browser) return;
    const url = new URL(location.href);
    if (encodedView === null) {
      url.searchParams.delete(VIEW_PARAM);
    } else {
      url.searchParams.set(VIEW_PARAM, encodedView);
    }
    if (url.href !== location.href) {
      // Built from location.href, so the base path is already applied.
      void goto(url, { state: page.state, shallow: true, replace: true, reset: false });
    }
  }

  $effect(() => {
    void encodedView;
    untrack(syncUrl);
  });

  /** Drops every filter and returns to the default ordering. */
  export function clearView() {
    // Column visibility is restored to the family's defaults rather than
    // emptied, so clearing filters does not reveal its hidden columns.
    view = { ...EMPTY_VIEW, columnFilters: {} };
    hiddenColumns = [...hiddenByDefault];
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

  /** Downloads the rows currently shown as CSV, with the columns on screen. */
  export function exportCsv(): ExportResult {
    if (!browser) return 'unavailable';
    if (visibleColumns.length === 0) return 'no-visible-columns';
    if (rows.length === 0) return 'no-displayed-rows';
    const text = toCsv(
      visibleColumns.map((col) => col.label),
      rows.map((artefact) => visibleColumns.map((col) => columnValue(artefact, col)))
    );
    const date = new Date().toISOString().slice(0, 10);
    downloadCsv(`${family.name}-${date}.csv`, text);
    return 'exported';
  }

  function ariaSort(col: ColumnSpec): 'ascending' | 'descending' | 'none' {
    if (view.sorting?.id !== col.key) return 'none';
    return view.sorting.desc ? 'descending' : 'ascending';
  }

  function setColumnFilter(id: string, value: string) {
    view.columnFilters = { ...view.columnFilters, [id]: value };
  }

  function toggleColumn(id: string, visible: boolean) {
    hiddenColumns = visible ? hiddenColumns.filter((c) => c !== id) : [...hiddenColumns, id];
  }

  function artefactPath(id: number) {
    return resolve(`${family.name}/${id}`);
  }

  // Clicks on the row open the artefact; the link in the first cell keeps the
  // row reachable by keyboard and middle click, and handles its own clicks.
  function openArtefact(event: MouseEvent, id: number) {
    if ((event.target as HTMLElement).closest('a, button, input')) return;
    void goto(artefactPath(id));
  }
</script>

<div class="table-wrapper">
  <div class="toolbar">
    <SearchBox
      aria-label="Search artefacts"
      placeholder="Search"
      bind:value={view.globalFilter}
    />
    <Popover>
      {#snippet trigger(triggerProps)}
        <button class="columns-button" {...triggerProps}>Choose columns</button>
      {/snippet}
      <fieldset class="columns-menu">
        <legend>Visible columns</legend>
        {#each family.columns as col (col.key)}
          <label>
            <Checkbox
              checked={!hiddenColumns.includes(col.key)}
              onchange={(e) => toggleColumn(col.key, e.currentTarget.checked)}
            />
            {col.label}
          </label>
        {/each}
      </fieldset>
    </Popover>
  </div>

  <div class="scroller">
    <Table>
      <thead>
        <tr>
          {#each visibleColumns as col (col.key)}
            <Table.TH scope="col" aria-sort={ariaSort(col)}>
              {col.label}
              {#snippet action()}
                <Table.TH.SortButton
                  aria-label={`Sort by ${col.label}`}
                  onclick={() => (view.sorting = nextSorting(view.sorting, col.key))}
                />
              {/snippet}
            </Table.TH>
          {/each}
        </tr>
        <tr class="filter-row">
          {#each visibleColumns as col (col.key)}
            <th scope="col">
              <input
                type="search"
                aria-label={`Filter ${col.label}`}
                placeholder="Filter"
                value={view.columnFilters[col.key] ?? ''}
                oninput={(e) => setColumnFilter(col.key, e.currentTarget.value)}
              />
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each paged.rows as artefact (artefact.id)}
          <tr class="artefact-row" onclick={(e) => openArtefact(e, artefact.id)}>
            {#each visibleColumns as col, index (col.key)}
              {@const text = columnValue(artefact, col)}
              {@const color = columnColor(artefact, col)}
              <td>
                {#if index === 0}
                  <a href={artefactPath(artefact.id)}>{text}</a>
                {:else if color}
                  <span style="color: {color}">{text}</span>
                {:else}
                  {text}
                {/if}
              </td>
            {/each}
          </tr>
        {:else}
          <tr>
            <td colspan={Math.max(visibleColumns.length, 1)}>
              No artefacts match the current filters.
            </td>
          </tr>
        {/each}
      </tbody>
    </Table>
  </div>

  <nav class="pagination" aria-label="Table pagination">
    <label>
      Rows per page
      <Select bind:value={pageSize} density="dense">
        {#each PAGE_SIZES as size (size)}
          <option value={size}>{size}</option>
        {/each}
      </Select>
    </label>
    <span aria-live="polite">
      {rows.length === 0 ? 0 : paged.page * pageSize + 1}–{Math.min(
        (paged.page + 1) * pageSize,
        rows.length
      )} of {rows.length}
    </span>
    <Button
      density="dense"
      severity="base"
      aria-label="Previous page"
      disabled={paged.page === 0}
      onclick={() => (requestedPage = paged.page - 1)}>Previous</Button
    >
    <Button
      density="dense"
      severity="base"
      aria-label="Next page"
      disabled={paged.page >= totalPages - 1}
      onclick={() => (requestedPage = paged.page + 1)}>Next</Button
    >
  </nav>
</div>

<style>
  .table-wrapper {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    height: 100%;
    min-height: 0;
    width: 100%;
  }

  .toolbar {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .scroller {
    flex: 1;
    min-height: 0;
    overflow: auto;
  }

  .scroller :global(table) {
    width: 100%;
  }

  .scroller :global(thead) {
    position: sticky;
    top: 0;
    z-index: 1;
    background: var(--lp-color-background-default);
  }

  .filter-row th {
    font-weight: normal;
  }

  .filter-row input {
    width: 100%;
    box-sizing: border-box;
    font: inherit;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-input);
    border: 1px solid var(--lp-color-border-default);
    border-radius: 4px;
    padding: 0.125rem 0.375rem;
  }

  .pagination {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    justify-content: flex-end;
  }

  .pagination label {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .artefact-row {
    cursor: pointer;
  }

  .artefact-row:hover {
    background: var(--lp-color-background-hover);
  }

  .columns-button {
    font: inherit;
    color: var(--lp-color-text-default);
    background: transparent;
    border: 1px solid var(--lp-color-border-default);
    border-radius: 4px;
    padding: 0.25rem 0.75rem;
    cursor: pointer;
  }

  .columns-menu {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    border: none;
    margin: 0;
    padding: 0.5rem;
  }

  .columns-menu label {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
</style>
