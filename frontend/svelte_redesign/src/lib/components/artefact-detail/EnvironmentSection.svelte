<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import ExpandableSection from "./ExpandableSection.svelte";
  import TestExecutionRow from "./TestExecutionRow.svelte";
  import ReviewForm from "./ReviewForm.svelte";
  import type { TestExecution } from "$lib/types/test-execution.js";
  import type { EnvironmentReview, EnvironmentReviewDecision, Environment } from "$lib/types/environment.js";
  import type { User } from "$lib/types/user.js";
  import { TestStatusChip } from "$lib/components/common/index.js";
  import { patchEnvironmentReview } from "$lib/api/artefacts.js";

  interface Props {
    environment: Environment;
    review: EnvironmentReview | undefined;
    executions: TestExecution[];
    artefactId: number;
    activeTestExecutionId?: number;
    selected?: boolean;
    onselect?: (environmentId: number, selected: boolean) => void;
  }

  const {
    environment,
    review,
    executions,
    artefactId,
    activeTestExecutionId,
    selected = false,
    onselect,
  }: Props = $props();

  let showReviewForm = $state(false);
  let reviewSubmitting = $state(false);

  const latestExecution = $derived(executions.length > 0 ? executions[0] : undefined);

  const reviewers = $derived<User[]>(review?.reviewers ?? []);

  const executionsByPlan = $derived(() => {
    const groups = new Map<string, TestExecution[]>();
    for (const exec of executions) {
      const plan = exec.testPlan || "Unknown";
      const list = groups.get(plan) ?? [];
      list.push(exec);
      groups.set(plan, list);
    }
    return groups;
  });

  function handleCheckboxChange(event: Event) {
    const target = event.target as HTMLInputElement;
    onselect?.(environment.id, target.checked);
  }

  async function handleReviewSubmit(decisions: EnvironmentReviewDecision[], comment: string) {
    if (!review) return;
    reviewSubmitting = true;
    try {
      await patchEnvironmentReview(artefactId, review.id, {
        reviewDecision: decisions,
        reviewComment: comment,
      });
      showReviewForm = false;
    } finally {
      reviewSubmitting = false;
    }
  }
</script>

{#snippet header()}
  <div class="ds environment-section__header-content">
    <input
      type="checkbox"
      checked={selected}
      onchange={handleCheckboxChange}
      aria-label="Select environment {environment.name} for bulk review"
      onclick={(e: MouseEvent) => e.stopPropagation()}
    />
    {#if latestExecution}
      <TestStatusChip status={latestExecution.status} />
    {/if}
    <span class="ds environment-section__arch">{environment.architecture}</span>
    <span class="ds environment-section__name">{environment.name}</span>
    <span class="ds environment-section__spacer"></span>
    {#if reviewers.length > 0}
      <span class="ds environment-section__reviewers">
        {#each reviewers as reviewer (reviewer.id)}
          <span class="ds environment-section__reviewer" title={reviewer.name}>
            {reviewer.name.charAt(0).toUpperCase()}
          </span>
        {/each}
      </span>
    {/if}
    <button
      type="button"
      class="ds environment-section__review-btn"
      onclick={(e: MouseEvent) => { e.stopPropagation(); showReviewForm = !showReviewForm; }}
    >
      Review
    </button>
  </div>
{/snippet}

<div class="ds environment-section">
  <ExpandableSection {header}>
    {#if showReviewForm && review}
      <div class="ds environment-section__review-form">
        <ReviewForm
          decisions={review.reviewDecision}
          comment={review.reviewComment}
          onsubmit={handleReviewSubmit}
          submitting={reviewSubmitting}
        />
      </div>
    {/if}

    {#each [...executionsByPlan().entries()] as [planName, planExecutions] (planName)}
      <div class="ds environment-section__plan">
        <h3 class="ds environment-section__plan-name">{planName}</h3>
        {#each planExecutions as execution (execution.id)}
          <TestExecutionRow
            {execution}
            initialOpen={activeTestExecutionId === execution.id}
          />
        {/each}
      </div>
    {/each}

    {#if executions.length === 0}
      <p class="ds environment-section__empty">No test executions for this environment</p>
    {/if}
  </ExpandableSection>
</div>

<style>
  .ds.environment-section {
    margin-bottom: 0.5rem;
  }

  .ds.environment-section__header-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
  }

  .ds.environment-section__arch {
    font-weight: 500;
    font-size: 0.875rem;
  }

  .ds.environment-section__name {
    font-size: 0.875rem;
    color: var(--color-text-muted, #666);
  }

  .ds.environment-section__spacer {
    flex: 1;
  }

  .ds.environment-section__reviewers {
    display: flex;
    gap: 0.25rem;
  }

  .ds.environment-section__reviewer {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 50%;
    background-color: var(--color-background-alt, #f0f0f0);
    font-size: 0.75rem;
    font-weight: 600;
  }

  .ds.environment-section__review-btn {
    padding: 0.25rem 0.75rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background: var(--color-background, #fff);
    font: inherit;
    font-size: 0.8125rem;
    cursor: pointer;
  }

  .ds.environment-section__review-form {
    margin-bottom: 1rem;
    padding: 0.75rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background-color: var(--color-background-alt, #f7f7f7);
  }

  .ds.environment-section__plan {
    margin-bottom: 0.75rem;
  }

  .ds.environment-section__plan-name {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.375rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.environment-section__empty {
    color: var(--color-text-muted, #666);
    font-size: 0.875rem;
    font-style: italic;
  }
</style>
