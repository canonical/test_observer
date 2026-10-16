<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Chip, Link } from "@canonical/svelte-ds-app-launchpad";
  import Expandable from "./Expandable.svelte";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import type { EnvironmentIssue } from "$lib/types/artefact-page";
  import { userStore } from "$lib/stores/user.svelte";

  interface Props {
    environmentName: string;
    store: ArtefactPageStore;
  }

  let { environmentName, store }: Props = $props();

  const issues = $derived(
    store.environmentIssues.filter(
      (i) => i.environment_name === environmentName,
    ),
  );

  let open = $state(false);

  $effect(() => {
    if (issues.length > 0) open = true;
  });

  let dialogEl: HTMLDialogElement | undefined = $state();
  let editingIssue = $state<EnvironmentIssue | null>(null);
  let formDescription = $state("");
  let formUrl = $state("");
  let formConfirmed = $state(false);
  let saving = $state(false);
  const canMutate = $derived(
    userStore.isLoggedIn &&
      userStore.hasPermission("change_environment_reported_issue"),
  );

  function openAddDialog() {
    editingIssue = null;
    formDescription = "";
    formUrl = "";
    formConfirmed = false;
    dialogEl?.showModal();
  }

  function openEditDialog(issue: EnvironmentIssue) {
    editingIssue = issue;
    formDescription = issue.description;
    formUrl = issue.url ?? "";
    formConfirmed = issue.is_confirmed;
    dialogEl?.showModal();
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    saving = true;
    try {
      if (editingIssue) {
        await store.updateEnvironmentIssue(editingIssue.id, {
          environment_name: environmentName,
          description: formDescription,
          url: formUrl.trim() || null,
          is_confirmed: formConfirmed,
        });
      } else {
        await store.createEnvironmentIssue({
          environment_name: environmentName,
          description: formDescription,
          url: formUrl.trim() || null,
          is_confirmed: formConfirmed,
        });
      }
      dialogEl?.close();
    } catch {
      // The API client reports request failures through the global error UI.
    } finally {
      saving = false;
    }
  }

  async function handleDelete(issue: EnvironmentIssue) {
    if (confirm(`Delete environment issue "${issue.description}"?`)) {
      try {
        await store.deleteEnvironmentIssue(issue.id);
      } catch {
        // The API client reports request failures through the global error UI.
      }
    }
  }
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="section-title">
      Reported Environment Issues ({issues.length})
    </span>
    <span role="none" onclick={(e) => e.stopPropagation()}>
      {#if canMutate}
        <button
          class="add-btn"
          onclick={() => openAddDialog()}
          title="Add environment issue">+ add</button
        >
      {/if}
    </span>
  {/snippet}

  {#if issues.length === 0}
    <p class="empty">No environment issues reported.</p>
  {:else}
    <div class="issues-list">
      {#each issues as issue (issue.id)}
        <div class="issue-row">
          <span class="issue-description">{issue.description}</span>
          {#if issue.url}
            <span role="none" onclick={(e) => e.stopPropagation()}>
              <Link href={issue.url}>URL</Link>
            </span>
          {/if}
          <Chip
            value={issue.is_confirmed ? "confirmed" : "unconfirmed"}
            severity={issue.is_confirmed ? "positive" : "caution"}
            readonly
            density="dense"
          />
          {#if canMutate}
            <span
              class="actions"
              role="none"
              onclick={(e) => e.stopPropagation()}
            >
              <button class="text-btn" onclick={() => openEditDialog(issue)}
                >edit</button
              >
            </span>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</Expandable>

<dialog bind:this={dialogEl} class="issue-dialog">
  <form onsubmit={handleSubmit}>
    <h3>{editingIssue ? "Edit" : "Add"} Environment Issue</h3>
    <label class="field">
      <span class="field-label">Description</span>
      <input
        class="field-input"
        bind:value={formDescription}
        placeholder="Issue description…"
        required
      />
    </label>
    <label class="field">
      <span class="field-label"
        >URL {formConfirmed ? "(required)" : "(optional)"}</span
      >
      <input
        class="field-input"
        bind:value={formUrl}
        placeholder="https://…"
        type="url"
        required={formConfirmed}
      />
    </label>
    <label class="checkbox-field">
      <input type="checkbox" bind:checked={formConfirmed} />
      Confirmed
    </label>
    <div class="dialog-actions">
      <button type="button" class="btn-cancel" onclick={() => dialogEl?.close()}
        >Cancel</button
      >
      {#if editingIssue}
        <button
          type="button"
          class="btn-delete"
          onclick={() => {
            const issue = editingIssue;
            if (!issue) return;
            dialogEl?.close();
            handleDelete(issue);
          }}>Delete</button
        >
      {/if}
      <button type="submit" class="btn-save" disabled={saving}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  </form>
</dialog>

<style>
  .section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .add-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.75rem;
    color: var(--lp-color-brand-default);
    font-family: inherit;
    padding: 0 4px;
    color: inherit;
  }

  .add-btn:hover {
    text-decoration: underline;
  }

  .empty {
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
    margin: 0;
  }

  .issues-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .issue-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    padding: 4px 8px;
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    background: var(--lp-color-background-alt);
  }

  .issue-description {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--lp-color-text-default);
  }

  .actions {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
  }

  .text-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.75rem;
    color: var(--lp-color-brand-default);
    font-family: inherit;
    padding: 0;
  }

  .text-btn:hover {
    text-decoration: underline;
  }

  /* Dialog */
  .issue-dialog {
    border: 1px solid var(--lp-color-border-default);
    border-radius: 8px;
    padding: 24px;
    background: var(--lp-color-background-default);
    color: var(--lp-color-text-default);
    min-width: 320px;
    max-width: 480px;
    width: 90vw;
  }

  .issue-dialog::backdrop {
    background: rgba(0, 0, 0, 0.5);
  }

  .issue-dialog h3 {
    margin: 0 0 16px;
    font-size: 1rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 12px;
  }

  .field-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-muted);
  }

  .field-input {
    padding: 6px 10px;
    border: 1px solid var(--lp-color-border-default);
    border-radius: 4px;
    font-size: 0.875rem;
    background: var(--lp-color-background-alt);
    color: var(--lp-color-text-default);
    font-family: inherit;
  }

  .checkbox-field {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    margin-bottom: 16px;
    cursor: pointer;
  }

  .dialog-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .btn-cancel,
  .btn-save,
  .btn-delete {
    padding: 6px 16px;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    font-family: inherit;
    border: 1px solid transparent;
  }

  .btn-cancel {
    background: var(--lp-color-background-alt);
    border-color: var(--lp-color-border-default);
    color: var(--lp-color-text-default);
  }

  .btn-save {
    background: var(--lp-color-brand-default);
    color: #fff;
  }

  .btn-save:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-delete {
    background: none;
    color: #c7162b;
    border-color: #c7162b;
  }
</style>
