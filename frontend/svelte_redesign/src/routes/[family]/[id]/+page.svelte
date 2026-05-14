<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { ArtefactHeader, BuildSection, BulkReviewDialog } from "$lib/components/artefact-detail/index.js";

  let { data } = $props();

  let selectedEnvironments = $state(new Set<number>());
  let bulkReviewOpen = $state(false);

  function handleEnvironmentSelect(environmentId: number, selected: boolean) {
    const next = new Set(selectedEnvironments);
    if (selected) {
      next.add(environmentId);
    } else {
      next.delete(environmentId);
    }
    selectedEnvironments = next;
  }

  function handleSelectAll() {
    const allIds = new Set<number>();
    for (const build of data.builds) {
      for (const exec of build.testExecutions) {
        allIds.add(exec.environment.id);
      }
    }
    selectedEnvironments = allIds;
  }

  function handleDeselectAll() {
    selectedEnvironments = new Set();
  }
</script>

<svelte:head>
  <title>{data.artefact.name} — Test Observer</title>
</svelte:head>

<ArtefactHeader
  artefact={data.artefact}
  family={data.family}
  versions={data.versions}
/>

<div class="ds artefact-detail__main">
  <div class="ds artefact-detail__toolbar">
    <h2>Environments</h2>
    <div class="ds artefact-detail__bulk-controls">
      <button type="button" onclick={handleSelectAll}>Select All</button>
      <button type="button" onclick={handleDeselectAll}>Deselect All</button>
      {#if selectedEnvironments.size > 0}
        <button type="button" onclick={() => (bulkReviewOpen = true)}>
          Bulk Review ({selectedEnvironments.size})
        </button>
      {/if}
    </div>
  </div>

  {#each data.builds as build (build.id)}
    <BuildSection
      {build}
      reviews={data.reviews}
      artefactId={data.artefact.id}
      activeTestExecutionId={data.activeTestExecutionId}
      {selectedEnvironments}
      onEnvironmentSelect={handleEnvironmentSelect}
    />
  {/each}

  {#if data.builds.length === 0}
    <p class="ds artefact-detail__empty">No builds found for this artefact.</p>
  {/if}
</div>

<BulkReviewDialog
  artefactId={data.artefact.id}
  reviews={data.reviews}
  selectedEnvironmentIds={selectedEnvironments}
  open={bulkReviewOpen}
  onclose={() => { bulkReviewOpen = false; }}
/>

<style>
  .ds.artefact-detail__main {
    margin-top: 1rem;
  }

  .ds.artefact-detail__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .ds.artefact-detail__toolbar h2 {
    margin: 0;
    font-size: 1.25rem;
  }

  .ds.artefact-detail__bulk-controls {
    display: flex;
    gap: 0.5rem;
  }

  .ds.artefact-detail__bulk-controls button {
    padding: 0.375rem 0.75rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background: var(--color-background, #fff);
    font: inherit;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .ds.artefact-detail__empty {
    color: var(--color-text-muted, #666);
    font-style: italic;
  }
</style>
