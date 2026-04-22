<script lang="ts">
  import { goto } from '$app/navigation';
  import { base } from '$app/paths';
  import { page } from '$app/state';
  import { IssuesListStore } from '$lib/stores/issues-list.svelte';
  import { ISSUE_SOURCES, ISSUE_STATUSES, DEFAULT_STATUSES } from '$lib/types/issues';
  import type { IssueSource, IssueStatus } from '$lib/types/issues';
  import IssueGroupHeader from '$lib/components/issues/IssueGroupHeader.svelte';
  import IssueRow from '$lib/components/issues/IssueRow.svelte';
  import AddIssueDialog from '$lib/components/issues/AddIssueDialog.svelte';

  const store = new IssuesListStore();
  let addDialogOpen = $state(false);

  const FAMILY_OPTIONS = ['snap', 'deb', 'charm', 'image'];

  $effect(() => {
    store.initFromUrl(page.url.searchParams);
  });

  // Initial fetch if no filters set on mount
  let initialized = false;
  $effect(() => {
    if (!initialized) {
      initialized = true;
      if (!store.hasFilters && store.issues.length === 0 && !store.loading) {
        store.fetchIssues();
      }
    }
  });

  function applyFilters() {
    const params = store.serializeToUrl();
    goto(`${base}/issues?${params}`, { replaceState: false });
  }

  function toggleSource(source: IssueSource) {
    const current = store.filters.source;
    const idx = current.indexOf(source);
    const next = idx >= 0 ? current.filter((s) => s !== source) : [...current, source];
    store.filters = { ...store.filters, source: next };
    applyFilters();
  }

  function toggleStatus(status: IssueStatus) {
    const current = store.filters.status;
    const idx = current.indexOf(status);
    const next = idx >= 0 ? current.filter((s) => s !== status) : [...current, status];
    store.filters = { ...store.filters, status: next };
    applyFilters();
  }

  function toggleFamily(family: string) {
    const current = store.filters.family;
    const idx = current.indexOf(family);
    const next = idx >= 0 ? current.filter((f) => f !== family) : [...current, family];
    store.filters = { ...store.filters, family: next };
    applyFilters();
  }

  function setProject(project: string) {
    store.filters = { ...store.filters, project };
    applyFilters();
  }

  let searchTimeout: ReturnType<typeof setTimeout> | null = null;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    store.filters = { ...store.filters, q: val };
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => applyFilters(), 400);
  }

  function handleIssueAdded(id: number) {
    addDialogOpen = false;
    goto(`${base}/issues/${id}`);
  }

  function clearFilters() {
    store.filters = { source: [], status: [...DEFAULT_STATUSES], family: [], project: '', q: '' };
    applyFilters();
  }
</script>

