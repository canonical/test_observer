<script lang="ts">
  import { base } from '$app/paths';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import type { Artefact, Family, ArtefactStatus } from '$lib/types';
  import { STATUS_COLORS, STATUS_LABELS } from '$lib/types';

  let { artefacts, family }: { artefacts: Artefact[]; family: Family } = $props();

  interface ColumnDef {
    label: string;
    key: string;
    flex: number;
    getValue: (a: Artefact) => string;
    color?: (a: Artefact) => string | undefined;
  }

  const COLUMNS: Record<Family, ColumnDef[]> = {
    snaps: [
      { label: 'Name', key: 'name', flex: 2, getValue: a => a.name },
      { label: 'Version', key: 'version', flex: 2, getValue: a => a.version },
      { label: 'Track', key: 'track', flex: 1, getValue: a => a.track },
      { label: 'Risk', key: 'risk', flex: 1, getValue: a => a.stage },
      { label: 'Branch', key: 'branch', flex: 1, getValue: a => a.branch },
      { label: 'Due date', key: 'dueDate', flex: 1, getValue: a => a.due_date ? new Date(a.due_date).toLocaleDateString() : '' },
      { label: 'Reviews', key: 'reviewsRemaining', flex: 1, getValue: a => String(a.all_environment_reviews_count - a.completed_environment_reviews_count) },
      { label: 'Status', key: 'status', flex: 1, getValue: a => STATUS_LABELS[a.status], color: a => STATUS_COLORS[a.status] },
      { label: 'Assignee', key: 'assignee', flex: 1, getValue: a => a.assignee?.name ?? '' },
    ],
    debs: [
      { label: 'Name', key: 'name', flex: 2, getValue: a => a.name },
      { label: 'Version', key: 'version', flex: 2, getValue: a => a.version },
      { label: 'Series', key: 'series', flex: 1, getValue: a => a.series },
      { label: 'Repo', key: 'repo', flex: 1, getValue: a => a.repo },
      { label: 'Pocket', key: 'pocket', flex: 1, getValue: a => a.stage },
      { label: 'Source', key: 'source', flex: 2, getValue: a => a.source },
      { label: 'Due date', key: 'dueDate', flex: 1, getValue: a => a.due_date ? new Date(a.due_date).toLocaleDateString() : '' },
      { label: 'Reviews', key: 'reviewsRemaining', flex: 1, getValue: a => String(a.all_environment_reviews_count - a.completed_environment_reviews_count) },
      { label: 'Status', key: 'status', flex: 1, getValue: a => STATUS_LABELS[a.status], color: a => STATUS_COLORS[a.status] },
      { label: 'Assignee', key: 'assignee', flex: 1, getValue: a => a.assignee?.name ?? '' },
    ],
    charms: [
      { label: 'Name', key: 'name', flex: 2, getValue: a => a.name },
      { label: 'Version', key: 'version', flex: 2, getValue: a => a.version },
      { label: 'Track', key: 'track', flex: 1, getValue: a => a.track },
      { label: 'Risk', key: 'risk', flex: 1, getValue: a => a.stage },
      { label: 'Branch', key: 'branch', flex: 1, getValue: a => a.branch },
      { label: 'Due date', key: 'dueDate', flex: 1, getValue: a => a.due_date ? new Date(a.due_date).toLocaleDateString() : '' },
      { label: 'Reviews', key: 'reviewsRemaining', flex: 1, getValue: a => String(a.all_environment_reviews_count - a.completed_environment_reviews_count) },
      { label: 'Status', key: 'status', flex: 1, getValue: a => STATUS_LABELS[a.status], color: a => STATUS_COLORS[a.status] },
      { label: 'Assignee', key: 'assignee', flex: 1, getValue: a => a.assignee?.name ?? '' },
    ],
    images: [
      { label: 'Name', key: 'name', flex: 2, getValue: a => a.name },
      { label: 'Version', key: 'version', flex: 1, getValue: a => a.version },
      { label: 'OS', key: 'os', flex: 1, getValue: a => a.os },
      { label: 'Release', key: 'release', flex: 1, getValue: a => a.release },
      { label: 'Owner', key: 'owner', flex: 1, getValue: a => a.owner },
      { label: 'Due date', key: 'dueDate', flex: 1, getValue: a => a.due_date ? new Date(a.due_date).toLocaleDateString() : '' },
      { label: 'Reviews', key: 'reviewsRemaining', flex: 1, getValue: a => String(a.all_environment_reviews_count - a.completed_environment_reviews_count) },
      { label: 'Status', key: 'status', flex: 1, getValue: a => STATUS_LABELS[a.status], color: a => STATUS_COLORS[a.status] },
      { label: 'Assignee', key: 'assignee', flex: 1, getValue: a => a.assignee?.name ?? '' },
    ],
  };

  const columns = $derived(COLUMNS[family]);
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
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  function navigateToArtefact(id: number) {
    goto(`${base}/${family}/${id}`);
  }
</script>

<div class="table-wrapper">
  <div class="header-row">
    {#each columns as col}
      <button
        class="header-cell"
        style="flex: {col.flex};"
        onclick={() => toggleSort(col.key)}
      >
        {col.label}
        {#if sortField === col.key}
          <span class="sort-arrow">{sortDir === 'asc' ? '↑' : '↓'}</span>
        {/if}
      </button>
    {/each}
  </div>

  <div class="separator"></div>

  {#each artefacts as artefact (artefact.id)}
    <button class="data-row" onclick={() => navigateToArtefact(artefact.id)}>
      {#each columns as col}
        <span
          class="data-cell"
          style="flex: {col.flex}; {col.color?.(artefact) ? `color: ${col.color(artefact)};` : ''}"
        >
          {col.getValue(artefact)}
        </span>
      {/each}
    </button>
    <div class="separator"></div>
  {/each}
</div>

<style>
  .table-wrapper {
    max-width: 1300px;
    width: 100%;
  }

  .header-row {
    display: flex;
    height: 56px;
    align-items: center;
  }

  .header-cell {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 0 8px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: inherit;
    color: #555;
  }

  .header-cell:hover {
    color: #111;
  }

  .sort-arrow {
    font-size: 0.75rem;
  }

  .separator {
    height: 1px;
    background: #e0e0e0;
  }

  .data-row {
    display: flex;
    height: 48px;
    align-items: center;
    width: 100%;
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
    font-family: inherit;
    padding: 0;
  }

  .data-row:hover {
    background: #f5f5f5;
  }

  .data-cell {
    padding: 0 8px;
    font-size: 0.85rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
