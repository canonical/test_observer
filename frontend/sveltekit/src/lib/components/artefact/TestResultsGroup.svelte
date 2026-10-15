<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Spinner } from "@canonical/svelte-ds-app-launchpad";
  import { page } from "$app/state";
  import Expandable from "./Expandable.svelte";
  import ExecutionStatusChip from "./ExecutionStatusChip.svelte";
  import TestResultExpandable from "./TestResultExpandable.svelte";
  import { shouldFetchExpandedData } from "$lib/utils/artefact-filters";
  import type { TestResultStatus } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";

  interface Props {
    executionId: number;
    status: TestResultStatus;
    store: ArtefactPageStore;
    parentExpanded: boolean;
  }

  let { executionId, status, store, parentExpanded }: Props = $props();

  const allResults = $derived(store.getTestResults(executionId));
  const results = $derived.by(() => {
    if (!allResults || allResults === "loading") return [];
    return allResults.filter((r) => r.status === status);
  });

  let open = $state(false);
  let requestedExecutionId = $state<number | null>(null);

  const targetResultId = $derived.by(() => {
    const queryValue = page.url.searchParams.get("testResultId");
    if (!queryValue || !/^\d+$/.test(queryValue)) return null;

    const parsedId = Number(queryValue);
    return Number.isSafeInteger(parsedId) && parsedId > 0 ? parsedId : null;
  });

  const targetExecutionId = $derived.by(() => {
    const queryValue = page.url.searchParams.get("testExecutionId");
    if (!queryValue || !/^\d+$/.test(queryValue)) return null;

    const parsedId = Number(queryValue);
    return Number.isSafeInteger(parsedId) && parsedId > 0 ? parsedId : null;
  });

  const isDeepLinkTarget = $derived(
    targetResultId !== null && targetExecutionId === executionId,
  );

  function fetchResults() {
    requestedExecutionId = executionId;
    void store.fetchTestResults(executionId);
  }

  $effect(() => {
    if (
      shouldFetchExpandedData(
        parentExpanded,
        open || isDeepLinkTarget,
        allResults === undefined,
      ) &&
      requestedExecutionId !== executionId
    ) {
      fetchResults();
    }
  });

  $effect(() => {
    if (parentExpanded && targetExecutionId === executionId) {
      open = true;
    }
  });

  $effect(() => {
    if (
      allResults !== undefined &&
      allResults !== "loading" &&
      targetResultId !== null &&
      parentExpanded &&
      targetExecutionId === executionId &&
      results.some((result) => result.id === targetResultId)
    ) {
      open = true;
    }
  });
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="group-title">
      <ExecutionStatusChip {status} />
      {#if allResults !== undefined && allResults !== "loading"}
        <span class="count"
          >{results.length} result{results.length !== 1 ? "s" : ""}</span
        >
      {/if}
    </span>
  {/snippet}

  {#if open}
    {#if allResults === "loading"}
      <div class="loading-row" role="status">
        <Spinner />
        <span>Loading results…</span>
      </div>
    {:else if allResults === undefined && requestedExecutionId === executionId}
      <div class="empty-row" role="alert">
        <span>Could not load test results.</span>
        <button type="button" onclick={fetchResults}>Retry</button>
      </div>
    {:else if allResults === undefined}
      <div class="empty-row">Open this group to load test results.</div>
    {:else if results.length === 0}
      <div class="empty-row">No results for this status.</div>
    {:else}
      <div class="results-list">
        {#each results as result (result.id)}
          <TestResultExpandable {result} {store} />
        {/each}
      </div>
    {/if}
  {/if}
</Expandable>

<style>
  .loading-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
    padding: 4px 0;
  }

  .empty-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
  }

  .empty-row button {
    font: inherit;
  }

  .group-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .count {
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
  }

  .results-list {
    display: flex;
    flex-direction: column;
  }
</style>
