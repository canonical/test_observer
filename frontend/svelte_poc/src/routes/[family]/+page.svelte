<script lang="ts">
  import { page } from '$app/state';
  import { FAMILY_STAGES, type Artefact, type Family } from '$lib/types';
  import { FAMILY_FILTERS } from '$lib/types/filters';
  import { viewModeStore } from '$lib/stores/view-mode.svelte';
  import DashboardHeader from '$lib/components/dashboard/DashboardHeader.svelte';
  import FilterSidebar from '$lib/components/dashboard/FilterSidebar.svelte';
  import StageColumn from '$lib/components/dashboard/StageColumn.svelte';
  import ArtefactTable from '$lib/components/dashboard/ArtefactTable.svelte';

  let { data } = $props();

  let sidebarVisible = $state(false);

  // --- Read URL state ---
  const searchQuery = $derived(page.url.searchParams.get('q') ?? '');
  const sortField = $derived(page.url.searchParams.get('sortBy') ?? 'name');
  const sortDir = $derived(page.url.searchParams.get('direction') ?? 'asc');

  const activeFilters = $derived.by(() => {
    const filters: Record<string, string[]> = {};
    const defs = FAMILY_FILTERS[data.family];
    for (const def of defs) {
      const values = page.url.searchParams.getAll(def.key);
      if (values.length > 0) {
        filters[def.key] = values;
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
    const defs = FAMILY_FILTERS[data.family];
    return searchedArtefacts.filter((a: Artefact) => {
      for (const def of defs) {
        const active = activeFilters[def.key];
        if (!active || active.length === 0) continue;
        const value = def.extract(a);
        if (!active.includes(value)) return false;
      }
      return true;
    });
  });

  const sortedArtefacts = $derived.by(() => {
    const arr = [...filteredArtefacts];
    const dir = sortDir === 'desc' ? -1 : 1;
    arr.sort((a: Artefact, b: Artefact) => {
      let aVal = getSortValue(a, sortField);
      let bVal = getSortValue(b, sortField);
      if (aVal === null && bVal === null) return 0;
      if (aVal === null) return 1;
      if (bVal === null) return -1;
      if (aVal < bVal) return -dir;
      if (aVal > bVal) return dir;
      return 0;
    });
    return arr;
  });

  function getSortValue(a: Artefact, field: string): string | number | null {
    switch (field) {
      case 'name': return a.name;
      case 'version': return a.version;
      case 'track': return a.track;
      case 'risk':
      case 'pocket': return a.stage;
      case 'branch': return a.branch;
      case 'series': return a.series;
      case 'repo': return a.repo;
      case 'source': return a.source;
      case 'os': return a.os;
      case 'release': return a.release;
      case 'owner': return a.owner;
      case 'dueDate': return a.due_date ?? null;
      case 'reviewsRemaining':
        return a.all_environment_reviews_count - a.completed_environment_reviews_count;
      case 'status': return a.status;
      case 'reviewers': return (a.reviewers?.length ?? 0) > 0 ? a.reviewers[0].name : null;
      default: return (a as any)[field] ?? '';
    }
  }

  // --- Kanban grouping ---
  const artefactsByStage = $derived.by(() => {
    const stages = FAMILY_STAGES[data.family];
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
        <svg class="filter-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M4.25 5.61C6.27 8.2 10 13 10 13v6c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-6s3.72-4.8 5.74-7.39c.51-.66.04-1.61-.79-1.61H5.04c-.83 0-1.3.95-.79 1.61z"/></svg>
        {#if hasActiveFilters}
          <span class="badge"></span>
        {/if}
      </button>
    </div>

    <FilterSidebar
      artefacts={data.artefacts}
      family={data.family}
      visible={sidebarVisible}
    />

    {#if sidebarVisible}
      <div class="gap"></div>
    {/if}

    <div class="body">
      {#if viewModeStore.mode === 'dashboard'}
        <div class="kanban">
          {#each FAMILY_STAGES[data.family] as stage}
            <StageColumn
              {stage}
              artefacts={artefactsByStage.get(stage) ?? []}
              family={data.family}
            />
          {/each}
        </div>
      {:else}
        <ArtefactTable artefacts={sortedArtefacts} family={data.family} />
      {/if}
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
    color: #555;
  }

  .filter-toggle:hover {
    color: #111;
  }

  .badge {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 8px;
    height: 8px;
    background: #e95420;
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
