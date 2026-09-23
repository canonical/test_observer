<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import { base } from '$app/paths';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import type { Artefact, Family } from '$lib/types';
  import { columnValue, columnColor } from '$lib/artefactMetadata';
  import { Table } from '@canonical/svelte-ds-app-launchpad';

  let { artefacts, family }: { artefacts: Artefact[]; family: Family } = $props();

  const columns = $derived(family.columns);
  const sortField = $derived(page.url.searchParams.get('sortBy') ?? '');
  const sortDir = $derived(page.url.searchParams.get('direction') ?? 'asc');

  function toggleSort(key: string) {
    const url = new URL(page.url);
    if (sortField === key) {
      url.searchParams.set('direction', sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      url.searchParams.set('sortBy', key);
      url.searchParams.set('direction', 'asc');
    }
    // Re-sorting reorders every row, so return to the first page.
    url.searchParams.delete('page');
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  function getSortState(key: string): 'ascending' | 'descending' | 'none' {
    if (sortField !== key) return 'none';
    return sortDir === 'asc' ? 'ascending' : 'descending';
  }
</script>

<div class="table-wrapper">
  <Table>
    <thead>
      <tr>
        {#each columns as col}
          <Table.TH aria-sort={getSortState(col.key)} scope="col">
            {col.label}
            {#snippet action()}<Table.TH.SortButton
                onclick={() => toggleSort(col.key)}
                aria-label="Sort by {col.label}"
              />{/snippet}
          </Table.TH>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each artefacts as artefact (artefact.id)}
        <tr class="clickable-row" onclick={() => goto(`${base}/${family.name}/${artefact.id}`)}>
          {#each columns as col}
            <td style={columnColor(artefact, col) ? `color: ${columnColor(artefact, col)}` : ''}>
              {columnValue(artefact, col)}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </Table>
</div>

<style>
  .table-wrapper {
    width: 100%;
    max-height: 100%;
    overflow-y: auto;
  }

  .clickable-row {
    cursor: pointer;
  }

  .clickable-row:hover {
    background: var(--lp-color-background-hover);
  }
</style>
