<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Chip, Checkbox, Textarea } from "@canonical/svelte-ds-app-launchpad";
  import type { ArtefactBuildEnvironmentReviewDecision } from "$lib/types/openapi";
  import type { EnvironmentReview } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import { userStore } from "$lib/stores/user.svelte";

  interface Props {
    review: EnvironmentReview;
    store: ArtefactPageStore;
    artefactId: number;
  }

  let { review, store, artefactId }: Props = $props();

  const DECISIONS: {
    key: ArtefactBuildEnvironmentReviewDecision;
    label: string;
  }[] = [
    { key: "APPROVED_ALL_TESTS_PASS", label: "Approved — All Tests Pass" },
    {
      key: "APPROVED_INCONSISTENT_TEST",
      label: "Approved — Inconsistent Test",
    },
    {
      key: "APPROVED_CUSTOMER_PREREQUISITE_FAIL",
      label: "Approved — Customer Prerequisite Fail",
    },
    { key: "REJECTED", label: "Rejected" },
  ];
  const visibleDecisions = $derived.by(() => {
    const existingDeprecated = review.review_decision.filter(
      (decision) => !DECISIONS.some((option) => option.key === decision),
    );
    return [
      ...DECISIONS,
      ...existingDeprecated.map((key) => ({
        key,
        label:
          key === "APPROVED_UNSTABLE_PHYSICAL_INFRA"
            ? "Approved — Unstable Physical Infra (deprecated)"
            : key === "APPROVED_FAULTY_HARDWARE"
              ? "Approved — Faulty Hardware (deprecated)"
              : `${key} (deprecated)`,
      })),
    ];
  });

  let open = $state(false);
  let selected = $state<ArtefactBuildEnvironmentReviewDecision[]>([]);
  let comment = $state("");
  let submitting = $state(false);
  let wrapperEl: HTMLDivElement | undefined = $state();
  const canChangeReview = $derived(
    userStore.isLoggedIn &&
      userStore.hasPermission("change_environment_review"),
  );

  $effect(() => {
    if (!canChangeReview) open = false;
  });

  $effect(() => {
    selected = [...review.review_decision];
    comment = review.review_comment;
  });

  const chipLabel = $derived.by(() => {
    if (review.review_decision.length === 0) return "Undecided";
    if (review.review_decision.includes("REJECTED")) return "Rejected";
    return "Approved";
  });

  const chipSeverity = $derived.by((): "positive" | "negative" | undefined => {
    if (review.review_decision.length === 0) return undefined;
    if (review.review_decision.includes("REJECTED")) return "negative";
    return "positive";
  });

  function toggle(key: ArtefactBuildEnvironmentReviewDecision) {
    if (key === "REJECTED") {
      selected = selected.includes("REJECTED") ? [] : ["REJECTED"];
    } else {
      selected = selected.includes(key)
        ? selected.filter((d) => d !== key && d !== "REJECTED")
        : [...selected.filter((d) => d !== "REJECTED"), key];
    }
  }

  async function submit(e: MouseEvent) {
    e.stopPropagation();
    if (!canChangeReview || submitting) return;
    submitting = true;
    try {
      await store.submitReview(artefactId, review.id, {
        review_decision: selected,
        review_comment: comment,
      });
      open = false;
    } catch {
      // The API client reports request failures through the global error UI.
    } finally {
      submitting = false;
    }
  }

  function handleClickOutside(e: MouseEvent) {
    if (wrapperEl && !wrapperEl.contains(e.target as Node)) open = false;
  }

  $effect(() => {
    if (open) {
      document.addEventListener("click", handleClickOutside, true);
      return () =>
        document.removeEventListener("click", handleClickOutside, true);
    }
  });
</script>

<div class="wrapper" bind:this={wrapperEl}>
  {#if canChangeReview}
    <button
      class="trigger"
      onclick={(e) => {
        e.stopPropagation();
        if (canChangeReview) open = !open;
      }}
      aria-haspopup="dialog"
      aria-expanded={open}
    >
      <Chip
        value={chipLabel}
        severity={chipSeverity}
        readonly
        density="dense"
      />
    </button>
  {:else}
    <Chip value={chipLabel} severity={chipSeverity} readonly density="dense" />
  {/if}

  {#if open && canChangeReview}
    <div
      class="dropdown"
      role="dialog"
      aria-label="Submit review"
      tabindex="-1"
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.stopPropagation()}
    >
      <p class="dropdown-title">Review decision</p>
      {#each visibleDecisions as d (d.key)}
        <label class="decision-option">
          <Checkbox
            checked={selected.includes(d.key)}
            onchange={() => toggle(d.key)}
          />
          <span>{d.label}</span>
        </label>
      {/each}

      <div class="comment-area">
        <Textarea bind:value={comment} placeholder="Add a comment (optional)" />
      </div>

      <button class="submit-btn" onclick={submit} disabled={submitting}>
        {submitting ? "Saving…" : "Submit review"}
      </button>
    </div>
  {/if}
</div>

<style>
  .wrapper {
    position: relative;
  }

  .trigger {
    all: unset;
    cursor: pointer;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 4px);
    right: 0;
    z-index: 100;
    min-width: 280px;
    padding: 12px;
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .dropdown-title {
    margin: 0 0 4px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .decision-option {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    cursor: pointer;
    color: var(--lp-color-text-default);
  }

  .comment-area {
    margin-top: 4px;
  }

  .submit-btn {
    align-self: flex-end;
    padding: 6px 14px;
    border: 1px solid var(--lp-color-border-default);
    border-radius: 4px;
    background: var(--lp-color-brand-default);
    color: #fff;
    font-size: 0.875rem;
    font-family: inherit;
    cursor: pointer;
  }

  .submit-btn:disabled {
    opacity: 0.6;
    cursor: default;
  }
</style>
