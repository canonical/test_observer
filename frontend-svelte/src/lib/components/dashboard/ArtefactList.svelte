<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Table } from "@canonical/svelte-ds-app-launchpad";
  import { StatusBadge } from "$lib/components/common/index.js";
  import type { Artefact, ArtefactStatus } from "$lib/types/artefact.js";
  import { artefactPath } from "$lib/utils/url.js";
  import { formatDate, formatStatus } from "$lib/utils/formatting.js";
  import StageGroup from "./StageGroup.svelte";
  import DashboardFilters from "./DashboardFilters.svelte";

  interface Props {
    artefacts: Artefact[];
    family: string;
  }

  const { artefacts, family }: Props = $props();

  let viewMode: "board" | "table" = $state("board");
  let searchQuery = $state("");
  let statusFilters: ArtefactStatus[] = $state([]);

  const filteredArtefacts = $derived(
    artefacts.filter((a) => {
      if (searchQuery && !a.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (statusFilters.length > 0 && !statusFilters.includes(a.status)) {
        return false;
      }
      return true;
    }),
  );

  const stages = $derived([...new Set(filteredArtefacts.map((a) => a.stage))]);

  function artefactsByStage(stage: string): Artefact[] {
    return filteredArtefacts.filter((a) => a.stage === stage);
  }
</script>

<div class="ds artefact-list">
  <div class="ds artefact-list__toolbar">
    <DashboardFilters
      {searchQuery}
      onsearchchange={(v) => (searchQuery = v)}
      {statusFilters}
      onstatuschange={(s) => (statusFilters = s)}
    />

    <div class="ds artefact-list__actions">
      <span class="ds artefact-list__count" aria-live="polite">
        {filteredArtefacts.length} of {artefacts.length} artefacts
      </span>
      <div class="ds artefact-list__view-toggle" role="radiogroup" aria-label="View mode">
        <button
          class="ds artefact-list__view-btn"
          class:active={viewMode === "board"}
          role="radio"
          aria-checked={viewMode === "board"}
          onclick={() => (viewMode = "board")}
        >
          Board
        </button>
        <button
          class="ds artefact-list__view-btn"
          class:active={viewMode === "table"}
          role="radio"
          aria-checked={viewMode === "table"}
          onclick={() => (viewMode = "table")}
        >
          Table
        </button>
      </div>
    </div>
  </div>

  {#if filteredArtefacts.length === 0}
    <div class="ds artefact-list__empty">
      <p>No artefacts found</p>
      {#if searchQuery || statusFilters.length > 0}
        <p>Try adjusting your filters.</p>
      {/if}
    </div>
  {:else if viewMode === "board"}
    <div class="ds dashboard-board">
      {#each stages as stage (stage)}
        <StageGroup {stage} artefacts={artefactsByStage(stage)} {family} />
      {/each}
    </div>
  {:else}
    <div class="ds dashboard-table">
      <Table>
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Version</th>
            <th scope="col">Stage</th>
            <th scope="col">Status</th>
            <th scope="col">Track</th>
            <th scope="col">Series</th>
            <th scope="col">Reviews</th>
            <th scope="col">Due Date</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredArtefacts as artefact (artefact.id)}
            <tr>
              <td>
                <a href={artefactPath(family, artefact.id)}>{artefact.name}</a>
              </td>
              <td>{artefact.version}</td>
              <td>{artefact.stage}</td>
              <td><StatusBadge status={artefact.status} /></td>
              <td>{artefact.track}</td>
              <td>{artefact.series}</td>
              <td>{artefact.completedEnvironmentReviewsCount}/{artefact.allEnvironmentReviewsCount}</td>
              <td>{artefact.dueDate ? formatDate(artefact.dueDate) : "—"}</td>
            </tr>
          {/each}
        </tbody>
      </Table>
    </div>
  {/if}
</div>

<style>
  .ds.artefact-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    height: 100%;
  }

  .ds.artefact-list__toolbar {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .ds.artefact-list__actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .ds.artefact-list__count {
    font-size: 0.8125rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-list__view-toggle {
    display: inline-flex;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    overflow: hidden;
  }

  .ds.artefact-list__view-btn {
    padding: 0.25rem 0.75rem;
    font-size: 0.8125rem;
    border: none;
    background: var(--color-background, #fff);
    cursor: pointer;
    color: var(--color-text, #333);
  }

  .ds.artefact-list__view-btn:not(:last-child) {
    border-right: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.artefact-list__view-btn.active {
    background-color: var(--color-background-alt, #f0f0f0);
    font-weight: 600;
  }

  .ds.dashboard-board {
    display: flex;
    gap: 1rem;
    overflow-x: auto;
    flex: 1;
    min-height: 0;
  }

  .ds.dashboard-table {
    width: 100%;
    overflow-x: auto;
  }

  .ds.dashboard-table a {
    color: var(--color-link, #06c);
    text-decoration: none;
  }

  .ds.dashboard-table a:hover {
    text-decoration: underline;
  }

  .ds.artefact-list__empty {
    text-align: center;
    padding: 2rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-list__empty p {
    margin: 0.25rem 0;
  }
</style>