<div class="issues-page">
  <div class="page-header">
    <h1>Linked External Issues</h1>
    <button class="btn-add-link" onclick={() => (addDialogOpen = true)}>
      + add issue
    </button>
  </div>

  <div class="content-row">
    <aside class="sidebar">
      <div class="sidebar-section">
        <label class="search-label">
          Search
          <input
            type="text"
            class="search-input"
            value={store.filters.q}
            oninput={handleSearchInput}
            placeholder="Search issues..."
          />
        </label>
      </div>

      <details open class="filter-section">
        <summary>Source</summary>
        <div class="filter-body">
          {#each ISSUE_SOURCES as src (src)}
            <label class="checkbox-option">
              <input type="checkbox" checked={store.filters.source.includes(src)} onchange={() => toggleSource(src)} />
              {src.charAt(0).toUpperCase() + src.slice(1)}
            </label>
          {/each}
        </div>
      </details>

      <details open class="filter-section">
        <summary>Status</summary>
        <div class="filter-body">
          {#each ISSUE_STATUSES as st (st)}
            <label class="checkbox-option">
              <input type="checkbox" checked={store.filters.status.includes(st)} onchange={() => toggleStatus(st)} />
              {st.charAt(0).toUpperCase() + st.slice(1)}
            </label>
          {/each}
        </div>
      </details>

      <details open class="filter-section">
        <summary>Family</summary>
        <div class="filter-body">
          {#each FAMILY_OPTIONS as fam (fam)}
            <label class="checkbox-option">
              <input type="checkbox" checked={store.filters.family.includes(fam)} onchange={() => toggleFamily(fam)} />
              {fam.charAt(0).toUpperCase() + fam.slice(1)}
            </label>
          {/each}
        </div>
      </details>

      {#if store.projectOptions.length > 0}
        <details open class="filter-section">
          <summary>Project</summary>
          <div class="filter-body">
            <select class="project-select" value={store.filters.project} onchange={(e) => setProject((e.target as HTMLSelectElement).value)}>
              <option value="">All projects</option>
              {#each store.projectOptions as proj (proj)}
                <option value={proj}>{proj}</option>
              {/each}
            </select>
          </div>
        </details>
      {/if}

      {#if store.hasFilters}
        <button class="btn-clear-filters" onclick={clearFilters}>Clear all filters</button>
      {/if}
    </aside>

    <main class="issues-main">
      {#if store.loading}
        <div class="loading-state">
          <div class="spinner"></div>
          <p>Loading issues...</p>
        </div>
      {:else if store.error}
        <div class="error-state">
          <p>{store.error}</p>
        </div>
      {:else if store.issues.length === 0}
        <div class="empty-state">
          <h2>No issues found</h2>
          <p>Try adjusting your filters or add a new issue.</p>
        </div>
      {:else}
        {#each store.grouped as group (`${group.source}:${group.project}`)}
          <IssueGroupHeader source={group.source} project={group.project} />
          {#each group.issues as issue (issue.id)}
            <IssueRow {issue} />
          {/each}
        {/each}

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

  <AddIssueDialog
    open={addDialogOpen}
    onadd={handleIssueAdded}
    onclose={() => (addDialogOpen = false)}
  />
</div>

<style>
  .issues-page {
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

  .page-header h1 {
    margin: 0;
    font-size: 22px;
    font-weight: 600;
  }

  .btn-add-link {
    background: none;
    color: #E95420;
    border: none;
    padding: 6px 16px;
    font-size: 13px;
    cursor: pointer;
    font-weight: 500;
    text-transform: lowercase;
  }

  .btn-add-link:hover {
    text-decoration: underline;
  }

  .content-row {
    display: flex;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .sidebar {
    width: 240px;
    min-width: 240px;
    border-right: 1px solid #e0e0e0;
    overflow-y: auto;
    padding: 12px;
    font-size: 13px;
    background: #fafafa;
  }

  .sidebar-section {
    margin-bottom: 16px;
  }

  .filter-section {
    border-bottom: 1px solid #e8e8e8;
  }

  .filter-section summary {
    padding: 8px 0;
    cursor: pointer;
    font-weight: 500;
    font-size: 13px;
    color: #333;
    user-select: none;
    list-style: none;
  }

  .filter-section summary::before {
    content: '▸ ';
    font-size: 11px;
    color: #999;
  }

  .filter-section[open] > summary::before {
    content: '▾ ';
  }

  .filter-body {
    padding: 0 0 10px 0;
  }

  .search-label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
    color: #333;
  }

  .search-input {
    padding: 6px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    outline: none;
  }

  .search-input:focus {
    border-color: #E95420;
  }

  .checkbox-option {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 0;
    cursor: pointer;
    font-size: 13px;
  }

  .project-select {
    width: 100%;
    padding: 5px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    background: white;
  }

  .project-select:focus {
    border-color: #E95420;
    outline: none;
  }

  .btn-clear-filters {
    background: none;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
    cursor: pointer;
    color: #555;
    width: 100%;
    margin-top: 4px;
  }

  .btn-clear-filters:hover {
    border-color: #E95420;
    color: #E95420;
  }

  .issues-main {
    flex: 1;
    min-width: 0;
    overflow-y: auto;
    padding: 0 24px 16px;
  }

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
  }

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
    margin: 0 0 4px;
    font-size: 18px;
    color: #555;
  }

  .empty-state p {
    margin: 0;
    font-size: 14px;
    color: #999;
  }

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
