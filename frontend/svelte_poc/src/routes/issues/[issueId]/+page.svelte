<script lang="ts">
  import { base } from '$app/paths';
  import { page } from '$app/state';
  import { IssueDetailStore } from '$lib/stores/issue-detail.svelte';
  import { issueDisplayKey } from '$lib/types/issues';
  import { emptyFilters } from '$lib/types/test-results';
  import type { TestResultWithContext } from '$lib/types/test-results';
  import AttachmentRuleCard from '$lib/components/issues/AttachmentRuleCard.svelte';
  import IssueDetailFilterPanel from '$lib/components/issues/IssueDetailFilterPanel.svelte';
  import ResultDetailDialog from '$lib/components/test-results/ResultDetailDialog.svelte';

  const store = new IssueDetailStore();

  let filterPanelVisible = $state(false);
  let expandedRuleId = $state<number | null>(null);
  let detailRow = $state<TestResultWithContext | null>(null);

  // Rerun dialog state
  let createRerunsDialog = $state<HTMLDialogElement | null>(null);
  let deleteRerunsDialog = $state<HTMLDialogElement | null>(null);
  let rerunBusy = $state(false);

  $effect(() => {
    const id = Number(page.params.issueId);
    if (!isNaN(id)) {
      store.loadIssue(id);
      store.searchResults(emptyFilters());
    }
  });

  $effect(() => {
    const ruleParam = page.url.searchParams.get('attachmentRule');
    if (ruleParam) {
      expandedRuleId = Number(ruleParam);
    }
  });

  const displayKey = $derived(store.issue ? issueDisplayKey(store.issue) : '');

  const statusClass = $derived(
    store.issue?.status === 'open'
      ? 'status-open'
      : store.issue?.status === 'closed'
        ? 'status-closed'
        : 'status-unknown',
  );

  const resultCountLabel = $derived(
    store.totalCount === 1
      ? '1 result'
      : `${store.totalCount.toLocaleString()} results`,
  );

  function openDialog(dialog: HTMLDialogElement | null) {
    rerunBusy = false;
    dialog?.showModal();
  }

  function closeDialog(dialog: HTMLDialogElement | null) {
    dialog?.close();
    rerunBusy = false;
  }

  async function handleCreateReruns() {
    rerunBusy = true;
    await store.createReruns(store.appliedFilters);
    rerunBusy = false;
    closeDialog(createRerunsDialog);
    store.searchResults(store.appliedFilters);
  }

  async function handleDeleteReruns() {
    rerunBusy = true;
    await store.deleteReruns(store.appliedFilters);
    rerunBusy = false;
    closeDialog(deleteRerunsDialog);
    store.searchResults(store.appliedFilters);
  }
</script>

