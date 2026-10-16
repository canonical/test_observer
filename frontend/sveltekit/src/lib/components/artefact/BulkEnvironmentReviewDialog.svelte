<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Checkbox, Textarea } from '@canonical/svelte-ds-app-launchpad';
  import type {
    ArtefactEnvironment,
    EnvironmentReview,
  } from '$lib/types/artefact-page';
  import type { ArtefactBuildEnvironmentReviewDecision } from '$lib/types/openapi';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    artefactId: number;
    environments: ArtefactEnvironment[];
    environmentReviews: EnvironmentReview[];
    store: ArtefactPageStore;
    onclose: () => void;
  }

  let { artefactId, environments, environmentReviews, store, onclose }: Props =
    $props();

  const NON_DEPRECATED: ArtefactBuildEnvironmentReviewDecision[] = [
    'REJECTED',
    'APPROVED_INCONSISTENT_TEST',
    'APPROVED_CUSTOMER_PREREQUISITE_FAIL',
    'APPROVED_ALL_TESTS_PASS',
  ];

  const DEPRECATED: ArtefactBuildEnvironmentReviewDecision[] = [
    'APPROVED_UNSTABLE_PHYSICAL_INFRA',
    'APPROVED_FAULTY_HARDWARE',
  ];

  const DECISION_LABELS: Record<string, string> = {
    REJECTED: 'Rejected',
    APPROVED_INCONSISTENT_TEST: 'Approved — Inconsistent Test',
    APPROVED_CUSTOMER_PREREQUISITE_FAIL:
      'Approved — Customer Prerequisite Fail',
    APPROVED_ALL_TESTS_PASS: 'Approved — All Tests Pass',
    APPROVED_UNSTABLE_PHYSICAL_INFRA: 'Approved — Unstable Physical Infra',
    APPROVED_FAULTY_HARDWARE: 'Approved — Faulty Hardware',
  };

  let selectedDecisions = $state<ArtefactBuildEnvironmentReviewDecision[]>([]);
  let comment = $state('');
  let submitting = $state(false);

  const visibleDecisions = $derived.by(() => {
    const visible = [...NON_DEPRECATED];
    const existingDecisions = new Set(
      environmentReviews.flatMap((r) => r.review_decision),
    );
    for (const d of DEPRECATED) {
      if (existingDecisions.has(d)) visible.push(d);
    }
    return visible;
  });

  function toggleDecision(decision: ArtefactBuildEnvironmentReviewDecision) {
    if (selectedDecisions.includes(decision)) {
      selectedDecisions = selectedDecisions.filter((d) => d !== decision);
    } else if (decision === 'REJECTED') {
      selectedDecisions = ['REJECTED'];
    } else {
      selectedDecisions = [
        ...selectedDecisions.filter((d) => d !== 'REJECTED'),
        decision,
      ];
    }
  }

  async function handleSubmit() {
    submitting = true;
    const reviews = environmentReviews.map((r) => ({
      id: r.id,
      review_decision: selectedDecisions,
      review_comment: comment,
    }));
    try {
      await store.bulkUpdateEnvironmentReviews(artefactId, reviews);
      store.deselectAll();
      onclose();
    } catch {
      // The API client reports request failures through the global error UI.
    } finally {
      submitting = false;
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) onclose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onclose();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="overlay" role="none" onclick={handleBackdropClick}>
  <div
    class="dialog"
    role="dialog"
    aria-modal="true"
    aria-label="Bulk Environment Review"
  >
    <h3>Bulk Environment Review</h3>
    <p class="subtitle">
      Applying review to {environments.length} environment{environments.length !==
      1
        ? 's'
        : ''}:
    </p>

    <div class="env-list">
      {#each environments as env (env.key)}
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
          <Checkbox
            checked={selectedDecisions.includes(decision)}
            onchange={() => toggleDecision(decision)}
          />
          <span>{DECISION_LABELS[decision] ?? decision}</span>
        </label>
      {/each}
    </div>

    <label class="comment-label">
      Additional review comment:
      <Textarea
        bind:value={comment}
        placeholder="Optional comment applied to all selected environments…"
      />
    </label>

    <div class="actions">
      <button class="btn-cancel" onclick={onclose}>Cancel</button>
      <button class="btn-submit" onclick={handleSubmit} disabled={submitting}>
        {submitting ? 'Submitting…' : 'Submit Reviews'}
      </button>
    </div>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .dialog {
    background: var(--lp-color-background-default);
    color: var(--lp-color-text-default);
    border: 1px solid var(--lp-color-border-default);
    border-radius: 8px;
    padding: 24px;
    max-width: 480px;
    width: 100%;
    max-height: 80vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .subtitle {
    margin: 0;
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }

  .env-list {
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    max-height: 160px;
    overflow-y: auto;
  }

  .env-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    font-size: 0.8rem;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
  }

  .env-item:last-child {
    border-bottom: none;
  }

  .env-name {
    font-weight: 500;
  }

  .env-arch {
    color: var(--lp-color-text-muted);
  }

  .section-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .decisions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .decision-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .comment-label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .btn-cancel,
  .btn-submit {
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

  .btn-submit {
    background: var(--lp-color-brand-default);
    color: #fff;
  }

  .btn-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
