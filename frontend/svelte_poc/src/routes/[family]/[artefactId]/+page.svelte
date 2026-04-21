<script lang="ts">
  import { page } from '$app/state';
  import { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import type { Family } from '$lib/types';
  import ArtefactPageHeader from '$lib/components/artefact/ArtefactPageHeader.svelte';
  import ArtefactPageSidebar from '$lib/components/artefact/ArtefactPageSidebar.svelte';
  import ArtefactPageBody from '$lib/components/artefact/ArtefactPageBody.svelte';

  let { data } = $props();
  const family = $derived(data.family as Family);
  const artefactId = $derived(data.artefactId);

  const store = new ArtefactPageStore();

  let sidebarOpen = $state(true);

  // Read active filter count from URL for the badge
  function countActiveFilters(): number {
    const keys = ['environment', 'test_plan', 'review_status', 'execution_status', 'plans_last_run'];
    let count = 0;
    for (const key of keys) {
      const val = page.url.searchParams.get(key);
      if (val) count += val.split(',').length;
    }
    return count;
  }

  const activeFilterCount = $derived(countActiveFilters());

  $effect(() => {
    store.init(artefactId);
  });
</script>

{#if store.loading && !store.artefact}
  <div class="loading">
    <span class="material-symbols-outlined spin">progress_activity</span>
    <span>Loading artefact...</span>
  </div>
{:else if store.artefact}
  <div class="artefact-page">
    <ArtefactPageHeader
      artefact={store.artefact}
      {family}
      versions={store.versions}
      {store}
    />

    <div class="page-body">
      <div class="toolbar">
        <button
          class="sidebar-toggle"
          onclick={() => (sidebarOpen = !sidebarOpen)}
          title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
        >
          <span class="material-symbols-outlined">
            {sidebarOpen ? 'side_navigation' : 'side_navigation'}
          </span>
          {#if !sidebarOpen && activeFilterCount > 0}
            <span class="filter-badge">{activeFilterCount}</span>
          {/if}
        </button>
      </div>

      <div class="content-area">
        {#if sidebarOpen}
          <ArtefactPageSidebar
            artefact={store.artefact}
            {family}
            {artefactId}
            {store}
          />
        {/if}

        <div class="main-content">
          {#if store.loading}
            <div class="loading-inline">
              <span class="material-symbols-outlined spin">progress_activity</span>
              Loading test data...
            </div>
          {:else if store.allEnvironments.length === 0}
            <div class="empty-state">
              <span class="material-symbols-outlined empty-icon">inbox</span>
              <p>No test executions found for this artefact.</p>
            </div>
          {:else}
            <ArtefactPageBody
              {artefactId}
              {family}
              environments={store.allEnvironments}
              {store}
            />
          {/if}
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="error-state">
    <span class="material-symbols-outlined">error</span>
    <p>Failed to load artefact.</p>
  </div>
{/if}

<style>
  .artefact-page {
    display: flex;
    flex-direction: column;
    gap: 0;
    min-height: calc(100vh - 120px);
  }

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 64px 0;
    color: #666;
    font-size: 16px;
  }

  .loading-inline {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 32px 16px;
    color: #666;
    font-size: 14px;
  }

  .spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .page-body {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .toolbar {
    display: flex;
    align-items: center;
    padding: 8px 0;
    gap: 8px;
  }

  .sidebar-toggle {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 8px;
    border: 1px solid #ddd;
    border-radius: 6px;
    background: #fff;
    cursor: pointer;
    font-family: inherit;
    color: #555;
    position: relative;
  }

  .sidebar-toggle:hover {
    background: #f5f5f5;
    border-color: #ccc;
  }

  .filter-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 9px;
    background: #E95420;
    color: #fff;
    font-size: 11px;
    font-weight: 600;
  }

  .content-area {
    display: flex;
    flex: 1;
    min-height: 0;
  }

  .main-content {
    flex: 1;
    min-width: 0;
    padding: 16px;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 64px 0;
    color: #999;
  }

  .empty-state :global(.material-symbols-outlined) {
    font-size: 48px;
  }

  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 64px 0;
    color: #C7162B;
  }

  .error-state :global(.material-symbols-outlined) {
    font-size: 48px;
  }
</style>
