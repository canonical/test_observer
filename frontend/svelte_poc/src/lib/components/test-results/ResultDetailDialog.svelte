<script lang="ts">
  import { base } from '$app/paths';
  import type { TestResultWithContext } from '$lib/types/test-results';

  interface Props {
    row: TestResultWithContext | null;
    onclose?: () => void;
  }

  let { row, onclose }: Props = $props();

  let dialogEl: HTMLDialogElement | undefined = $state();

  $effect(() => {
    if (row && dialogEl && !dialogEl.open) {
      dialogEl.showModal();
    } else if (!row && dialogEl?.open) {
      dialogEl.close();
    }
  });

  function handleClose() {
    onclose?.();
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleString();
  }

  function metadataEntries(meta: Record<string, string[]>): [string, string][] {
    const entries: [string, string][] = [];
    for (const [key, vals] of Object.entries(meta)) {
      entries.push([key, vals.join(', ')]);
    }
    return entries;
  }
</script>

<dialog bind:this={dialogEl} class="detail-dialog" onclose={handleClose}>
  {#if row}
    <div class="dialog-header">
      <h2>Test Result Details</h2>
      <button class="close-btn" onclick={handleClose} title="Close">&times;</button>
    </div>

    <div class="dialog-body">
      <section class="detail-section">
        <h3>Test Case</h3>
        <dl>
          <dt>Name</dt>
          <dd>{row.test_result.name}</dd>
          {#if row.test_result.category}
            <dt>Category</dt>
            <dd>{row.test_result.category}</dd>
          {/if}
          {#if row.test_result.template_id}
            <dt>Template ID</dt>
            <dd>{row.test_result.template_id}</dd>
          {/if}
          <dt>Status</dt>
          <dd>
            <span
              class="status-badge"
              class:passed={row.test_result.status === 'PASSED'}
              class:failed={row.test_result.status === 'FAILED'}
              class:skipped={row.test_result.status === 'SKIPPED'}
            >
              {row.test_result.status}
            </span>
          </dd>
        </dl>
      </section>

      <section class="detail-section">
        <h3>Artefact</h3>
        <dl>
          <dt>Family</dt>
          <dd>{row.artefact.family}</dd>
          <dt>Name</dt>
          <dd>{row.artefact.name}</dd>
          <dt>Version</dt>
          <dd>{row.artefact.version}</dd>
          <dt>Track</dt>
          <dd>{row.artefact.track || '—'}</dd>
          <dt>Architecture</dt>
          <dd>{row.artefact_build.architecture}</dd>
        </dl>
      </section>

      <section class="detail-section">
        <h3>Test Execution</h3>
        <dl>
          <dt>ID</dt>
          <dd>{row.test_execution.id}</dd>
          <dt>Test Plan</dt>
          <dd>{row.test_execution.test_plan || '—'}</dd>
          <dt>Environment</dt>
          <dd>{row.test_execution.environment.architecture} / {row.test_execution.environment.name}</dd>
          <dt>Status</dt>
          <dd>{row.test_execution.status}</dd>
          <dt>Created</dt>
          <dd>{formatDate(row.test_execution.created_at)}</dd>
          {#each metadataEntries(row.test_execution.execution_metadata) as [key, val]}
            <dt>{key}</dt>
            <dd>{val}</dd>
          {/each}
        </dl>
      </section>

      {#if row.test_result.io_log}
        <section class="detail-section">
          <h3>IO Log</h3>
          <pre class="io-log">{row.test_result.io_log}</pre>
        </section>
      {/if}

      {#if row.test_result.issues && row.test_result.issues.length > 0}
        <section class="detail-section">
          <h3>Issues</h3>
          <div class="issues-list">
            {#each row.test_result.issues as attachment}
              <a
                class="issue-card"
                href="{base}/issues/{attachment.issue.id}"
                onclick={handleClose}
              >
                <span class="issue-key">{attachment.issue.key}</span>
                <span class="issue-title">{attachment.issue.title || '[No title]'}</span>
                <span class="issue-status" class:open={attachment.issue.status === 'open'} class:closed={attachment.issue.status === 'closed'}>
                  {attachment.issue.status}
                </span>
              </a>
            {/each}
          </div>
        </section>
      {/if}
    </div>

    <div class="dialog-footer">
      <a
        class="view-run-link"
        href="{base}/{row.artefact.family}s/{row.artefact.id}"
      >
        View Run
      </a>
      <button class="btn-close" onclick={handleClose}>Close</button>
    </div>
  {/if}
</dialog>

<style>
  .detail-dialog {
    border: none;
    border-radius: 8px;
    padding: 0;
    width: min(900px, 90vw);
    max-height: 85vh;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    display: flex;
    flex-direction: column;
  }

  .detail-dialog::backdrop {
    background: rgba(0, 0, 0, 0.4);
  }

  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: #E95420;
    color: white;
    flex-shrink: 0;
  }

  .dialog-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }

  .close-btn:hover {
    opacity: 0.8;
  }

  .dialog-body {
    padding: 24px;
    overflow-y: auto;
    flex: 1;
  }

  .detail-section {
    margin-bottom: 24px;
  }

  .detail-section:last-child {
    margin-bottom: 0;
  }

  .detail-section h3 {
    margin: 0 0 12px;
    font-size: 14px;
    font-weight: 600;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 6px;
  }

  dl {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 4px 12px;
    margin: 0;
    font-size: 13px;
  }

  dt {
    color: #666;
    font-weight: 500;
  }

  dd {
    margin: 0;
    color: #333;
    word-break: break-word;
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

  .io-log {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 16px;
    border-radius: 4px;
    font-family: 'Ubuntu Mono', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.5;
    overflow-x: auto;
    max-height: 300px;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
  }

  .dialog-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid #e0e0e0;
    flex-shrink: 0;
  }

  .view-run-link {
    color: #E95420;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
  }

  .view-run-link:hover {
    text-decoration: underline;
  }

  .btn-close {
    background: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px 20px;
    font-size: 13px;
    cursor: pointer;
    color: #333;
  }

  .btn-close:hover {
    background: #e0e0e0;
  }

  .issues-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .issue-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    text-decoration: none;
    color: inherit;
    transition: background 0.15s;
  }

  .issue-card:hover {
    background: #f5f5f5;
  }

  .issue-card .issue-key {
    font-weight: 600;
    font-size: 13px;
    color: #0645ad;
    white-space: nowrap;
  }

  .issue-card .issue-title {
    flex: 1;
    font-size: 13px;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .issue-card .issue-status {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    white-space: nowrap;
    color: #888;
  }

  .issue-card .issue-status.open {
    color: #0e8420;
  }

  .issue-card .issue-status.closed {
    color: #7c355d;
  }
</style>
