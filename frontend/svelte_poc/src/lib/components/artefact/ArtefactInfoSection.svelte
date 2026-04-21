<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    artefact: Artefact;
    family: Family;
    store: ArtefactPageStore;
  }

  let { artefact, family, store }: Props = $props();

  let editingComment = $state(false);
  let commentDraft = $state('');

  function startEditComment() {
    commentDraft = artefact.comment ?? '';
    editingComment = true;
  }

  async function saveComment() {
    editingComment = false;
    if (commentDraft !== artefact.comment) {
      await store.updateArtefactComment(artefact.id, commentDraft);
    }
  }

  function handleCommentKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      saveComment();
    }
    if (e.key === 'Escape') {
      editingComment = false;
    }
  }

  interface InfoRow {
    label: string;
    value: string;
    show: boolean;
  }

  const infoRows = $derived<InfoRow[]>([
    { label: 'track', value: artefact.track, show: family === 'snaps' || family === 'charms' },
    { label: 'series', value: artefact.series, show: family === 'debs' },
    { label: 'repo', value: artefact.repo, show: family === 'debs' },
    { label: 'store', value: artefact.store, show: family === 'snaps' },
    { label: 'branch', value: artefact.branch, show: !!artefact.branch },
    { label: 'source', value: artefact.source, show: !!artefact.source },
    { label: 'os', value: artefact.os, show: family === 'images' },
    { label: 'release', value: artefact.release, show: family === 'images' },
    { label: 'owner', value: artefact.owner, show: family === 'images' },
  ].filter((r) => r.show));
</script>

<section class="info-section">
  <div class="info-list">
    {#each infoRows as row (row.label)}
      <div class="info-row">{row.label}: {row.value}</div>
    {/each}
  </div>

  {#if artefact.bug_link}
    <div class="info-row">
      bug link: <a href={artefact.bug_link} target="_blank" rel="noopener noreferrer" class="bug-link">{artefact.bug_link}</a>
    </div>
  {/if}

  <div class="comment-section">
    <div class="comment-header">
      <span class="info-label">comment:</span>
      {#if !editingComment}
        <button class="edit-icon" onclick={startEditComment} title="Edit comment">
          <span class="material-symbols-outlined" style="font-size: 16px">edit</span>
        </button>
      {/if}
    </div>
    {#if editingComment}
      <textarea
        class="comment-input"
        bind:value={commentDraft}
        onkeydown={handleCommentKeydown}
        onblur={saveComment}
        rows="3"
      ></textarea>
      <span class="hint">Press Enter to save, Esc to cancel</span>
    {:else}
      <button class="comment-display" onclick={startEditComment} title="Click to edit">
        {#if artefact.comment}
          {artefact.comment}
        {:else}
          <span class="placeholder">Add a comment...</span>
        {/if}
      </button>
    {/if}
  </div>
</section>

<style>
  .info-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-title {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .info-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 14px;
    color: #333;
  }

  .info-row {
    line-height: 1.4;
  }

  .info-label {
    color: #333;
    font-size: 14px;
  }

  .comment-header {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .edit-icon {
    all: unset;
    cursor: pointer;
    color: #757575;
    display: flex;
    align-items: center;
  }

  .edit-icon:hover {
    color: #333;
  }

  .bug-link-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .bug-link {
    color: #E95420;
    font-size: 13px;
    word-break: break-all;
  }

  .bug-link:hover {
    text-decoration: underline;
  }

  .comment-section {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .comment-display {
    all: unset;
    font-size: 14px;
    color: #333;
    cursor: pointer;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #e0e0e0;
    min-height: 48px;
    word-break: break-word;
    background: #fafafa;
    display: block;
    width: 100%;
    box-sizing: border-box;
  }

  .comment-display:hover {
    border-color: #ccc;
    background: #fafafa;
  }

  .placeholder {
    color: #999;
    font-style: italic;
  }

  .comment-input {
    padding: 6px 8px;
    border: 1px solid #E95420;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
    resize: vertical;
    outline: none;
  }

  .hint {
    font-size: 11px;
    color: #999;
  }
</style>
