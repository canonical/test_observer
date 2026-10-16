<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Chip, Checkbox } from "@canonical/svelte-ds-app-launchpad";
  import Expandable from "./Expandable.svelte";
  import ExecutionStatusChip from "./ExecutionStatusChip.svelte";
  import EnvironmentReviewButton from "./EnvironmentReviewButton.svelte";
  import EnvironmentIssuesExpandable from "./EnvironmentIssuesExpandable.svelte";
  import TestPlanExpandable from "./TestPlanExpandable.svelte";
  import ReviewersAvatars from "$lib/components/dashboard/ReviewersAvatars.svelte";
  import { page } from "$app/state";
  import type { ArtefactEnvironment } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import { parsePositiveSafeInteger } from "$lib/utils/artefact-filters";

  interface Props {
    env: ArtefactEnvironment;
    store: ArtefactPageStore;
    artefactId: number;
  }

  let { env, store, artefactId }: Props = $props();

  const selected = $derived(
    env.review !== null && store.isSelected(env.review.id),
  );

  let open = $state(false);

  // Auto-open when navigating directly to an execution inside this environment
  const targetExecutionId = $derived(
    parsePositiveSafeInteger(
      page.url.searchParams.get("testExecutionId") ?? "",
    ),
  );
  $effect(() => {
    if (
      targetExecutionId !== null &&
      env.runsDescending.some((r) => r.id === targetExecutionId)
    ) {
      open = true;
    }
  });

  const latestRun = $derived(env.runsDescending[0]);

  const planGroups = $derived.by(() => {
    const groups: [string, typeof env.runsDescending][] = [];
    for (const run of env.runsDescending) {
      const plan = run.test_plan || "(unnamed)";
      const group = groups.find(([name]) => name === plan)?.[1];
      if (group) group.push(run);
      else groups.push([plan, [run]]);
    }
    return groups;
  });
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="env-title">
      <!-- stop checkbox click from toggling the expandable -->
      {#if env.review}
        <span
          class="env-checkbox"
          role="none"
          onclick={(e) => e.stopPropagation()}
        >
          <Checkbox
            checked={selected}
            onchange={(e) => {
              (e as Event).stopPropagation();
              if (env.review) store.toggleSelection(env.review.id);
            }}
          />
        </span>
      {/if}
      {#if latestRun}
        <ExecutionStatusChip status={latestRun.status} />
      {/if}
      <Chip value={env.architecture} readonly density="dense" />
      <span class="env-name">{env.name}</span>
      {#if env.review}
        <ReviewersAvatars
          reviewers={env.review.reviewers}
          allEnvironmentReviewsCount={1}
          completedEnvironmentReviewsCount={env.review.review_decision.length > 0
            ? 1
            : 0}
        />
      {/if}
      <span class="spacer"></span>
      <!-- stop clicks on the review button from toggling the expandable -->
      {#if env.review}
        <span role="none" onclick={(e) => e.stopPropagation()}>
          <EnvironmentReviewButton review={env.review} {store} {artefactId} />
        </span>
      {/if}
    </span>
  {/snippet}

  <div class="env-content">
    <EnvironmentIssuesExpandable environmentName={env.name} {store} />
    {#each planGroups as [planName, runs] (planName)}
      <TestPlanExpandable
        {planName}
        {runs}
        {store}
        isOnlyPlan={planGroups.length === 1}
        parentExpanded={open}
      />
    {/each}
  </div>
</Expandable>

<style>
  .env-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .env-checkbox {
    flex-shrink: 0;
  }

  .env-name {
    font-size: 0.875rem;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .spacer {
    flex: 1;
  }

  .env-content {
    display: flex;
    flex-direction: column;
  }
</style>
