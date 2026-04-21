<script lang="ts">
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import StatusIcon from '$lib/components/ui/StatusIcon.svelte';
  import TestResultHistory from './TestResultHistory.svelte';
  import type { TestResult, TestIssue } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import { page } from '$app/state';

  interface Props {
    result: TestResult;
    store: ArtefactPageStore;
    artefactId: number;
    family: string;
  }

  let { result, store, artefactId, family }: Props = $props();

  const targetResultId = $derived(
    page.url.searchParams.get('testResultId'),
  );

  let open = $state(false);

  $effect(() => {
    if (targetResultId && parseInt(targetResultId, 10) === result.id) {
      open = true;
    }
  });

  // Match test issues by template_id or case_name
  const matchedTestIssues = $derived(
    store.testIssues.filter(
      (ti: TestIssue) =>
        (result.template_id && ti.template_id === result.template_id) ||
        (result.name && ti.case_name === result.name),
    ),
  );

  const issueCount = $derived(result.issues.length + matchedTestIssues.length);
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="result-title">
      <span class="result-name">{result.name}</span>
      {#if issueCount > 0}
        <span class="issue-count">({issueCount} issue{issueCount !== 1 ? 's' : ''})</span>
      {/if}
      <span class="spacer"></span>
      <TestResultHistory previousResults={result.previous_results} {family} />
    </span>
  {/snippet}

  <div class="result-details">
    <!-- Legacy test issues -->
    {#if matchedTestIssues.length > 0}
      <div class="section">
        <h5>Reported Test Issues</h5>
        {#each matchedTestIssues as ti (ti.id)}
          <div class="test-issue-row">
            <span class="ti-description">{ti.description}</span>
            {#if ti.url}
              <a href={ti.url} target="_blank" rel="noopener" class="ti-link">
                <span class="material-symbols-outlined" style="font-size:14px">open_in_new</span>
                {ti.url}
              </a>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <!-- Issue attachments -->
    {#if result.issues.length > 0}
      <div class="section">
        <h5>Attached Issues</h5>
        {#each result.issues as attachment (attachment.issue.id)}
          <div class="attachment-row">
            <span class="att-badge" class:open={attachment.issue.status === 'open'} class:closed={attachment.issue.status === 'closed'}>
              {attachment.issue.status}
            </span>
            <a href={attachment.issue.url} target="_blank" rel="noopener" class="att-link">
              [{attachment.issue.source}] {attachment.issue.project} #{attachment.issue.key}
            </a>
            <span class="att-title">{attachment.issue.title}</span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Details -->
    <div class="section">
      {#if result.category}
        <div class="detail-row">
          <span class="detail-label">Category</span>
          <span class="detail-value">{result.category}</span>
        </div>
      {/if}
      {#if result.comment}
        <div class="detail-row">
          <span class="detail-label">Comment</span>
          <span class="detail-value">{result.comment}</span>
        </div>
      {/if}
      {#if result.io_log}
        <div class="detail-row">
          <span class="detail-label">IO Log</span>
          <pre class="io-log">{result.io_log}</pre>
        </div>
      {/if}
    </div>
  </div>
</Expandable>

<style>
  .result-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .result-name {
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .issue-count {
    font-size: 12px;
    color: #C7162B;
    white-space: nowrap;
  }

  .spacer {
    flex: 1;
  }

  .result-details {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  h5 {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .test-issue-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    padding: 4px 0;
  }

  .ti-description {
    color: #333;
  }

  .ti-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: #0066cc;
    font-size: 12px;
    text-decoration: none;
  }

  .ti-link:hover {
    text-decoration: underline;
  }

  .attachment-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    padding: 4px 0;
  }

  .att-badge {
    font-size: 11px;
    padding: 1px 6px;
    border-radius: 8px;
    background: #eee;
    color: #666;
    text-transform: capitalize;
    white-space: nowrap;
  }

  .att-badge.open {
    background: #fff3cd;
    color: #856404;
  }

  .att-badge.closed {
    background: #dcf5e0;
    color: #0E8420;
  }

  .att-link {
    color: #0066cc;
    font-size: 13px;
    text-decoration: none;
    white-space: nowrap;
  }

  .att-link:hover {
    text-decoration: underline;
  }

  .att-title {
    color: #666;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .detail-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 4px 0;
  }

  .detail-label {
    font-size: 12px;
    font-weight: 600;
    color: #555;
  }

  .detail-value {
    font-size: 13px;
    color: #333;
  }

  .io-log {
    margin: 0;
    padding: 8px 12px;
    background: #1a1a2e;
    color: #e0e0e0;
    border-radius: 4px;
    font-size: 12px;
    font-family: 'Ubuntu Mono', monospace;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 400px;
    overflow-y: auto;
  }
</style>
