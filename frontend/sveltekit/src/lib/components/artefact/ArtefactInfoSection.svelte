<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import {
    DescriptionList,
    Textarea,
    Link,
  } from "@canonical/svelte-ds-app-launchpad";
  import { EditIcon } from "@canonical/svelte-icons";
  import type { Artefact } from "$lib/types";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";

  interface Props {
    artefact: Artefact;
    store: ArtefactPageStore;
  }

  let { artefact, store }: Props = $props();

  let editingComment = $state(false);
  let commentDraft = $state("");
  const canChangeArtefact = $derived(store.canChangeArtefact);

  $effect(() => {
    if (!canChangeArtefact) editingComment = false;
  });

  interface InfoRow {
    label: string;
    value: string;
    show: boolean;
  }

  // Rows derived without branching on family in the template — the
  // family-conditional logic lives here in the data, not in the markup.
  const infoRows = $derived<InfoRow[]>(
    [
      { label: "track", value: artefact.track, show: !!artefact.track },
      { label: "store", value: artefact.store, show: !!artefact.store },
      { label: "branch", value: artefact.branch, show: !!artefact.branch },
      { label: "series", value: artefact.series, show: !!artefact.series },
      { label: "repo", value: artefact.repo, show: !!artefact.repo },
      { label: "source", value: artefact.source, show: !!artefact.source },
      { label: "os", value: artefact.os, show: !!artefact.os },
      { label: "release", value: artefact.release, show: !!artefact.release },
      { label: "owner", value: artefact.owner, show: !!artefact.owner },
    ].filter((r) => r.show),
  );

  function startEdit() {
    commentDraft = artefact.comment ?? "";
    editingComment = true;
  }

  async function saveComment() {
    if (!canChangeArtefact || !editingComment) return;
    editingComment = false;
    if (commentDraft !== (artefact.comment ?? "")) {
      try {
        await store.updateArtefactComment(artefact.id, commentDraft);
      } catch {
        // The API client reports request failures through the global error UI.
      }
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void saveComment();
    }
    if (e.key === "Escape") {
      commentDraft = artefact.comment ?? "";
      editingComment = false;
    }
  }
</script>

<section class="info-section">
  {#if infoRows.length > 0}
    <DescriptionList layout="list">
      {#each infoRows as row (row.label)}
        <DescriptionList.Item name={row.label}>{row.value}</DescriptionList.Item
        >
      {/each}
      {#if artefact.bug_link}
        <DescriptionList.Item name="bug link">
          <Link href={artefact.bug_link}>{artefact.bug_link}</Link>
        </DescriptionList.Item>
      {/if}
    </DescriptionList>
  {/if}

  <div class="comment-section">
    <div class="comment-header">
      <span class="label">comment</span>
      {#if canChangeArtefact && !editingComment}
        <button
          class="edit-btn"
          onclick={startEdit}
          title="Edit comment"
          aria-label="Edit comment"
        >
          <EditIcon />
        </button>
      {/if}
    </div>

    {#if editingComment && canChangeArtefact}
      <Textarea
        bind:value={commentDraft}
        onkeydown={handleKeydown}
        onblur={saveComment}
      />
      <span class="hint">Enter to save · Esc to cancel</span>
    {:else}
      {#if canChangeArtefact}
        <button
          class="comment-display"
          onclick={startEdit}
          title="Click to edit"
        >
          {#if artefact.comment}
            {artefact.comment}
          {:else}
            <span class="placeholder">Add a comment…</span>
          {/if}
        </button>
      {:else}
        <div class="comment-display read-only">
          {#if artefact.comment}
            {artefact.comment}
          {:else}
            <span class="placeholder">Add a comment…</span>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</section>

<style>
  .info-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .comment-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .comment-header {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--lp-color-text-muted);
  }

  .edit-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px;
    color: var(--lp-color-text-muted);
    display: flex;
    align-items: center;
  }

  .edit-btn:hover {
    color: var(--lp-color-text-default);
  }

  .comment-display {
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
    font-family: inherit;
    font-size: 0.875rem;
    color: var(--lp-color-text-default);
    padding: 0;
    width: 100%;
  }

  .comment-display.read-only {
    cursor: default;
  }

  .placeholder {
    color: var(--lp-color-text-muted);
    font-style: italic;
  }

  .hint {
    font-size: 0.75rem;
    color: var(--lp-color-text-muted);
  }
</style>
