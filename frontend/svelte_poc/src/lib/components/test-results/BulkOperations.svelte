<script lang="ts">
  import type { TestResultsStore } from '$lib/stores/test-results.svelte';
  import type { TestResultFilters } from '$lib/types/test-results';

  interface Props {
    store: TestResultsStore;
  }

  let { store }: Props = $props();

  // Dialog refs
  let attachDialog = $state<HTMLDialogElement | null>(null);
  let detachDialog = $state<HTMLDialogElement | null>(null);
  let createRerunsDialog = $state<HTMLDialogElement | null>(null);
  let deleteRerunsDialog = $state<HTMLDialogElement | null>(null);
  let attachmentRuleDialog = $state<HTMLDialogElement | null>(null);
  let confirmDialog = $state<HTMLDialogElement | null>(null);

  // Shared state
  let issueUrl = $state('');
  let busy = $state(false);
  let errorMsg = $state('');

  // Rerun options
  let rerunOnlyLatest = $state(false);
  let rerunExcludeArchived = $state(false);

  // Pending action for confirmation
  let pendingAction: (() => Promise<void>) | null = null;

  function buildRerunFilters(): TestResultFilters {
    const filters = { ...store.appliedFilters };
    if (rerunOnlyLatest) filters.executionIsLatest = 'yes';
    if (rerunExcludeArchived) filters.archived = 'no';
    return filters;
  }

  function resetState() {
    issueUrl = '';
    errorMsg = '';
    busy = false;
    rerunOnlyLatest = false;
    rerunExcludeArchived = false;
    pendingAction = null;
  }

  function openDialog(dialog: HTMLDialogElement | null) {
    resetState();
    dialog?.showModal();
  }

  function closeDialog(dialog: HTMLDialogElement | null) {
    dialog?.close();
    resetState();
  }

  function maybeConfirm(action: () => Promise<void>, dialog: HTMLDialogElement | null) {
    if (store.totalCount > 50) {
      pendingAction = async () => {
        confirmDialog?.close();
        await action();
      };
      dialog?.close();
      confirmDialog?.showModal();
    } else {
      action();
    }
  }

  async function handleAttachIssue() {
    if (!issueUrl.trim()) return;
    busy = true;
    errorMsg = '';
    const issueId = await store.getOrCreateIssue(issueUrl.trim());
    if (issueId == null) {
      errorMsg = 'Failed to resolve issue URL';
      busy = false;
      return;
    }
    await store.attachIssue(issueId, store.appliedFilters);
    busy = false;
    closeDialog(attachDialog);
    store.search(store.appliedFilters);
  }

  async function handleDetachIssue() {
    if (!issueUrl.trim()) return;
    busy = true;
    errorMsg = '';
    const issueId = await store.getOrCreateIssue(issueUrl.trim());
    if (issueId == null) {
      errorMsg = 'Failed to resolve issue URL';
      busy = false;
      return;
    }
    await store.detachIssue(issueId, store.appliedFilters);
    busy = false;
    closeDialog(detachDialog);
    store.search(store.appliedFilters);
  }

  async function handleCreateReruns() {
    busy = true;
    errorMsg = '';
    await store.createReruns(buildRerunFilters());
    busy = false;
    closeDialog(createRerunsDialog);
    store.search(store.appliedFilters);
  }

  async function handleDeleteReruns() {
    busy = true;
    errorMsg = '';
    await store.deleteReruns(buildRerunFilters());
    busy = false;
    closeDialog(deleteRerunsDialog);
    store.search(store.appliedFilters);
  }

  async function handleCreateAttachmentRule() {
    if (!issueUrl.trim()) return;
    busy = true;
    errorMsg = '';
    const issueId = await store.getOrCreateIssue(issueUrl.trim());
    if (issueId == null) {
      errorMsg = 'Failed to resolve issue URL';
      busy = false;
      return;
    }
    await store.createAttachmentRule(issueId, store.appliedFilters);
    busy = false;
    closeDialog(attachmentRuleDialog);
  }

  function filterSummary(filters: TestResultFilters): string[] {
    const parts: string[] = [];
    if (filters.families.length) parts.push(`Families: ${filters.families.join(', ')}`);
    if (filters.statuses.length) parts.push(`Statuses: ${filters.statuses.join(', ')}`);
    if (filters.environments.length) parts.push(`Environments: ${filters.environments.join(', ')}`);
    if (filters.testCases.length) parts.push(`Test cases: ${filters.testCases.length}`);
    if (filters.artefacts.length) parts.push(`Artefacts: ${filters.artefacts.join(', ')}`);
    if (filters.metadata.length) parts.push(`Metadata filters: ${filters.metadata.length}`);
    if (filters.fromDate) parts.push(`From: ${filters.fromDate}`);
    if (filters.untilDate) parts.push(`Until: ${filters.untilDate}`);
    return parts;
  }
