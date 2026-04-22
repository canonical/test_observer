<script lang="ts">
  import type { ArtefactEnvironment, EnvironmentReview } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    artefactId: number;
    environments: ArtefactEnvironment[];
    environmentReviews: EnvironmentReview[];
    store: ArtefactPageStore;
    onclose: () => void;
  }

  let { artefactId, environments, environmentReviews, store, onclose }: Props = $props();

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

  let selectedDecisions = $state<string[]>([]);
  let comment = $state('');
  let submitting = $state(false);

  // Show deprecated decisions only if any selected environment already has them
  const visibleDecisions = $derived.by(() => {
    const visible = [...NON_DEPRECATED];
    const existingDecisions = new Set(environmentReviews.flatMap((r) => r.review_decision));
    for (const d of DEPRECATED) {
      if (existingDecisions.has(d)) visible.push(d);
    }
    return visible;
  });

  function toggleDecision(decision: string) {
    const isRejected = decision === 'REJECTED';
    if (selectedDecisions.includes(decision)) {
      selectedDecisions = selectedDecisions.filter((d) => d !== decision);
    } else {
      if (isRejected) {
        selectedDecisions = ['REJECTED'];
      } else {
        selectedDecisions = [...selectedDecisions.filter((d) => d !== 'REJECTED'), decision];
      }
    }
  }

  async function handleSubmit() {
    submitting = true;
    const reviews = environmentReviews.map((r) => ({
      id: r.id,
      review_decision: selectedDecisions,
      review_comment: comment,
    }));
    await store.bulkUpdateEnvironmentReviews(artefactId, reviews);
    submitting = false;
    store.deselectAll();
    onclose();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) onclose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onclose();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div class="overlay" onclick={handleBackdropClick}>
  <div class="dialog" role="dialog" aria-modal="true" aria-label="Bulk Environment Review">
    <h3>Bulk Environment Review</h3>
    <p class="subtitle">Applying review to {environments.length} environment{environments.length !== 1 ? 's' : ''}:</p>

    <div class="env-list">
      {#each environments as env (env.review.id)}
        <div class="env-item">
          <span class="env-name">{env.name}</span>
          <span class="env-arch">{env.architecture}</span>
        </div>
      {/each}
    </div>

    <div class="section-label">Select review status:</div>
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
      Additional review comment:
      <textarea
        bind:value={comment}
        rows="3"
        placeholder="Optional comment applied to all selected environments..."
      ></textarea>
    </label>

    <div class="actions">
      <button class="cancel-btn" onclick={onclose} disabled={submitting}>Cancel</button>
      <button class="submit-btn" onclick={handleSubmit} disabled={submitting}>
        {submitting ? 'Submitting...' : 'Submit Reviews'}
      </button>
    </div>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .dialog {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    max-width: 480px;
    width: 100%;
    max-height: 80vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .subtitle {
    margin: 0;
    font-size: 14px;
    color: #333;
  }

  .env-list {
    border: 1px solid #ddd;
    border-radius: 8px;
    max-height: 160px;
    overflow-y: auto;
  }

  .env-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    font-size: 13px;
    border-bottom: 1px solid #f0f0f0;
  }

  .env-item:last-child {
    border-bottom: none;
  }

  .env-name {
    font-weight: 500;
  }

  .env-arch {
    color: #666;
    font-size: 12px;
  }

  .section-label {
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

  .decision-row input {
    cursor: pointer;
  }

  .comment-label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
  }

  textarea {
    resize: vertical;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    font-family: inherit;
  }

  textarea:focus {
    outline: none;
    border-color: #E95420;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding-top: 4px;
  }

  .cancel-btn {
    padding: 8px 16px;
    border: 1px solid #ccc;
    border-radius: 6px;
    background: #fff;
    font-size: 13px;
    font-family: inherit;
    cursor: pointer;
  }

  .cancel-btn:hover:not(:disabled) {
    background: #f5f5f5;
  }

  .submit-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    background: #E95420;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
  }

  .submit-btn:hover:not(:disabled) {
    background: #c74516;
  }

  .submit-btn:disabled,
  .cancel-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
