<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Chip, SearchBox } from "@canonical/svelte-ds-app-launchpad";
  import type { ArtefactStatus } from "$lib/types/artefact.js";
  import { formatStatus } from "$lib/utils/formatting.js";

  interface Props {
    searchQuery: string;
    onsearchchange: (value: string) => void;
    statusFilters: ArtefactStatus[];
    onstatuschange: (statuses: ArtefactStatus[]) => void;
  }

  const { searchQuery, onsearchchange, statusFilters, onstatuschange }: Props = $props();

  const allStatuses: ArtefactStatus[] = ["APPROVED", "MARKED_AS_FAILED", "UNDECIDED"];

  function toggleStatus(status: ArtefactStatus): void {
    if (statusFilters.includes(status)) {
      onstatuschange(statusFilters.filter((s) => s !== status));
    } else {
      onstatuschange([...statusFilters, status]);
    }
  }

  function removeStatus(status: ArtefactStatus): void {
    onstatuschange(statusFilters.filter((s) => s !== status));
  }

  function clearAll(): void {
    onsearchchange("");
    onstatuschange([]);
  }

  const hasActiveFilters = $derived(searchQuery.length > 0 || statusFilters.length > 0);

  function handleSearchInput(e: Event): void {
    const target = e.target as HTMLInputElement;
    onsearchchange(target.value);
  }
</script>

<div class="ds dashboard-filters">
  <div class="ds dashboard-filters__controls">
    <div class="ds dashboard-filters__search">
      <SearchBox
        aria-label="Filter artefacts by name"
        placeholder="Search artefacts…"
        value={searchQuery}
        oninput={handleSearchInput}
      />
    </div>

    <div class="ds dashboard-filters__statuses" role="group" aria-label="Filter by status">
      {#each allStatuses as status (status)}
        {@const active = statusFilters.includes(status)}
        <Chip
          value={formatStatus(status)}
          severity={active
            ? status === "APPROVED"
              ? "positive"
              : status === "MARKED_AS_FAILED"
                ? "negative"
                : "neutral"
            : undefined}
          onclick={() => toggleStatus(status)}
        />
      {/each}
    </div>
  </div>

  {#if hasActiveFilters}
    <div class="ds dashboard-filters__active" aria-live="polite">
      {#if searchQuery}
        <Chip
          lead="Name"
          value={searchQuery}
          ondismiss={() => onsearchchange("")}
        />
      {/if}
      {#each statusFilters as status (status)}
        <Chip
          lead="Status"
          value={formatStatus(status)}
          ondismiss={() => removeStatus(status)}
        />
      {/each}
      <button class="ds dashboard-filters__clear" onclick={clearAll}>
        Clear all
      </button>
    </div>
  {/if}
</div>

<style>
  .ds.dashboard-filters {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ds.dashboard-filters__controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .ds.dashboard-filters__search {
    flex: 1;
    min-width: 200px;
    max-width: 360px;
  }

  .ds.dashboard-filters__statuses {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
  }

  .ds.dashboard-filters__active {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex-wrap: wrap;
  }

  .ds.dashboard-filters__clear {
    font-size: 0.8125rem;
    color: var(--color-link, #06c);
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
  }

  .ds.dashboard-filters__clear:hover {
    color: var(--color-text, #333);
  }
</style>
