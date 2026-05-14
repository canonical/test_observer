<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import ReviewForm from "./ReviewForm.svelte";
  import type { EnvironmentReview, EnvironmentReviewDecision, Environment } from "$lib/types/environment.js";
  import { bulkPatchEnvironmentReviews } from "$lib/api/artefacts.js";

  interface Props {
    artefactId: number;
    reviews: EnvironmentReview[];
    selectedEnvironmentIds: Set<number>;
    open: boolean;
    onclose: () => void;
  }

  const { artefactId, reviews, selectedEnvironmentIds, open, onclose }: Props = $props();

  let submitting = $state(false);

  const selectedReviews = $derived(
    reviews.filter((r) => selectedEnvironmentIds.has(r.environment.id)),
  );

  async function handleSubmit(decisions: EnvironmentReviewDecision[], comment: string) {
    submitting = true;
    try {
      const patches = selectedReviews.map((r) => ({
        id: r.id,
        reviewDecision: decisions,
        reviewComment: comment,
      }));
      await bulkPatchEnvironmentReviews(artefactId, patches);
      onclose();
    } finally {
      submitting = false;
    }
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="ds bulk-review-dialog__overlay" role="presentation" onclick={onclose} onkeydown={(e: KeyboardEvent) => { if (e.key === "Escape") onclose(); }}>
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <dialog
      class="ds bulk-review-dialog"
      {open}
      aria-label="Bulk Review {selectedReviews.length} environments"
      onclick={(e: MouseEvent) => e.stopPropagation()}
      onkeydown={(e: KeyboardEvent) => { if (e.key === "Escape") onclose(); }}
    >
      <div class="ds bulk-review-dialog__header">
        <h2>Bulk Review ({selectedReviews.length} environment{selectedReviews.length !== 1 ? "s" : ""})</h2>
        <button type="button" class="ds bulk-review-dialog__close" onclick={onclose} aria-label="Close">
          &#10005;
        </button>
      </div>

      <div class="ds bulk-review-dialog__environments">
        <h3>Selected Environments</h3>
        <ul>
          {#each selectedReviews as review (review.id)}
            <li>{review.environment.name} ({review.artefactBuild.architecture})</li>
          {/each}
        </ul>
      </div>

      <ReviewForm
        decisions={[]}
        comment=""
        onsubmit={handleSubmit}
        {submitting}
      />
    </dialog>
  </div>
{/if}

<style>
  .ds.bulk-review-dialog__overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .ds.bulk-review-dialog {
    background: var(--color-background, #fff);
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.5rem;
    padding: 1.5rem;
    max-width: 500px;
    width: 90vw;
    max-height: 80vh;
    overflow-y: auto;
  }

  .ds.bulk-review-dialog__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .ds.bulk-review-dialog__header h2 {
    margin: 0;
    font-size: 1.125rem;
  }

  .ds.bulk-review-dialog__close {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0.25rem;
    line-height: 1;
  }

  .ds.bulk-review-dialog__environments {
    margin-bottom: 1rem;
  }

  .ds.bulk-review-dialog__environments h3 {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.375rem;
  }

  .ds.bulk-review-dialog__environments ul {
    margin: 0;
    padding-left: 1.25rem;
    font-size: 0.875rem;
  }
</style>
