<script lang="ts">
  import type { ArtefactEnvironment } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import BulkEnvironmentReviewDialog from './BulkEnvironmentReviewDialog.svelte';

  interface Props {
    environments: ArtefactEnvironment[];
    artefactId: number;
    store: ArtefactPageStore;
  }

  let { environments, artefactId, store }: Props = $props();

  let dialogOpen = $state(false);

  const selectedCount = $derived(store.selectedEnvironmentIds.size);
  const totalCount = $derived(environments.length);

  const selectedEnvironments = $derived(
    environments.filter((env) => store.isSelected(env.review.id)),
  );

  function handleSelectAll() {
    store.selectAll(environments.map((env) => env.review.id));
  }

  function handleDeselectAll() {
    store.deselectAll();
  }
</script>

<div class="bulk-controls">
  <span class="selection-count">{selectedCount} of {totalCount} selected</span>
  <button class="text-action" onclick={handleSelectAll}>Select All</button>
  <button class="text-action" onclick={handleDeselectAll}>Deselect All</button>
  <button
    class="review-btn"
    disabled={selectedCount === 0}
    onclick={() => (dialogOpen = true)}
  >
    Review {selectedCount} environment{selectedCount !== 1 ? 's' : ''}
  </button>
</div>

{#if dialogOpen}
  <BulkEnvironmentReviewDialog
    {artefactId}
    environments={selectedEnvironments}
    environmentReviews={selectedEnvironments.map((e) => e.review)}
    {store}
    onclose={() => (dialogOpen = false)}
  />
{/if}

<style>
  .bulk-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    flex-wrap: wrap;
  }

  .selection-count {
    font-size: 13px;
    color: #666;
    white-space: nowrap;
  }

  .text-action {
    all: unset;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    color: #E95420;
    white-space: nowrap;
  }

  .text-action:hover {
    text-decoration: underline;
  }

  .review-btn {
    padding: 6px 16px;
    border: none;
    border-radius: 6px;
    background: #E95420;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    white-space: nowrap;
  }

  .review-btn:hover:not(:disabled) {
    background: #c74516;
  }

  .review-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
