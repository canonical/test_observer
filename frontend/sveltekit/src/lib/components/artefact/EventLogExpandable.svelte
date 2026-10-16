<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Spinner } from "@canonical/svelte-ds-app-launchpad";
  import Expandable from "./Expandable.svelte";
  import { shouldFetchExpandedData } from "$lib/utils/artefact-filters";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";

  interface Props {
    executionId: number;
    store: ArtefactPageStore;
    isCompleted: boolean;
    parentExpanded: boolean;
  }

  let { executionId, store, isCompleted, parentExpanded }: Props = $props();

  // Auto-open event log for in-progress runs so users can see activity
  let open = $state(false);

  $effect(() => {
    if (!isCompleted && parentExpanded) open = true;
  });

  const events = $derived(store.getTestEvents(executionId));

  $effect(() => {
    if (shouldFetchExpandedData(parentExpanded, open, events === undefined))
      store.fetchTestEvents(executionId);
  });
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="section-title">Event Log</span>
  {/snippet}

  {#if events === "loading" || events === undefined}
    <div class="loading-row">
      <Spinner />
      <span>Loading events…</span>
    </div>
  {:else if events === "error"}
    <div class="empty" role="alert">
      <span>Could not load events.</span>
      <button type="button" onclick={() => store.fetchTestEvents(executionId)}
        >Retry</button
      >
    </div>
  {:else if events.length === 0}
    <p class="empty">No events recorded.</p>
  {:else}
    <table class="event-table">
      <thead>
        <tr>
          <th>Event Name</th>
          <th>Timestamp</th>
          <th>Detail</th>
        </tr>
      </thead>
      <tbody>
        {#each events as evt, i (i)}
          <tr>
            <td class="event-name">{evt.event_name}</td>
            <td class="timestamp">{new Date(evt.timestamp).toLocaleString()}</td
            >
            <td class="detail">{evt.detail}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</Expandable>

<style>
  .section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--lp-color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .loading-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
  }

  .empty {
    font-size: 0.8rem;
    color: var(--lp-color-text-muted);
    margin: 0;
  }

  .event-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
  }

  .event-table th {
    text-align: left;
    font-weight: 600;
    color: var(--lp-color-text-muted);
    padding: 4px 8px;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
  }

  .event-table td {
    padding: 4px 8px;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
    color: var(--lp-color-text-default);
    vertical-align: top;
  }

  .event-name {
    white-space: nowrap;
    font-weight: 500;
  }

  .timestamp {
    white-space: nowrap;
    color: var(--lp-color-text-muted);
  }

  .detail {
    word-break: break-word;
  }
</style>