</script>

<div class="bulk-ops-bar">
  <button
    class="bulk-btn"
    disabled={store.filtersModified || !store.hasFilters}
    onclick={() => openDialog(attachmentRuleDialog)}
  >Create Attachment Rule</button>
  <button
    class="bulk-btn"
    disabled={store.filtersModified || !store.hasFilters}
    onclick={() => openDialog(attachDialog)}
  >Attach Issue</button>
  <button
    class="bulk-btn"
    disabled={store.filtersModified || !store.hasFilters}
    onclick={() => openDialog(detachDialog)}
  >Detach Issue</button>
  <button
    class="bulk-btn"
    disabled={store.filtersModified || !store.hasFilters}
    onclick={() => openDialog(createRerunsDialog)}
  >Create Rerun Requests</button>
  <button
    class="bulk-btn"
    disabled={store.filtersModified || !store.hasFilters}
    onclick={() => openDialog(deleteRerunsDialog)}
  >Delete Rerun Requests</button>
</div>

<!-- Attach Issue Dialog -->
<dialog bind:this={attachDialog} class="bulk-dialog">
  <h3>Attach Issue</h3>
  <p class="dialog-subtitle">Attach an issue to {store.totalCount.toLocaleString()} matching test results.</p>
  <label class="dialog-label">
    Issue URL
    <input
      type="url"
      class="dialog-input"
      bind:value={issueUrl}
      placeholder="https://bugs.launchpad.net/..."
    />
  </label>
  {#if errorMsg}
    <p class="dialog-error">{errorMsg}</p>
  {/if}
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(attachDialog)}>Cancel</button>
    <button
      class="btn-submit"
      disabled={busy || !issueUrl.trim()}
      onclick={() => maybeConfirm(handleAttachIssue, attachDialog)}
    >{busy ? 'Working...' : 'Attach'}</button>
  </div>
</dialog>

<!-- Detach Issue Dialog -->
<dialog bind:this={detachDialog} class="bulk-dialog">
  <h3>Detach Issue</h3>
  <p class="dialog-subtitle">Detach an issue from {store.totalCount.toLocaleString()} matching test results.</p>
  <label class="dialog-label">
    Issue URL
    <input
      type="url"
      class="dialog-input"
      bind:value={issueUrl}
      placeholder="https://bugs.launchpad.net/..."
    />
  </label>
  {#if errorMsg}
    <p class="dialog-error">{errorMsg}</p>
  {/if}
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(detachDialog)}>Cancel</button>
    <button
      class="btn-submit"
      disabled={busy || !issueUrl.trim()}
      onclick={() => maybeConfirm(handleDetachIssue, detachDialog)}
    >{busy ? 'Working...' : 'Detach'}</button>
  </div>
</dialog>

<!-- Create Rerun Requests Dialog -->
<dialog bind:this={createRerunsDialog} class="bulk-dialog">
  <h3>Create Rerun Requests</h3>
  <p class="dialog-subtitle">Create rerun requests for {store.totalCount.toLocaleString()} matching test results.</p>
  <label class="dialog-checkbox">
    <input type="checkbox" bind:checked={rerunOnlyLatest} />
    Only latest test executions
  </label>
  <label class="dialog-checkbox">
    <input type="checkbox" bind:checked={rerunExcludeArchived} />
    Exclude archived artefacts
  </label>
  {#if errorMsg}
    <p class="dialog-error">{errorMsg}</p>
  {/if}
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(createRerunsDialog)}>Cancel</button>
    <button
      class="btn-submit"
      disabled={busy}
      onclick={() => maybeConfirm(handleCreateReruns, createRerunsDialog)}
    >{busy ? 'Working...' : 'Create Reruns'}</button>
  </div>
</dialog>

