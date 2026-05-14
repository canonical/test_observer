<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { EnvironmentReviewDecision } from "$lib/types/environment.js";
  import { formatStatus } from "$lib/utils/formatting.js";

  interface Props {
    decisions: EnvironmentReviewDecision[];
    comment: string;
    onsubmit: (decisions: EnvironmentReviewDecision[], comment: string) => void;
    submitting?: boolean;
  }

  const { decisions: initialDecisions, comment: initialComment, onsubmit, submitting = false }: Props = $props();

  const allDecisions: EnvironmentReviewDecision[] = [
    "APPROVED_ALL_TESTS_PASS",
    "APPROVED_INCONSISTENT_TEST",
    "APPROVED_UNSTABLE_PHYSICAL_INFRA",
    "APPROVED_CUSTOMER_PREREQUISITE_FAIL",
    "APPROVED_FAULTY_HARDWARE",
    "REJECTED",
  ];

  let selectedDecisions = $state<EnvironmentReviewDecision[]>([]);
  let reviewComment = $state("");

  $effect(() => {
    selectedDecisions = [...initialDecisions];
  });

  $effect(() => {
    reviewComment = initialComment;
  });

  function toggleDecision(decision: EnvironmentReviewDecision) {
    if (selectedDecisions.includes(decision)) {
      selectedDecisions = selectedDecisions.filter((d) => d !== decision);
    } else {
      selectedDecisions = [...selectedDecisions, decision];
    }
  }

  function handleSubmit() {
    onsubmit(selectedDecisions, reviewComment);
  }
</script>

<div class="ds review-form">
  <fieldset class="ds review-form__decisions">
    <legend class="ds review-form__legend">Review Decision</legend>
    {#each allDecisions as decision (decision)}
      <label class="ds review-form__checkbox-label">
        <input
          type="checkbox"
          checked={selectedDecisions.includes(decision)}
          onchange={() => toggleDecision(decision)}
          disabled={submitting}
        />
        {formatStatus(decision)}
      </label>
    {/each}
  </fieldset>

  <label class="ds review-form__comment-label">
    Comment
    <textarea
      class="ds review-form__comment"
      bind:value={reviewComment}
      rows="3"
      disabled={submitting}
    ></textarea>
  </label>

  <button
    type="button"
    class="ds review-form__submit"
    onclick={handleSubmit}
    disabled={submitting}
  >
    {submitting ? "Submitting..." : "Submit Review"}
  </button>
</div>

<style>
  .ds.review-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.5rem;
    min-width: 260px;
  }

  .ds.review-form__decisions {
    border: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .ds.review-form__legend {
    font-weight: 600;
    margin-bottom: 0.375rem;
    font-size: 0.875rem;
  }

  .ds.review-form__checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .ds.review-form__comment-label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .ds.review-form__comment {
    padding: 0.375rem 0.5rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    font: inherit;
    resize: vertical;
  }

  .ds.review-form__submit {
    align-self: flex-end;
    padding: 0.375rem 1rem;
    border: none;
    border-radius: 0.25rem;
    background-color: var(--color-positive, #0e8420);
    color: white;
    font: inherit;
    cursor: pointer;
  }

  .ds.review-form__submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
