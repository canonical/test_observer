<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Chip, Link } from "@canonical/svelte-ds-app-launchpad";
  import { TestStatusChip } from "$lib/components/common/index.js";
  import type { TestExecution, TestEvent } from "$lib/types/test-execution.js";
  import type { TestResult } from "$lib/types/test-result.js";
  import { formatDate } from "$lib/utils/formatting.js";
  import { getTestExecutionResults, getTestExecutionEvents } from "$lib/api/test-executions.js";
  import { createReruns } from "$lib/api/test-executions.js";
  import TestResultsList from "./TestResultsList.svelte";
  import EventTimeline from "./EventTimeline.svelte";

  interface Props {
    execution: TestExecution;
    initialOpen?: boolean;
  }

  const { execution, initialOpen = false }: Props = $props();

  let expanded = $state(false);
  let results = $state<TestResult[] | null>(null);
  let events = $state<TestEvent[] | null>(null);
  let loadingResults = $state(false);
  let rerunRequested = $state(false);
  let rerunSubmitting = $state(false);

  $effect(() => {
    expanded = initialOpen;
  });

  $effect(() => {
    rerunRequested = execution.isRerunRequested;
  });

  async function toggle() {
    expanded = !expanded;
    if (expanded && results === null && !loadingResults) {
      loadingResults = true;
      try {
        const [r, e] = await Promise.all([
          getTestExecutionResults(execution.id),
          getTestExecutionEvents(execution.id),
        ]);
        results = r;
        events = e;
      } catch {
        results = [];
        events = [];
      } finally {
        loadingResults = false;
      }
    }
  }

  async function requestRerun() {
    if (rerunRequested || rerunSubmitting) return;
    rerunSubmitting = true;
    try {
      await createReruns([{ testExecutionId: execution.id, ciLink: execution.ciLink ?? "" }]);
      rerunRequested = true;
    } finally {
      rerunSubmitting = false;
    }
  }
</script>

<div class="ds test-execution-row">
  <button
    type="button"
    class="ds test-execution-row__header"
    onclick={toggle}
    aria-expanded={expanded}
  >
    <span class="ds test-execution-row__chevron" class:open={expanded}>&#9656;</span>
    <TestStatusChip status={execution.status} />
    <span class="ds test-execution-row__plan">{execution.testPlan}</span>
    <span class="ds test-execution-row__date">{formatDate(execution.createdAt)}</span>
    {#if execution.ciLink}
      <Link href={execution.ciLink}>CI</Link>
    {/if}
    {#if execution.c3Link}
      <Link href={execution.c3Link}>C3</Link>
    {/if}
    {#each execution.relevantLinks as link (link.id)}
      <Link href={link.url}>{link.label}</Link>
    {/each}
  </button>

  <div class="ds test-execution-row__actions">
    {#if rerunRequested}
      <Chip value="Rerun Requested" severity="caution" readonly />
    {:else}
      <button
        type="button"
        class="ds test-execution-row__rerun-btn"
        onclick={requestRerun}
        disabled={rerunSubmitting}
      >
        {rerunSubmitting ? "Requesting..." : "Request Rerun"}
      </button>
    {/if}
  </div>

  {#if expanded}
    <div class="ds test-execution-row__body">
      {#if loadingResults}
        <p>Loading results...</p>
      {:else}
        {#if results && results.length > 0}
          <TestResultsList {results} />
        {:else if results}
          <p class="ds test-execution-row__empty">No test results</p>
        {/if}
        {#if events && events.length > 0}
          <EventTimeline {events} />
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .ds.test-execution-row {
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    margin-bottom: 0.25rem;
  }

  .ds.test-execution-row__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: none;
    border: none;
    cursor: pointer;
    font: inherit;
    text-align: left;
    flex-wrap: wrap;
  }

  .ds.test-execution-row__header:hover {
    background-color: var(--color-background-hover, #f5f5f5);
  }

  .ds.test-execution-row__chevron {
    display: inline-block;
    transition: transform 0.15s ease;
    font-size: 0.75rem;
  }

  .ds.test-execution-row__chevron.open {
    transform: rotate(90deg);
  }

  .ds.test-execution-row__plan {
    font-weight: 500;
  }

  .ds.test-execution-row__date {
    color: var(--color-text-muted, #666);
    font-size: 0.875rem;
  }

  .ds.test-execution-row__actions {
    display: flex;
    gap: 0.5rem;
    padding: 0 0.75rem 0.5rem;
  }

  .ds.test-execution-row__rerun-btn {
    padding: 0.25rem 0.75rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background: var(--color-background, #fff);
    font: inherit;
    font-size: 0.8125rem;
    cursor: pointer;
  }

  .ds.test-execution-row__rerun-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .ds.test-execution-row__body {
    padding: 0.75rem;
    border-top: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.test-execution-row__empty {
    color: var(--color-text-muted, #666);
    font-size: 0.875rem;
  }
</style>
