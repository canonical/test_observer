<script lang="ts">
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import type { EnvironmentIssue } from '$lib/types/artefact-page';
  import { userStore } from '$lib/stores/user.svelte';

  interface Props {
    environmentName: string;
    store: ArtefactPageStore;
  }

  let { environmentName, store }: Props = $props();

  const issues = $derived(
    store.environmentIssues.filter((i) => i.environment_name === environmentName),
  );

  let open = $state(false);

  // Auto-expand if issues exist
  $effect(() => {
    if (issues.length > 0) open = true;
  });

  // Dialog state
  let dialogEl: HTMLDialogElement | undefined = $state();
  let editingIssue = $state<EnvironmentIssue | null>(null);
  let formDescription = $state('');
  let formUrl = $state('');
  let formConfirmed = $state(false);
  let saving = $state(false);

  function openAddDialog() {
    editingIssue = null;
    formDescription = '';
    formUrl = '';
    formConfirmed = false;
    dialogEl?.showModal();
  }

  function openEditDialog(issue: EnvironmentIssue) {
    editingIssue = issue;
    formDescription = issue.description;
    formUrl = issue.url ?? '';
    formConfirmed = issue.is_confirmed;
    dialogEl?.showModal();
  }

  async function handleSubmit() {
    saving = true;
    if (editingIssue) {
      await store.updateEnvironmentIssue(editingIssue.id, {
        environment_name: environmentName,
        description: formDescription,
        url: formUrl || null,
        is_confirmed: formConfirmed,
      });
    } else {
      await store.createEnvironmentIssue({
        environment_name: environmentName,
        description: formDescription,
        url: formUrl || null,
        is_confirmed: formConfirmed,
      });
    }
    saving = false;
    dialogEl?.close();
  }

  async function handleDelete(issue: EnvironmentIssue) {
    if (confirm(`Delete environment issue "${issue.description}"?`)) {
      await store.deleteEnvironmentIssue(issue.id);
    }
  }
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="env-issues-title">
      Reported Environment Issues ({issues.length})
    </span>
    {#if userStore.isLoggedIn}
      <button
        class="add-btn"
        onclick={(e) => { e.stopPropagation(); e.preventDefault(); openAddDialog(); }}
        title="Add environment issue"
      >
        <span class="material-symbols-outlined" style="font-size:18px">add</span>
      </button>
    {/if}
  {/snippet}

  {#if issues.length === 0}
    <p class="no-issues">No environment issues reported.</p>
  {:else}
    <div class="issues-list">
      {#each issues as issue (issue.id)}
        <div class="issue-row">
          <span class="issue-description">{issue.description}</span>
          {#if issue.url}
            <a href={issue.url} target="_blank" rel="noopener" class="issue-link">
              <span class="material-symbols-outlined" style="font-size:16px">open_in_new</span>
            </a>
          {/if}
          <span class="confirmed-badge" class:confirmed={issue.is_confirmed}>
            {issue.is_confirmed ? 'Confirmed' : 'Unconfirmed'}
          </span>
          {#if userStore.isLoggedIn}
            <button class="icon-btn" onclick={() => openEditDialog(issue)} title="Edit">
              <span class="material-symbols-outlined" style="font-size:16px">edit</span>
            </button>
            <button class="icon-btn danger" onclick={() => handleDelete(issue)} title="Delete">
              <span class="material-symbols-outlined" style="font-size:16px">delete</span>
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</Expandable>

<!-- Add / Edit dialog -->
<dialog bind:this={dialogEl}>
  <form method="dialog" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
    <h3>{editingIssue ? 'Edit' : 'Add'} Environment Issue</h3>
    <label class="field">
      Description
      <input type="text" bind:value={formDescription} required />
    </label>
    <label class="field">
      URL (optional)
      <input type="url" bind:value={formUrl} placeholder="https://..." />
    </label>
    <label class="checkbox-field">
      <input type="checkbox" bind:checked={formConfirmed} />
      Confirmed
    </label>
    <div class="dialog-actions">
      <button type="button" class="cancel-btn" onclick={() => dialogEl?.close()}>Cancel</button>
      <button type="submit" class="save-btn" disabled={saving || !formDescription.trim()}>
        {saving ? 'Saving...' : 'Save'}
      </button>
    </div>
  </form>
</dialog>

<style>
  .env-issues-title {
    font-size: 13px;
    font-weight: 600;
    color: #555;
  }

  .add-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    color: #555;
    padding: 0;
  }

  .add-btn:hover {
    background: #f0f0f0;
  }

  .no-issues {
    color: #999;
    font-size: 13px;
    margin: 0;
  }

  .issues-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .issue-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    font-size: 13px;
  }

  .issue-description {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .issue-link {
    color: #0066cc;
    display: inline-flex;
  }

  .confirmed-badge {
    font-size: 11px;
    padding: 1px 6px;
    border-radius: 8px;
    background: #eee;
    color: #666;
    white-space: nowrap;
  }

  .confirmed-badge.confirmed {
    background: #dcf5e0;
    color: #0E8420;
  }

  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: none;
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    color: #666;
    padding: 0;
  }

  .icon-btn:hover {
    background: #f0f0f0;
  }

  .icon-btn.danger:hover {
    color: #C7162B;
    background: #fde8e8;
  }

  dialog {
    border: none;
    border-radius: 8px;
    padding: 24px;
    width: 440px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }

  dialog::backdrop {
    background: rgba(0, 0, 0, 0.3);
  }

  dialog h3 {
    margin: 0 0 16px;
    font-size: 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 12px;
    font-size: 13px;
    font-weight: 500;
  }

  .field input {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
  }

  .field input:focus {
    outline: none;
    border-color: #E95420;
  }

  .checkbox-field {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    margin-bottom: 16px;
    cursor: pointer;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  .cancel-btn {
    padding: 6px 14px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
  }

  .save-btn {
    padding: 6px 14px;
    border: none;
    border-radius: 4px;
    background: #E95420;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    font-family: inherit;
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
