<script lang="ts">
  import { base } from '$app/paths';
  import { page } from '$app/state';
  import { TestResultsStore } from '$lib/stores/test-results.svelte';
  import FilterPanel from '$lib/components/test-results/FilterPanel.svelte';
  import BulkOperations from '$lib/components/test-results/BulkOperations.svelte';
  import ResultDetailDialog from '$lib/components/test-results/ResultDetailDialog.svelte';
  import type { TestResultWithContext } from '$lib/types/test-results';

  const store = new TestResultsStore();
  let detailRow = $state<TestResultWithContext | null>(null);

  let filterPanelVisible = $state(true);

  // React to URL search params changes
  $effect(() => {
    store.initFromUrl(page.url.searchParams);
  });

  // Load metadata options once
  $effect(() => {
    store.loadMetadata();
  });

  const resultCountLabel = $derived(
    store.totalCount === 1
      ? '1 result'
      : `${store.totalCount.toLocaleString()} results`,
  );
</script>

<div class="test-results-page">
  <div class="page-header">
    <div class="title-row">
      <h1>Test Results</h1>
      {#if store.hasFilters}
        <span class="result-count">{resultCountLabel}</span>
      {/if}
    </div>
    <button
      class="filter-toggle"
      title="Toggle filters"
      onclick={() => (filterPanelVisible = !filterPanelVisible)}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M4.25 5.61C6.27 8.2 10 13 10 13v6c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-6s3.72-4.8 5.74-7.39c.51-.66.04-1.61-.79-1.61H5.04c-.83 0-1.3.95-.79 1.61z"/></svg>
      {#if store.hasFilters}
        <span class="badge"></span>
      {/if}
    </button>
  </div>

  <div class="content-row">
    {#if filterPanelVisible}
      <FilterPanel {store} />
    {/if}

    <main class="results-main">
      {#if store.hasFilters}
        <BulkOperations {store} />
      {/if}

      {#if !store.hasFilters && !store.loading}
        <!-- Empty state: no filters applied -->
        <div class="empty-state">
          <svg class="empty-icon" width="64" height="64" viewBox="0 0 24 24" fill="#ccc">
            <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
          <h2>Search for test results</h2>
          <p>Use the filters to search across all test results.</p>
        </div>
      {:else if store.loading}
        <!-- Loading state -->
        <div class="loading-state">
          <div class="spinner"></div>
          <p>Loading test results...</p>
        </div>
      {:else if store.error}
        <!-- Error state -->
        <div class="error-state">
          <svg class="error-icon" width="48" height="48" viewBox="0 0 24 24" fill="#c7162b">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          <p>{store.error}</p>
        </div>
      {:else if store.results.length === 0}
        <!-- No results -->
        <div class="empty-state">
          <h2>No results found</h2>
          <p>Try adjusting your filters to find test results.</p>
        </div>
      {:else}
        <!-- Results table -->
        <div class="results-summary">
          Showing {store.results.length} of {store.totalCount.toLocaleString()} results
        </div>
        <div class="results-grid" role="table">
          <div class="grid-header" role="row">
            <span role="columnheader">Artefact</span>
            <span role="columnheader">Test Case</span>
            <span role="columnheader">Test Execution ID</span>
            <span role="columnheader">Status</span>
            <span role="columnheader">Track</span>
            <span role="columnheader">Version</span>
            <span role="columnheader">Environment</span>
            <span role="columnheader">Test Plan</span>
            <span role="columnheader">Actions</span>
          </div>
          {#each store.results as row (row.test_result.id)}
            <div class="grid-row" role="row">
              <span class="cell cell-artefact" role="cell" title={row.artefact.name}>{row.artefact.name}</span>
              <span class="cell cell-testcase" role="cell" title={row.test_result.name}>
                {row.test_result.name}
                {#if row.test_result.category}
                  <span class="category-sub">{row.test_result.category}</span>
                {/if}
              </span>
              <span class="cell" role="cell">{row.test_execution.id}</span>
              <span class="cell" role="cell">
                <span
                  class="status-badge"
                  class:passed={row.test_result.status === 'PASSED'}
                  class:failed={row.test_result.status === 'FAILED'}
                  class:skipped={row.test_result.status === 'SKIPPED'}
                >
                  {row.test_result.status}
                </span>
              </span>
              <span class="cell" role="cell">{row.artefact.track || '—'}</span>
              <span class="cell cell-version" role="cell" title={row.artefact.version}>{row.artefact.version}</span>
              <span class="cell" role="cell">{row.test_execution.environment.architecture}/{row.test_execution.environment.name}</span>
              <span class="cell cell-plan" role="cell" title={row.test_execution.test_plan || ''}>{row.test_execution.test_plan || '—'}</span>
              <span class="cell cell-actions" role="cell">
                <button class="action-link" onclick={() => (detailRow = row)}>Details</button>
                <a class="action-link" href="{base}/{row.artefact.family}s/{row.artefact.id}">View Run</a>
              </span>
            </div>
          {/each}
        </div>

        <ResultDetailDialog row={detailRow} onclose={() => (detailRow = null)} />

        {#if store.hasMore}
          <div class="load-more">
            <button class="btn-load-more" onclick={() => store.loadMore()} disabled={store.loadingMore}>
              {store.loadingMore ? 'Loading...' : 'Load more'}
            </button>
          </div>
        {/if}
      {/if}
    </main>
  </div>
</div>

<style>
  .test-results-page {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    border-bottom: 1px solid #e0e0e0;
    flex-shrink: 0;
  }

  .title-row {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .title-row h1 {
    margin: 0;
    font-size: 22px;
    font-weight: 600;
  }

  .result-count {
    font-size: 14px;
    color: #666;
  }

  .filter-toggle {
    position: relative;
    background: none;
    border: none;
    cursor: pointer;
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
    background: #E95420;
    border-radius: 50%;
  }

  .content-row {
    display: flex;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .results-main {
    flex: 1;
    min-width: 0;
    overflow-y: auto;
    padding: 16px 24px;
  }

  /* Empty state */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 24px;
    color: #888;
    text-align: center;
  }

  .empty-state h2 {
    margin: 16px 0 4px;
    font-size: 18px;
    color: #555;
  }

  .empty-state p {
    margin: 0;
    font-size: 14px;
    color: #999;
  }

  .empty-icon {
    opacity: 0.5;
  }

  /* Loading state */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 80px 0;
    color: #888;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #e0e0e0;
    border-top-color: #E95420;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 12px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Error state */
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 80px 0;
    text-align: center;
  }

  .error-state p {
    color: #c7162b;
    font-size: 14px;
    margin-top: 12px;
  }

  /* Results grid */
  .results-summary {
    font-size: 13px;
    color: #666;
    margin-bottom: 8px;
  }

  .results-grid {
    width: 100%;
    font-size: 13px;
  }

  .grid-header,
  .grid-row {
    display: grid;
    grid-template-columns: 3fr 4fr 3fr 2fr 2fr 3fr 3fr 3fr 3fr;
    gap: 0 8px;
    align-items: start;
    padding: 0 4px;
  }

  .grid-header {
    font-weight: 600;
    color: #555;
    padding-top: 8px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e0e0e0;
    white-space: nowrap;
  }

  .grid-row {
    padding-top: 6px;
    padding-bottom: 6px;
    border-bottom: 1px solid #f0f0f0;
  }

  .grid-row:hover {
    background: #fafafa;
  }

  .cell {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .cell-artefact {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .cell-testcase {
    display: flex;
    flex-direction: column;
    gap: 1px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    min-width: 0;
  }

  .category-sub {
    font-size: 11px;
    color: #999;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cell-version {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .cell-plan {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .cell-actions {
    display: flex;
    gap: 12px;
    white-space: nowrap;
  }

  .action-link {
    background: none;
    border: none;
    color: #E95420;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    padding: 0;
    text-decoration: none;
  }

  .action-link:hover {
    text-decoration: underline;
  }

  .status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .status-badge.passed {
    background: #e8f5e9;
    color: #0e8420;
  }

  .status-badge.failed {
    background: #fce4ec;
    color: #c7162b;
  }

  .status-badge.skipped {
    background: #f5f5f5;
    color: #888;
  }

  /* Load more */
  .load-more {
    display: flex;
    justify-content: center;
    padding: 16px 0;
  }

  .btn-load-more {
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px 24px;
    font-size: 13px;
    cursor: pointer;
    color: #555;
  }

  .btn-load-more:hover:not(:disabled) {
    border-color: #E95420;
    color: #E95420;
  }

  .btn-load-more:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
