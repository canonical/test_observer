<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import BulkEnvironmentReviewDialog from "./BulkEnvironmentReviewDialog.svelte";
  import type { ArtefactEnvironment } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import { userStore } from "$lib/stores/user.svelte";

  interface Props {
    environments: ArtefactEnvironment[];
    artefactId: number;
    store: ArtefactPageStore;
  }

  let { environments, artefactId, store }: Props = $props();

  let dialogOpen = $state(false);
  const canChangeReview = $derived(
    userStore.isLoggedIn &&
      userStore.hasPermission("change_environment_review"),
  );

  $effect(() => {
    if (!canChangeReview) dialogOpen = false;
  });

  const selectedEnvironments = $derived(
    environments.filter(
      (env): env is typeof env & { review: NonNullable<typeof env.review> } =>
        env.review !== null && store.isSelected(env.review.id),
    ),
  );
  const selectedCount = $derived(selectedEnvironments.length);
  const totalCount = $derived(environments.length);

  function handleSelectAll() {
    store.selectAll(
      environments.flatMap((env) => (env.review ? [env.review.id] : [])),
    );
  }

  function handleDeselectAll() {
    store.deselectAll();
  }
</script>

<div class="bulk-controls">
  <span class="selection-count">{selectedCount} of {totalCount} selected</span>
  <button class="ctrl-btn" onclick={handleSelectAll}>Select All</button>
  <button class="ctrl-btn" onclick={handleDeselectAll}>Deselect All</button>
  {#if canChangeReview && selectedCount > 0}
    <button
      class="ctrl-btn brand"
      onclick={() => {
        if (canChangeReview) dialogOpen = true;
      }}
    >
      Review {selectedCount} environment{selectedCount !== 1 ? "s" : ""}
    </button>
  {/if}
</div>

{#if dialogOpen && canChangeReview}
  <BulkEnvironmentReviewDialog
    {artefactId}
    environments={selectedEnvironments}
    environmentReviews={selectedEnvironments.map((e) => e.review)}
    {store}
    onclose={() => (dialogOpen = false)}
  />
{/if}

<style>
  .bulk-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    font-size: 0.8rem;
  }

  .selection-count {
    color: var(--lp-color-text-muted);
    white-space: nowrap;
  }

  .ctrl-btn {
    background: none;
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 0.8rem;
    cursor: pointer;
    color: var(--lp-color-text-default);
    font-family: inherit;
  }

  .ctrl-btn:hover {
    background: var(--lp-color-background-hover);
  }

  .ctrl-btn.brand {
    background: var(--lp-color-brand-default);
    color: #fff;
    border-color: transparent;
  }

  .ctrl-btn.brand:hover {
    opacity: 0.9;
  }
</style>
