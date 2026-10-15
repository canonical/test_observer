<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Link } from "@canonical/svelte-ds-app-launchpad";
  import { page } from "$app/state";
  import Expandable from "./Expandable.svelte";
  import ExecutionStatusChip from "./ExecutionStatusChip.svelte";
  import EventLogExpandable from "./EventLogExpandable.svelte";
  import ExecutionMetadataExpandable from "./ExecutionMetadataExpandable.svelte";
  import TestResultsGroup from "./TestResultsGroup.svelte";
  import { shouldFetchExpandedData } from "$lib/utils/artefact-filters";
  import type { TestExecution } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import { parsePositiveSafeInteger } from "$lib/utils/artefact-filters";

  interface Props {
    run: TestExecution & { artefact_build_id: number };
    runNumber: number;
    isNewest: boolean;
    store: ArtefactPageStore;
    parentExpanded: boolean;
  }

  let { run, runNumber, isNewest, store, parentExpanded }: Props = $props();

  const targetExecutionId = $derived(
    parsePositiveSafeInteger(
      page.url.searchParams.get("testExecutionId") ?? "",
    ),
  );

  let open = $state(false);

  $effect(() => {
    if (
      (parentExpanded && isNewest) ||
      (parentExpanded && targetExecutionId === run.id)
    ) {
      open = true;
    }
  });

  const isManualTesting = $derived(run.test_plan === "Manual Testing");
  const isCompleted = $derived(
    run.status === "PASSED" || run.status === "FAILED",
  );
  const showResults = $derived(isCompleted || isManualTesting);

  $effect(() => {
    if (shouldFetchExpandedData(parentExpanded, open, showResults))
      store.fetchTestResults(run.id);
  });
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="exec-title">
      <ExecutionStatusChip status={run.status} />
      <span class="run-label">Run {runNumber}</span>
      <span class="meta">{new Date(run.created_at).toLocaleDateString()}</span>
      <span class="spacer"></span>
      <!-- stop link clicks from toggling the expandable -->
      <span class="links" role="none" onclick={(e) => e.stopPropagation()}>
        {#if run.ci_link}
          <Link href={run.ci_link}>CI</Link>
        {/if}
        {#if run.c3_link}
          <Link href={run.c3_link}>C3</Link>
        {/if}
        {#each run.relevant_links as rl (rl.id)}
          <Link href={rl.url}>{rl.label}</Link>
        {/each}
      </span>
    </span>
  {/snippet}

  <div class="exec-content">
    {#if !isManualTesting}
      <EventLogExpandable
        executionId={run.id}
        {store}
        {isCompleted}
        parentExpanded={open && parentExpanded}
      />
      <ExecutionMetadataExpandable metadata={run.execution_metadata} />
    {/if}

    {#if showResults}
      <TestResultsGroup
        executionId={run.id}
        status="FAILED"
        {store}
        parentExpanded={open && parentExpanded}
      />
      <TestResultsGroup
        executionId={run.id}
        status="PASSED"
        {store}
        parentExpanded={open && parentExpanded}
      />
      <TestResultsGroup
        executionId={run.id}
        status="SKIPPED"
        {store}
        parentExpanded={open && parentExpanded}
      />
    {:else}
      <p class="no-results">No test results available for this run status.</p>
    {/if}
  </div>
</Expandable>

<style>
  .exec-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .run-label {
    font-weight: 500;
    font-size: 0.875rem;
  }

  .meta {
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
  }

  .spacer {
    flex: 1;
  }

  .links {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
  }

  .exec-content {
    display: flex;
    flex-direction: column;
  }

  .no-results {
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
    padding: 8px 0;
    margin: 0;
  }
</style>