<!-- Delete Rerun Requests Dialog -->
<dialog bind:this={deleteRerunsDialog} class="bulk-dialog">
  <h3>Delete Rerun Requests</h3>
  <p class="dialog-subtitle">Delete rerun requests for {store.totalCount.toLocaleString()} matching test results.</p>
  <label class="dialog-checkbox">
    <input type="checkbox" bind:checked={rerunOnlyLatest} />
    Only latest test executions
  </label>
  <label class="dialog-checkbox">
    <input type="checkbox" bind:checked={rerunExcludeArchived} />
    Exclude archived artefacts
  </label>
  {#if errorMsg}
    <p class="dialog-error">{errorMsg}</p>
  {/if}
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(deleteRerunsDialog)}>Cancel</button>
    <button
      class="btn-submit btn-danger"
      disabled={busy}
      onclick={() => maybeConfirm(handleDeleteReruns, deleteRerunsDialog)}
    >{busy ? 'Working...' : 'Delete Reruns'}</button>
  </div>
</dialog>

<!-- Create Attachment Rule Dialog -->
<dialog bind:this={attachmentRuleDialog} class="bulk-dialog">
  <h3>Create Attachment Rule</h3>
  <p class="dialog-subtitle">Create an automatic attachment rule using the current filters.</p>
  <label class="dialog-label">
    Issue URL
    <input
      type="url"
      class="dialog-input"
      bind:value={issueUrl}
      placeholder="https://bugs.launchpad.net/..."
    />
  </label>
  <div class="filter-summary">
    <h4>Applied Filters</h4>
    {#each filterSummary(store.appliedFilters) as line}
      <p class="filter-line">{line}</p>
    {:else}
      <p class="filter-line muted">No filters applied</p>
    {/each}
  </div>
  {#if errorMsg}
    <p class="dialog-error">{errorMsg}</p>
  {/if}
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => closeDialog(attachmentRuleDialog)}>Cancel</button>
    <button
      class="btn-submit"
      disabled={busy || !issueUrl.trim()}
      onclick={() => handleCreateAttachmentRule()}
    >{busy ? 'Working...' : 'Create Rule'}</button>
  </div>
</dialog>

<!-- Confirmation Dialog -->
<dialog bind:this={confirmDialog} class="bulk-dialog">
  <h3>Confirm Bulk Operation</h3>
  <p class="dialog-subtitle">
    This will affect <strong>{store.totalCount.toLocaleString()}</strong> test results. Are you sure?
  </p>
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={() => { confirmDialog?.close(); pendingAction = null; }}>Cancel</button>
    <button
      class="btn-submit"
      onclick={() => { if (pendingAction) pendingAction(); }}
    >Confirm</button>
  </div>
</dialog>

<style>
  .bulk-ops-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 0;
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 12px;
  }

  .bulk-btn {
    background: #E95420;
    color: white;
    border: none;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 0.15s;
  }

  .bulk-btn:hover:not(:disabled) {
    opacity: 0.85;
  }

  .bulk-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .bulk-dialog {
    border: none;
    border-radius: 8px;
    padding: 24px;
    max-width: 480px;
    width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .bulk-dialog::backdrop {
    background: rgba(0, 0, 0, 0.4);
  }

  .bulk-dialog h3 {
    margin: 0 0 4px;
    font-size: 18px;
    font-weight: 600;
  }

  .dialog-subtitle {
    margin: 0 0 16px;
    font-size: 13px;
    color: #666;
  }

  .dialog-label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: #333;
    margin-bottom: 12px;
  }

  .dialog-input {
    display: block;
    width: 100%;
    margin-top: 4px;
    padding: 8px 10px;
    font-size: 13px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
  }

  .dialog-input:focus {
    outline: none;
    border-color: #E95420;
    box-shadow: 0 0 0 2px rgba(233, 84, 32, 0.15);
  }

  .dialog-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #333;
    margin-bottom: 8px;
    cursor: pointer;
  }

  .dialog-error {
    color: #c7162b;
    font-size: 13px;
    margin: 8px 0;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 20px;
  }

  .btn-cancel {
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px 16px;
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
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
  }

  .btn-submit:hover:not(:disabled) {
    opacity: 0.85;
  }

  .btn-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-danger {
    background: #c7162b;
  }

  .filter-summary {
    background: #f7f7f7;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 8px;
  }

  .filter-summary h4 {
    margin: 0 0 6px;
    font-size: 12px;
    font-weight: 600;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .filter-line {
    margin: 2px 0;
    font-size: 12px;
    color: #444;
  }

  .filter-line.muted {
    color: #999;
    font-style: italic;
  }
</style>
