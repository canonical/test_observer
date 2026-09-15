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
  import { page } from '$app/state';
  import type { Artefact } from '$lib/types';
  import { columnSortValue, filterValue } from '$lib/artefactMetadata';
  import { FilterIcon } from '@canonical/svelte-icons';
  import DashboardHeader from '$lib/components/dashboard/DashboardHeader.svelte';
  import FilterSidebar from '$lib/components/dashboard/FilterSidebar.svelte';
  import ArtefactTable from '$lib/components/dashboard/ArtefactTable.svelte';

  let { data } = $props();

  let sidebarVisible = $state(false);

  // --- Read URL state ---
  const searchQuery = $derived(page.url.searchParams.get('q') ?? '');
  const sortField = $derived(page.url.searchParams.get('sortBy') ?? 'name');
  const sortDir = $derived(page.url.searchParams.get('direction') ?? 'asc');

  const activeFilters = $derived.by(() => {
    const filters: Record<string, string[]> = {};
    for (const def of data.family.filters) {
      const values = page.url.searchParams.getAll(def.label);
      if (values.length > 0) {
        filters[def.label] = values;
      }
    }
    return filters;
  });

  const hasActiveFilters = $derived(
    Object.keys(activeFilters).length > 0 || searchQuery !== ''
  );

  // --- Filter pipeline ---
  const searchedArtefacts = $derived(
    searchQuery
      ? data.artefacts.filter((a: Artefact) =>
          a.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : data.artefacts
  );

  const filteredArtefacts = $derived.by(() => {
    return searchedArtefacts.filter((a: Artefact) => {
      for (const def of data.family.filters) {
        const active = activeFilters[def.label];
        if (!active || active.length === 0) continue;
        if (!active.includes(filterValue(a, def))) return false;
      }
      return true;
    });
  });

  // The 'sortBy' query parameter holds a column key; look up its spec so the
  // generic columnSortValue helper knows how to compare (no family branching).
  const sortColumn = $derived(data.family.columns.find((c) => c.key === sortField));

  const sortedArtefacts = $derived.by(() => {
    const arr = [...filteredArtefacts];
    const dir = sortDir === 'desc' ? -1 : 1;
    const col = sortColumn;
    arr.sort((a: Artefact, b: Artefact) => {
      const aVal = col ? columnSortValue(a, col) : '';
      const bVal = col ? columnSortValue(b, col) : '';
      if (aVal === null && bVal === null) return 0;
      if (aVal === null) return 1;
      if (bVal === null) return -1;
      if (aVal < bVal) return -dir;
      if (aVal > bVal) return dir;
      return 0;
    });
    return arr;
  });

  // --- Kanban grouping ---
  const artefactsByStage = $derived.by(() => {
    const stages = data.family.stages;
    const map = new Map<string, Artefact[]>();
    for (const stage of stages) map.set(stage, []);
    for (const a of sortedArtefacts) {
      const bucket = map.get(a.stage);
      if (bucket) bucket.push(a);
    }
    return map;
  });
</script>

<div class="dashboard">
  <DashboardHeader
    family={data.family}
    filteredCount={filteredArtefacts.length}
    totalCount={data.artefacts.length}
  />

  <div class="content-row">
    <div class="filter-toggle-area">
      <button
        class="filter-toggle"
        title="Toggle filters"
        onclick={() => (sidebarVisible = !sidebarVisible)}
      >
        <FilterIcon class="filter-icon" />
        {#if hasActiveFilters}
          <span class="badge"></span>
        {/if}
      </button>
    </div>

    <FilterSidebar artefacts={data.artefacts} family={data.family} visible={sidebarVisible} />

    {#if sidebarVisible}
      <div class="gap"></div>
    {/if}

    <div class="body">
      <ArtefactTable artefacts={sortedArtefacts} family={data.family} />
    </div>
  </div>
</div>

<style>
  .dashboard {
    padding-left: 0;
  }

  .content-row {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  .filter-toggle-area {
    flex-shrink: 0;
    padding-top: 4px;
  }

  .filter-toggle {
    position: relative;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 8px;
    color: var(--lp-color-text-muted);
  }

  .filter-toggle:hover {
    color: var(--lp-color-text-default);
  }

  .badge {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 8px;
    height: 8px;
    background: var(--lp-color-brand-default);
    border-radius: 50%;
  }

  .filter-icon {
    display: block;
  }

  .gap {
    width: 32px;
    flex-shrink: 0;
  }

  .body {
    flex: 1;
    min-width: 0;
    overflow-x: auto;
  }

  .kanban {
    display: flex;
    gap: 24px;
    overflow-x: auto;
    padding-bottom: 16px;
  }
</style>

