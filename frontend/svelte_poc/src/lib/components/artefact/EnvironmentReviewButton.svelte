<script lang="ts">
  import type { EnvironmentReview } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import { userStore } from '$lib/stores/user.svelte';

  interface Props {
    review: EnvironmentReview;
    store: ArtefactPageStore;
    artefactId: number;
  }

  let { review, store, artefactId }: Props = $props();

  const NON_DEPRECATED: string[] = [
    'REJECTED',
    'APPROVED_INCONSISTENT_TEST',
    'APPROVED_CUSTOMER_PREREQUISITE_FAIL',
    'APPROVED_ALL_TESTS_PASS',
  ];

  const DEPRECATED: string[] = [
    'APPROVED_UNSTABLE_PHYSICAL_INFRA',
    'APPROVED_FAULTY_HARDWARE',
  ];

  const DECISION_LABELS: Record<string, string> = {
    REJECTED: 'Rejected',
    APPROVED_INCONSISTENT_TEST: 'Approved — Inconsistent Test',
    APPROVED_CUSTOMER_PREREQUISITE_FAIL: 'Approved — Customer Prerequisite Fail',
    APPROVED_ALL_TESTS_PASS: 'Approved — All Tests Pass',
    APPROVED_UNSTABLE_PHYSICAL_INFRA: 'Approved — Unstable Physical Infra',
    APPROVED_FAULTY_HARDWARE: 'Approved — Faulty Hardware',
  };

  let popoverOpen = $state(false);
  let selectedDecisions = $state<string[]>([]);
  let comment = $state('');
  let submitting = $state(false);
  let popoverEl: HTMLDivElement | undefined = $state();

  // Sync when review changes externally
  $effect(() => {
    selectedDecisions = [...review.review_decision];
    comment = review.review_comment;
  });

  const chipLabel = $derived.by(() => {
    if (review.review_decision.length === 0) return 'Undecided';
    if (review.review_decision.includes('REJECTED')) return 'Rejected';
    return 'Approved';
  });

  const chipColor = $derived.by(() => {
    if (review.review_decision.length === 0) return '#666';
    if (review.review_decision.includes('REJECTED')) return '#C7162B';
    return '#0E8420';
  });

  const visibleDecisions = $derived.by(() => {
    const visible = [...NON_DEPRECATED];
    for (const d of DEPRECATED) {
      if (review.review_decision.includes(d)) visible.push(d);
    }
    return visible;
  });

  function toggleDecision(decision: string) {
    const isRejected = decision === 'REJECTED';
    if (selectedDecisions.includes(decision)) {
      selectedDecisions = selectedDecisions.filter((d) => d !== decision);
    } else {
      if (isRejected) {
        // REJECTED is mutually exclusive with approvals
        selectedDecisions = ['REJECTED'];
      } else {
        // Approvals remove REJECTED
        selectedDecisions = [...selectedDecisions.filter((d) => d !== 'REJECTED'), decision];
      }
    }
  }

  async function submit() {
    submitting = true;
    await store.submitReview(artefactId, review.id, {
      review_decision: selectedDecisions,
      review_comment: comment,
    });
    submitting = false;
    popoverOpen = false;
  }

  function handleClickOutside(e: MouseEvent) {
    if (popoverEl && !popoverEl.contains(e.target as Node)) {
      popoverOpen = false;
    }
  }

  $effect(() => {
    if (popoverOpen) {
      document.addEventListener('click', handleClickOutside, true);
      return () => document.removeEventListener('click', handleClickOutside, true);
    }
  });
</script>

<div class="review-button-wrapper" bind:this={popoverEl}>
  <button
    class="review-chip"
    style="border-color: {chipColor}; color: {chipColor}"
    onclick={(e) => { e.stopPropagation(); popoverOpen = !popoverOpen; }}
    disabled={!userStore.isLoggedIn}
  >
    {chipLabel}
  </button>

  {#if popoverOpen}
    <div class="review-popover">
      <h4>Environment Review</h4>
      <div class="decisions">
        {#each visibleDecisions as decision (decision)}
          <label class="decision-row">
            <input
              type="checkbox"
              checked={selectedDecisions.includes(decision)}
              onchange={() => toggleDecision(decision)}
            />
            <span>{DECISION_LABELS[decision] ?? decision}</span>
          </label>
        {/each}
      </div>
      <label class="comment-label">
        Comment
        <textarea
          bind:value={comment}
          rows="3"
          placeholder="Optional review comment..."
        ></textarea>
      </label>
      <button class="submit-btn" onclick={submit} disabled={submitting}>
        {submitting ? 'Saving...' : 'Submit'}
      </button>
    </div>
  {/if}
</div>

<style>
  .review-button-wrapper {
    position: relative;
    display: inline-block;
  }

  .review-chip {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border: 1.5px solid;
    border-radius: 12px;
    background: #fff;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    font-family: inherit;
  }

  .review-chip:disabled {
    opacity: 0.6;
    cursor: default;
  }

  .review-chip:hover:not(:disabled) {
    opacity: 0.8;
  }

  .review-popover {
    position: absolute;
    top: 100%;
    right: 0;
    z-index: 100;
    width: 340px;
    margin-top: 4px;
    padding: 16px;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
  }

  .decisions {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .decision-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    cursor: pointer;
  }

  .comment-label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
  }

  textarea {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
    resize: vertical;
  }

  textarea:focus {
    outline: none;
    border-color: #E95420;
  }

  .submit-btn {
    align-self: flex-end;
    padding: 6px 16px;
    border: none;
    border-radius: 4px;
    background: #E95420;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
  }

  .submit-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }

  .submit-btn:hover:not(:disabled) {
    background: #c7471a;
  }
</style>