<div class="issue-detail-page">
  {#if store.issueLoading}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading issue...</p>
    </div>
  {:else if store.issueError}
    <div class="error-state">
      <p>{store.issueError}</p>
    </div>
  {:else if store.issue}
    {@const issue = store.issue}

    <!-- Header -->
    <div class="issue-header">
      <div class="header-top">
        <a href="{base}/issues" class="back-link">&larr; Issues</a>
      </div>
      <div class="header-main">
        <span class="source-badge">{issue.source.toUpperCase()}</span>
        <span class="project-name">{issue.project}</span>
        <a href={issue.url} target="_blank" rel="noopener noreferrer" class="issue-key-link">
          {displayKey}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
        </a>
        <span class="issue-status {statusClass}">
          {#if issue.status === 'open'}
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
            Open
          {:else if issue.status === 'closed'}
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/></svg>
            Closed
          {:else}
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"/></svg>
            Unknown
          {/if}
        </span>
      </div>
      <h1 class="issue-title">{issue.title || '[No title]'}</h1>
      {#if issue.labels && issue.labels.length > 0}
        <div class="labels-row">
          {#each issue.labels as label (label)}
            <span class="label-chip">{label}</span>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Attachment Rules -->
    <section class="section">
      <h2 class="section-title">
        Attachment Rules
        <span class="section-count">({issue.attachment_rules.length})</span>
      </h2>
      {#if issue.attachment_rules.length === 0}
        <p class="no-items">No attachment rules configured for this issue.</p>
      {:else}
        {#each issue.attachment_rules as rule (rule.id)}
          <AttachmentRuleCard
            {rule}
            expanded={expandedRuleId === rule.id}
            onenable={(id) => store.enableRule(id)}
            ondisable={(id) => store.disableRule(id)}
            ondelete={(id) => store.deleteRule(id)}
          />
        {/each}
      {/if}
    </section>

    <!-- Test Results -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">
          Test Results
          {#if store.totalCount > 0}
            <span class="section-count">({resultCountLabel})</span>
          {/if}
        </h2>
        <div class="section-actions">
          <button class="btn-bulk" onclick={() => openDialog(createRerunsDialog)}>Create Rerun Requests</button>
          <button class="btn-bulk" onclick={() => openDialog(deleteRerunsDialog)}>Delete Rerun Requests</button>
          <button
            class="filter-toggle"
            title="Toggle filters"
            onclick={() => (filterPanelVisible = !filterPanelVisible)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M4.25 5.61C6.27 8.2 10 13 10 13v6c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-6s3.72-4.8 5.74-7.39c.51-.66.04-1.61-.79-1.61H5.04c-.83 0-1.3.95-.79 1.61z"/></svg>
            {#if store.hasFilters}
              <span class="filter-badge"></span>
            {/if}
          </button>
        </div>
      </div>

      <div class="results-area">
        {#if filterPanelVisible}
          <IssueDetailFilterPanel {store} />
        {/if}

        <div class="results-content">
          {#if store.resultsLoading}
            <div class="loading-state">
              <div class="spinner"></div>
              <p>Loading test results...</p>
            </div>
          {:else if store.results.length === 0}
            <div class="empty-results">
              <p>No test results found for this issue.</p>
            </div>
          {:else}
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

            {#if store.hasMore}
              <div class="load-more">
                <button class="btn-load-more" onclick={() => store.loadMoreResults()} disabled={store.resultsLoadingMore}>
                  {store.resultsLoadingMore ? 'Loading...' : 'Load more'}
                </button>
              </div>
            {/if}
          {/if}
        </div>
      </div>
    </section>
  {/if}
</div>

<!-- Create Rerun Requests Dialog -->
<dialog bind:this={createRerunsDialog} class="bulk-dialog" onclose={() => (rerunBusy = false)}>
  <h3>Create Rerun Requests</h3>
  <p class="dialog-subtitle">Create rerun requests for {store.totalCount.toLocaleString()} matching test results.</p>
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(createRerunsDialog)}>Cancel</button>
    <button class="btn-submit" disabled={rerunBusy} onclick={handleCreateReruns}>
      {rerunBusy ? 'Working...' : 'Create Reruns'}
    </button>
  </div>
</dialog>

<!-- Delete Rerun Requests Dialog -->
<dialog bind:this={deleteRerunsDialog} class="bulk-dialog" onclose={() => (rerunBusy = false)}>
  <h3>Delete Rerun Requests</h3>
  <p class="dialog-subtitle">Delete rerun requests for {store.totalCount.toLocaleString()} matching test results.</p>
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(deleteRerunsDialog)}>Cancel</button>
    <button class="btn-submit btn-danger" disabled={rerunBusy} onclick={handleDeleteReruns}>
      {rerunBusy ? 'Working...' : 'Delete Reruns'}
    </button>
  </div>
</dialog>

<ResultDetailDialog row={detailRow} onclose={() => (detailRow = null)} />

<style>
  .issue-detail-page {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
  }

  /* Header */
  .issue-header {
    padding: 16px 24px;
    border-bottom: 1px solid #e0e0e0;
  }

  .header-top {
    margin-bottom: 8px;
  }

  .back-link {
    font-size: 13px;
    color: #E95420;
    text-decoration: none;
  }

  .back-link:hover {
    text-decoration: underline;
  }

  .header-main {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
  }

  .source-badge {
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1px;
    color: #333;
    background: #f0f0f0;
    padding: 2px 8px;
    border-radius: 3px;
  }

  .project-name {
    font-size: 14px;
    color: #666;
  }

  .issue-key-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: #0645ad;
    font-weight: 500;
    font-size: 14px;
    text-decoration: none;
  }

  .issue-key-link:hover {
    text-decoration: underline;
  }

  .issue-status {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
  }

  .status-open {
    color: #0e8420;
  }

  .status-closed {
    color: #7c355d;
  }

  .status-unknown {
    color: #888;
  }

  .issue-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #111;
  }

  .labels-row {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 8px;
  }

  .label-chip {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 12px;
    background: #f0f0f0;
    border: 1px solid #ddd;
    color: #555;
  }

  /* Sections */
  .section {
    padding: 16px 24px;
    border-bottom: 1px solid #e0e0e0;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .section-title {
    margin: 0 0 12px;
    font-size: 17px;
    font-weight: 600;
  }

  .section-count {
    font-weight: 400;
    color: #888;
    font-size: 14px;
  }

  .section-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .no-items {
    color: #888;
    font-size: 13px;
    font-style: italic;
  }

  .btn-bulk {
    background: #E95420;
    border: 1px solid #E95420;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
    cursor: pointer;
    color: white;
    font-weight: 500;
  }

  .btn-bulk:hover {
    background: #d4471a;
    border-color: #d4471a;
    color: white;
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

  .filter-badge {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 8px;
    height: 8px;
    background: #E95420;
    border-radius: 50%;
  }

  .results-area {
    display: flex;
    min-height: 200px;
  }

  .results-content {
    flex: 1;
    min-width: 0;
    padding: 0;
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
    color: #E95420;
    font-size: 13px;
    font-weight: 500;
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

  /* States */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60px 0;
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
  }

  .error-state p {
    color: #c7162b;
    font-size: 14px;
  }

  .empty-results {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: #888;
    font-size: 14px;
  }

  /* Action button styled as link */
  button.action-link {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    font-family: inherit;
  }

  /* Dialog styles */
  .bulk-dialog {
    border: none;
    border-radius: 8px;
    padding: 24px;
    min-width: 400px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .bulk-dialog::backdrop {
    background: rgba(0, 0, 0, 0.4);
  }

  .bulk-dialog h3 {
    margin: 0 0 8px;
    font-size: 18px;
    font-weight: 600;
  }

  .dialog-subtitle {
    margin: 0 0 16px;
    font-size: 13px;
    color: #666;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 16px;
  }

  .btn-cancel {
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
    cursor: pointer;
    color: #555;
  }

  .btn-cancel:hover {
    border-color: #999;
  }

  .btn-submit {
    background: #E95420;
    color: white;
    border: 1px solid #E95420;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
    cursor: pointer;
    font-weight: 500;
  }

  .btn-submit:hover:not(:disabled) {
    background: #d4471a;
  }

  .btn-submit:disabled {
    opacity: 0.6;
    cursor: default;
  }

  .btn-danger {
    background: #c7162b;
    border-color: #c7162b;
  }

  .btn-danger:hover:not(:disabled) {
    background: #a01222;
  }
</style>
