<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Chip } from "@canonical/svelte-ds-app-launchpad";
  import { page } from "$app/state";
  import Expandable from "./Expandable.svelte";
  import TestExecutionExpandable from "./TestExecutionExpandable.svelte";
  import type { TestExecution } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import { parsePositiveSafeInteger } from "$lib/utils/artefact-filters";

  interface Props {
    planName: string;
    runs: (TestExecution & { artefact_build_id: number })[];
    store: ArtefactPageStore;
    isOnlyPlan: boolean;
    parentExpanded: boolean;
  }

  let { planName, runs, store, isOnlyPlan, parentExpanded }: Props = $props();

  let open = $state(false);

  const targetExecutionId = $derived(
    parsePositiveSafeInteger(
      page.url.searchParams.get("testExecutionId") ?? "",
    ),
  );

  $effect(() => {
    if (isOnlyPlan && parentExpanded) {
      open = true;
    } else if (
      parentExpanded &&
      targetExecutionId !== null &&
      runs.some((r) => r.id === targetExecutionId)
    ) {
      open = true;
    }
  });

  const sortedRuns = $derived([...runs].sort((a, b) => b.id - a.id));

  const latestRun = $derived(sortedRuns[0]);

  let rerunning = $state(false);

  async function handleRerun(e: Event) {
    e.stopPropagation();
    if (!store.canChangeRerun || !latestRun) return;
    rerunning = true;
    try {
      await store.rerunExecutions([latestRun.id]);
    } catch {
      // The API client reports request failures through the global error UI.
    } finally {
      rerunning = false;
    }
  }
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="plan-title">
      <Chip value={planName} readonly density="dense" />
      <span class="run-count"
        >({sortedRuns.length} run{sortedRuns.length !== 1 ? "s" : ""})</span
      >
      <span class="spacer"></span>
      {#if store.canChangeRerun}
        <span role="none" onclick={(e) => e.stopPropagation()}>
          <button class="rerun-btn" onclick={handleRerun} disabled={rerunning}>
            {latestRun?.is_rerun_requested
              ? "↺ Rerun Requested"
              : rerunning
                ? "↺ Requesting…"
                : "↺ Rerun"}
          </button>
        </span>
      {/if}
    </span>
  {/snippet}

  <div class="runs-list">
    {#each sortedRuns as run, i (run.id)}
      <TestExecutionExpandable
        {run}
        runNumber={sortedRuns.length - i}
        isNewest={i === 0}
        {store}
        parentExpanded={open && parentExpanded}
      />
    {/each}
  </div>
</Expandable>

<style>
  .plan-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .run-count {
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
  }

  .spacer {
    flex: 1;
  }

  .rerun-btn {
    background: none;
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    cursor: pointer;
    color: var(--lp-color-text-default);
    font-family: inherit;
  }

  .rerun-btn:hover {
    background: var(--lp-color-background-hover);
  }

  .rerun-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .runs-list {
    display: flex;
    flex-direction: column;
  }
</style>
