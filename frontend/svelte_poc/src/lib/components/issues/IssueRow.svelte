<script lang="ts">
  import { base } from '$app/paths';
  import type { MinimalIssue } from '$lib/types/test-results';
  import { issueDisplayKey } from '$lib/types/issues';

  interface Props {
    issue: MinimalIssue;
  }

  let { issue }: Props = $props();

  const displayKey = $derived(issueDisplayKey(issue));

  const statusClass = $derived(
    issue.status === 'open' ? 'status-open' : issue.status === 'closed' ? 'status-closed' : 'status-unknown',
  );

  const execCount = $derived(issue.test_executions_count ?? 0);
  const execLabel = $derived(
    execCount === 1 ? '1 test execution' : `${execCount} test executions`,
  );
</script>

<a class="issue-row" href="{base}/issues/{issue.id}">
  <div class="row-line1">
    <span class="issue-key">{displayKey}</span>
    <span class="issue-status {statusClass}">
      {#if issue.status === 'open'}
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
        Open
      {:else if issue.status === 'closed'}
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/></svg>
        Closed
      {:else}
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zm-.25-6.25a.75.75 0 00-1.5 0v3.5a.75.75 0 001.5 0v-3.5z"/></svg>
        Unknown
      {/if}
    </span>
    {#if execCount > 0}
      <span class="exec-count">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        {execLabel}
      </span>
    {/if}
    <button
      class="external-link"
      title="Open in {issue.source}"
      onclick={(e: MouseEvent) => { e.preventDefault(); e.stopPropagation(); window.open(issue.url, '_blank', 'noopener,noreferrer'); }}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
    </button>
  </div>
  <div class="row-line2">
    <span class="issue-title">{issue.title || '[No title]'}</span>
  </div>
</a>

<style>
  .issue-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 4px;
    border-bottom: 1px solid #f0f0f0;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
  }

  .issue-row:hover {
    background: #fafafa;
  }

  .row-line1 {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .row-line2 {
    padding-left: 0;
  }

  .issue-key {
    color: #0645ad;
    font-weight: 500;
    font-size: 13px;
    white-space: nowrap;
  }

  .issue-status {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
    font-size: 12px;
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
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
    color: #E95420;
  }

  .external-link {
    flex-shrink: 0;
    color: #888;
    display: flex;
    align-items: center;
    padding: 2px;
    background: none;
    border: none;
    cursor: pointer;
  }

  .external-link:hover {
    color: #E95420;
  }

  .exec-count {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    color: #888;
    white-space: nowrap;
  }
</style>
