<script lang="ts">
  import type { Family, ViewMode } from '$lib/types';
  import { FAMILY_TITLES } from '$lib/types';
  import { viewModeStore } from '$lib/stores/view-mode.svelte';

  let { family, filteredCount, totalCount }: {
    family: Family;
    filteredCount: number;
    totalCount: number;
  } = $props();

  const title = $derived(FAMILY_TITLES[family]);
  const countText = $derived(
    filteredCount === totalCount
      ? `${totalCount} artifacts`
      : `${filteredCount} of ${totalCount} artifacts`
  );
</script>

<header class="dashboard-header">
  <div class="title-group">
    <h1 class="title">{title}</h1>
    <span class="count">{countText}</span>
  </div>
  <div class="view-toggle">
    <button
      class="toggle-btn"
      class:active={viewModeStore.mode === 'list'}
      title="List view"
      onclick={() => viewModeStore.set('list')}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
    </button>
    <button
      class="toggle-btn"
      class:active={viewModeStore.mode === 'dashboard'}
      title="Dashboard view"
      onclick={() => viewModeStore.set('dashboard')}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 3h8v8H3V3zm0 10h8v8H3v-8zm10-10h8v8h-8V3zm0 10h8v8h-8v-8z"/></svg>
    </button>
  </div>
</header>

<style>
  .dashboard-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 32px 0 16px;
  }

  .title-group {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .title {
    font-size: 1.6rem;
    font-weight: 400;
    margin: 0;
  }

  .count {
    font-size: 1rem;
    color: #888;
  }

  .view-toggle {
    display: flex;
    gap: 2px;
  }

  .toggle-btn {
    padding: 6px 10px;
    border: 1px solid #ccc;
    background: white;
    cursor: pointer;
    font-size: 1rem;
    color: #666;
    font-family: inherit;
  }

  .toggle-btn.active {
    background: #f0f0f0;
    color: #e95420;
    border-color: #e95420;
  }

  .toggle-btn:first-child {
    border-radius: 4px 0 0 4px;
  }

  .toggle-btn:last-child {
    border-radius: 0 4px 4px 0;
  }
</style>
